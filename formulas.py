# formulas.py
import math

# 核心數學公式
def calc_log_gain(invest_amount, base_cost=50.0):
    return math.log2(1 + (invest_amount / base_cost))

def calculate_required_funds(cfg, t_h_fund, t_gdp, curr_h_fund, curr_gdp, r_val, forecast_decay, build_abi):
    eff_decay_h = forecast_decay * r_val * 0.2 * curr_h_fund
    req_boost_h = (t_h_fund - curr_h_fund) + eff_decay_h
    funds_h = (req_boost_h * max(0.1, r_val)) / max(0.01, build_abi) if req_boost_h > 0 else 0

    eff_decay_gdp = forecast_decay * 1000
    req_boost_gdp = (t_gdp - curr_gdp) + eff_decay_gdp
    funds_gdp = (req_boost_gdp * cfg['BUILD_DIFF']) / max(0.01, build_abi) if req_boost_gdp > 0 else 0

    req_funds = max(0, int(funds_h + funds_gdp))
    h_ratio = funds_h / req_funds if req_funds > 0 else 1.0
    return req_funds, h_ratio

def calc_support_shift(cfg, hp, rp, act_h, act_gdp, t_h, t_gdp, curr_gdp, h_prop, r_prop, h_blame, r_blame):
    h_perf = ((act_h - t_h) / max(1, t_h)) * 100.0  
    r_perf = ((act_gdp - curr_gdp) / max(1, curr_gdp)) * 100.0 

    h_prop_pow = calc_log_gain(h_prop) * cfg['H_PROP_BONUS']
    r_prop_pow = calc_log_gain(r_prop)
    h_blame_pow = calc_log_gain(h_blame) * hp.blame_ability
    r_blame_pow = calc_log_gain(r_blame) * rp.blame_ability

    if h_perf >= 0:
        h_raw_shift = h_perf * (1 + h_prop_pow * 0.15)
        h_shift_to_r = 0
    else:
        transfer_ratio = min(1.0, h_blame_pow * 0.05)
        h_raw_shift = h_perf * (1 - transfer_ratio)
        h_shift_to_r = h_perf * transfer_ratio 

    if r_perf >= 0:
        r_raw_shift = r_perf * (1 + r_prop_pow * 0.15)
        r_shift_to_h = 0
    else:
        transfer_ratio = min(1.0, r_blame_pow * 0.05)
        r_raw_shift = r_perf * (1 - transfer_ratio)
        r_shift_to_h = r_perf * transfer_ratio

    net_h = h_raw_shift + r_shift_to_h
    net_r = r_raw_shift + h_shift_to_r

    shift_to_h = net_h - net_r
    if shift_to_h > 0: return shift_to_h * ((100.0 - hp.support) / 100.0)
    else: return shift_to_h * (hp.support / 100.0)

def calculate_preview(cfg, game, req_funds, h_ratio, r_val, fc_decay, hp_build, r_pays, h_pays):
    gdp_bst = (req_funds * hp_build) / cfg['BUILD_DIFF']
    est_gdp = max(0.0, game.gdp + gdp_bst - (fc_decay * 1000))
    gdp_change = est_gdp - game.gdp
    gdp_change_pct = (gdp_change / game.gdp) * 100.0 if game.gdp > 0 else 0.0

    actual_h_funds = req_funds * h_ratio
    h_bst = (actual_h_funds * hp_build) / max(0.1, r_val)
    eff_decay_h = fc_decay * r_val * 0.2 * game.h_fund
    est_h_fund = max(0.0, game.h_fund + h_bst - eff_decay_h)

    future_budget = cfg['BASE_TOTAL_BUDGET'] + (est_gdp * cfg['HEALTH_MULTIPLIER'])
    h_share_ratio = est_h_fund / max(1.0, future_budget) if future_budget > 0 else 0.5
    
    h_ruling_bonus = cfg['RULING_BONUS'] if game.ruling_party == game.h_role_party else 0
    r_ruling_bonus = cfg['RULING_BONUS'] if game.ruling_party == game.r_role_party else 0
    
    h_gross = cfg['DEFAULT_BONUS'] + h_ruling_bonus + (future_budget * h_share_ratio)
    r_gross = cfg['DEFAULT_BONUS'] + r_ruling_bonus + (future_budget * (1 - h_share_ratio))
    
    h_net = h_gross - h_pays
    r_net = r_gross - r_pays
    
    current_share = game.h_fund / max(1.0, game.total_budget)
    net_h_shift = (h_share_ratio - current_share) * 100.0
    
    return gdp_change_pct, h_gross, h_net, r_gross, r_net, net_h_shift, -net_h_shift, est_gdp, est_h_fund

# 資料結構
class Party:
    def __eq__(self, other):
        return self.name == other.name if hasattr(other, 'name') else False

    def __init__(self, name, cfg):
        self.name = name
        self.wealth = cfg['INITIAL_WEALTH']
        self.support = 50.0 
        self.build_ability = 1.0 / cfg['BUILD_DIFF']
        self.investigate_ability = 1.0 / cfg['INVESTIGATE_DIFF']
        self.edu_ability = 1.0 / cfg['EDU_DIFF']
        self.prop_ability = 1.0 / cfg['PROP_DIFF']
        self.predict_ability = 1.0
        self.blame_ability = 1.0 
        
        self.current_forecast = 0.0
        self.last_forecast = 0.0
        self.last_income_diff = 0.0
        self.last_sup_diff = 0.0
        self.current_poll_result = None

class GameEngine:
    def __init__(self, cfg):
        self.year = 1
        self.party_A = Party(cfg['PARTY_A_NAME'], cfg)
        self.party_B = Party(cfg['PARTY_B_NAME'], cfg)
        self.gdp = cfg['CURRENT_GDP']
        self.total_budget = cfg['BASE_TOTAL_BUDGET'] + (self.gdp * cfg['HEALTH_MULTIPLIER'])
        self.h_fund = cfg['H_FUND_DEFAULT']
        
        self.phase = 1 
        self.p1_state = 'drafting' 
        self.ruling_party = self.party_A
        self.r_role_party = self.party_A  
        self.h_role_party = self.party_B  
        self.sanity = 1.0 
        
        self.current_real_decay = 0.0
        self.last_real_decay = 0.0
        self.proposal_count = 0
        self.proposing_party = self.party_A

        # 新增：歷史數據追蹤與單期事件標記
        self.history = []
        self.swap_triggered_this_year = False

    def record_history(self, is_election):
        # 紀錄每年期末的結算數據供畫圖使用
        self.history.append({
            'Year': self.year,
            'GDP': self.gdp,
            'Sanity': self.sanity,
            'A_Support': self.party_A.support,
            'B_Support': self.party_B.support,
            'A_Wealth': self.party_A.wealth,
            'B_Wealth': self.party_B.wealth,
            'A_Build': self.party_A.build_ability, 'A_Inv': self.party_A.investigate_ability,
            'A_Edu': self.party_A.edu_ability, 'A_Prop': self.party_A.prop_ability, 'A_Blame': self.party_A.blame_ability,
            'B_Build': self.party_B.build_ability, 'B_Inv': self.party_B.investigate_ability,
            'B_Edu': self.party_B.edu_ability, 'B_Prop': self.party_B.prop_ability, 'B_Blame': self.party_B.blame_ability,
            'Is_Election': is_election,
            'Is_Swap': self.swap_triggered_this_year
        })
        self.swap_triggered_this_year = False
