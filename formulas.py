# ==========================================
# formulas.py
# 負責核心數學模型、撞牆懲罰與年度詳細戰報記錄
# ==========================================
import math

def calc_log_gain(invest_amount, base_cost=50.0):
    return math.log2(1 + (invest_amount / base_cost))

def calculate_required_funds(cfg, t_h_fund, t_gdp, curr_h_fund, curr_gdp, r_val, forecast_decay, build_abi):
    # 撞牆機制：R 值的影響改為「平方級放大」，嚴格度越高，成本呈現指數型爆發
    strictness_multiplier = r_val ** 2 
    
    eff_decay_h = forecast_decay * strictness_multiplier * 0.2 * curr_h_fund
    req_boost_h = (t_h_fund - curr_h_fund) + eff_decay_h
    funds_h = (req_boost_h * max(0.1, strictness_multiplier)) / max(0.01, build_abi) if req_boost_h > 0 else 0

    eff_decay_gdp = forecast_decay * 1000
    req_boost_gdp = (t_gdp - curr_gdp) + eff_decay_gdp
    funds_gdp = (req_boost_gdp * cfg['BUILD_DIFF']) / max(0.01, build_abi) if req_boost_gdp > 0 else 0

    req_funds = max(0, int(funds_h + funds_gdp))
    h_ratio = funds_h / req_funds if req_funds > 0 else 1.0
    return req_funds, h_ratio

def calc_support_shift(cfg, hp, rp, act_h, act_gdp, t_h, t_gdp, curr_gdp, h_prop, r_prop, h_blame, r_blame):
    # 詳細記錄支持度轉移過程，供 UI 戰報使用
    h_perf = ((act_h - t_h) / max(1, t_h)) * 100.0  
    r_perf = ((act_gdp - curr_gdp) / max(1, curr_gdp)) * 100.0 

    h_prop_pow = calc_log_gain(h_prop) * cfg['H_PROP_BONUS']
    r_prop_pow = calc_log_gain(r_prop)
    h_blame_pow = calc_log_gain(h_blame) * hp.blame_ability
    r_blame_pow = calc_log_gain(r_blame) * rp.blame_ability

    h_raw_shift = 0; h_shift_to_r = 0; r_raw_shift = 0; r_shift_to_h = 0

    if h_perf >= 0:
        h_raw_shift = h_perf * (1 + h_prop_pow * 0.15)
    else:
        transfer_ratio = min(1.0, h_blame_pow * 0.05)
        h_raw_shift = h_perf * (1 - transfer_ratio)
        h_shift_to_r = h_perf * transfer_ratio 

    if r_perf >= 0:
        r_raw_shift = r_perf * (1 + r_prop_pow * 0.15)
    else:
        transfer_ratio = min(1.0, r_blame_pow * 0.05)
        r_raw_shift = r_perf * (1 - transfer_ratio)
        r_shift_to_h = r_perf * transfer_ratio

    net_h = h_raw_shift + r_shift_to_h
    net_r = r_raw_shift + h_shift_to_r
    shift_to_h = net_h - net_r
    
    actual_shift = shift_to_h * ((100.0 - hp.support) / 100.0) if shift_to_h > 0 else shift_to_h * (hp.support / 100.0)
    
    # 回傳詳細戰報物件
    return {
        'actual_shift': actual_shift,
        'h_perf': h_perf, 'r_perf': r_perf,
        'h_blame_saved': h_shift_to_r, # H 成功推給 R 的傷害
        'r_blame_saved': r_shift_to_h  # R 成功推給 H 的傷害
    }

def calculate_preview(cfg, game, req_funds, h_ratio, r_val, fc_decay, hp_build, r_pays, h_pays):
    # 用於提案階段的假想推演
    gdp_bst = (req_funds * hp_build) / cfg['BUILD_DIFF']
    est_gdp = max(0.0, game.gdp + gdp_bst - (fc_decay * 1000))
    gdp_change_pct = ((est_gdp - game.gdp) / game.gdp) * 100.0 if game.gdp > 0 else 0.0

    actual_h_funds = req_funds * h_ratio
    strict_mult = r_val ** 2
    h_bst = (actual_h_funds * hp_build) / max(0.1, strict_mult)
    eff_decay_h = fc_decay * strict_mult * 0.2 * game.h_fund
    est_h_fund = max(0.0, game.h_fund + h_bst - eff_decay_h)

    future_budget = cfg['BASE_TOTAL_BUDGET'] + (est_gdp * cfg['HEALTH_MULTIPLIER'])
    h_share_ratio = est_h_fund / max(1.0, future_budget) if future_budget > 0 else 0.5
    
    h_gross = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.h_role_party.name else 0) + (future_budget * h_share_ratio)
    r_gross = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.r_role_party.name else 0) + (future_budget * (1 - h_share_ratio))
    
    current_share = game.h_fund / max(1.0, game.total_budget)
    net_h_shift = (h_share_ratio - current_share) * 100.0
    
    return gdp_change_pct, h_gross, h_gross - h_pays, r_gross, r_gross - r_pays, net_h_shift, -net_h_shift, est_gdp, est_h_fund

class Party:
    def __eq__(self, other): return self.name == other.name if hasattr(other, 'name') else False
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
        self.current_forecast = 0.0; self.last_forecast = 0.0
        self.last_income_diff = 0.0; self.last_sup_diff = 0.0
        self.current_poll_result = None

class GameEngine:
    def __init__(self, cfg):
        self.year = 1
        self.party_A = Party(cfg['PARTY_A_NAME'], cfg)
        self.party_B = Party(cfg['PARTY_B_NAME'], cfg)
        self.gdp = cfg['CURRENT_GDP']
        self.total_budget = cfg['BASE_TOTAL_BUDGET'] + (self.gdp * cfg['HEALTH_MULTIPLIER'])
        self.h_fund = cfg['H_FUND_DEFAULT']
        self.confiscated_funds = 0.0 
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

        # 軌跡紀錄與戰報儲存
        self.history = []
        self.swap_triggered_this_year = False
        self.last_year_report = None # 紀錄去年詳細數據供 UI 顯示

    def record_history(self, is_election):
        self.history.append({
            'Year': self.year, 'GDP': self.gdp, 'Sanity': self.sanity,
            'A_Support': self.party_A.support, 'B_Support': self.party_B.support,
            'A_Wealth': self.party_A.wealth, 'B_Wealth': self.party_B.wealth,
            'A_Build': self.party_A.build_ability, 'A_Inv': self.party_A.investigate_ability,
            'A_Edu': self.party_A.edu_ability, 'A_Prop': self.party_A.prop_ability, 'A_Blame': self.party_A.blame_ability,
            'B_Build': self.party_B.build_ability, 'B_Inv': self.party_B.investigate_ability,
            'B_Edu': self.party_B.edu_ability, 'B_Prop': self.party_B.prop_ability, 'B_Blame': self.party_B.blame_ability,
            'Is_Election': is_election, 'Is_Swap': self.swap_triggered_this_year
        })
        self.swap_triggered_this_year = False
