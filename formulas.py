# ==========================================
# formulas.py
# 負責核心量化、維護費、ROI 與年度結算
# ==========================================
import math
import random

def calc_log_gain(invest_amount, base_cost=50.0):
    return math.log2(1 + (invest_amount / base_cost)) if invest_amount > 0 else 0.0

def get_ability_preview(current, invest, cfg):
    maint = max(0, (current - 3.0) * cfg['MAINTENANCE_RATE'])
    if invest < maint:
        drop = (maint - invest) * 0.02
        next_val = max(3.0, current - drop)
    else:
        gain = calc_log_gain(invest - maint)
        next_val = min(cfg['MAX_ABILITY'], current + gain)
    next_maint = max(0, (next_val - 3.0) * cfg['MAINTENANCE_RATE'])
    return next_val, maint, next_maint

def calculate_campaign_effect(a_vol, b_vol, base_mag):
    total_vol = a_vol + b_vol
    if total_vol <= 0: return 0.0, 0.0
    return (a_vol / total_vol - 0.5) * base_mag, (b_vol / total_vol - 0.5) * base_mag

def calculate_required_funds(cfg, t_h_fund, t_gdp, curr_h_fund, curr_gdp, r_val, forecast_decay, build_abi):
    strict_mult = r_val ** 2 
    eff_decay_h = forecast_decay * strict_mult * 0.2 * curr_h_fund
    req_boost_h = (t_h_fund - curr_h_fund) + eff_decay_h
    funds_h = (req_boost_h * max(0.1, strict_mult)) / max(0.01, build_abi) if req_boost_h > 0 else 0

    eff_decay_gdp = forecast_decay * 1000
    req_boost_gdp = (t_gdp - curr_gdp) + eff_decay_gdp
    funds_gdp = (req_boost_gdp * cfg['BUILD_DIFF']) / max(0.01, build_abi) if req_boost_gdp > 0 else 0

    req_funds = max(0, int(funds_h + funds_gdp))
    h_ratio = funds_h / req_funds if req_funds > 0 else 1.0
    return req_funds, h_ratio

def calc_support_shift(cfg, hp, rp, act_h, act_gdp, t_h, t_gdp, curr_gdp, h_media, r_media):
    h_perf = ((act_h - t_h) / max(1, t_h)) * 100.0  
    r_perf = ((act_gdp - curr_gdp) / max(1, curr_gdp)) * 100.0 

    h_media_pow = calc_log_gain(h_media) * cfg['H_MEDIA_BONUS'] * hp.media_ability
    r_media_pow = calc_log_gain(r_media) * rp.media_ability

    if h_perf >= 0: h_raw_shift = h_perf * (1 + h_media_pow * 0.15); h_shift_to_r = 0
    else:
        trans = min(1.0, h_media_pow * 0.05)
        h_raw_shift = h_perf * (1 - trans); h_shift_to_r = h_perf * trans 

    if r_perf >= 0: r_raw_shift = r_perf * (1 + r_media_pow * 0.15); r_shift_to_h = 0
    else:
        trans = min(1.0, r_media_pow * 0.05)
        r_raw_shift = r_perf * (1 - trans); r_shift_to_h = r_perf * trans

    shift_to_h = (h_raw_shift + r_shift_to_h) - (r_raw_shift + h_shift_to_r)
    act_h_shift = shift_to_h * ((100.0 - hp.support) / 100.0) if shift_to_h > 0 else shift_to_h * (hp.support / 100.0)
    
    return {'actual_shift': act_h_shift, 'h_perf': h_perf, 'r_perf': r_perf}

def calculate_preview(cfg, game, req_funds, h_ratio, r_val, fc_decay, hp_build, r_pays, h_pays):
    gdp_bst = (req_funds * hp_build) / cfg['BUILD_DIFF']
    est_gdp = max(0.0, game.gdp + gdp_bst - (fc_decay * 1000))
    gdp_change_pct = ((est_gdp - game.gdp) / max(1.0, game.gdp)) * 100.0

    actual_h_funds = req_funds * h_ratio
    h_bst = (actual_h_funds * hp_build) / max(0.1, r_val ** 2)
    est_h_fund = max(0.0, game.h_fund + h_bst - (fc_decay * (r_val**2) * 0.2 * game.h_fund))

    future_budget = cfg['BASE_TOTAL_BUDGET'] + (est_gdp * cfg['HEALTH_MULTIPLIER'])
    h_share_ratio = est_h_fund / max(1.0, future_budget) if future_budget > 0 else 0.5
    
    h_gross = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.h_role_party.name else 0) + (future_budget * h_share_ratio)
    r_gross = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.r_role_party.name else 0) + (future_budget * (1 - h_share_ratio))
    
    h_net = h_gross - h_pays; r_net = r_gross - r_pays
    h_roi = (h_net / max(1.0, float(h_pays))) * 100.0 if h_pays > 0 else float('inf')
    r_roi = (r_net / max(1.0, float(r_pays))) * 100.0 if r_pays > 0 else float('inf')
    
    return gdp_change_pct, h_gross, h_net, r_gross, r_net, 0, 0, est_gdp, est_h_fund, h_roi, r_roi

def execute_year_end(game, cfg, ra, ha, d):
    rp, hp = game.r_role_party, game.h_role_party
    corr_amt = d.get('total_funds', 0) * (ha.get('corr', 0) / 100.0)
    act_build = d.get('total_funds', 0) - corr_amt
    
    caught = False; confiscated = 0.0
    if ha.get('corr', 0) > 0:
        eff_inv = rp.investigate_ability * cfg['R_INV_BONUS']
        catch_prob = min(1.0, (eff_inv / cfg['MAX_ABILITY']) * (corr_amt / max(1.0, hp.wealth)) * 10.0)
        if random.random() < catch_prob:
            caught = True; confiscated = corr_amt; corr_amt = 0 
            
    h_bst = (act_build * d.get('h_ratio', 1.0) * hp.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
    new_h_fund = max(0.0, game.h_fund + h_bst - (game.current_real_decay * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
    gdp_bst = (act_build * hp.build_ability) / cfg['BUILD_DIFF']
    new_gdp = max(0.0, game.gdp + gdp_bst - (game.current_real_decay * 1000))
    
    h_bonus_overflow = max(0.0, new_h_fund - d.get('target_h_fund', 600)) if new_h_fund >= d.get('target_h_fund', 600) else 0.0
    
    budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
    h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
    
    hp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == hp.name else 0) + (budg * h_shr) - d.get('h_pays',0) + corr_amt + h_bonus_overflow - (confiscated * cfg['CORRUPTION_PENALTY'] if caught else 0)
    rp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == rp.name else 0) + (budg * (1 - h_shr)) - d.get('r_pays',0)
    
    shift = calc_support_shift(cfg, hp, rp, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha.get('media', 0), ra.get('media', 0))
    
    a_vol = ra.get('camp', 0) * rp.media_ability * cfg['R_INV_BONUS'] if rp.name == game.party_A.name else ha.get('camp', 0) * hp.media_ability * cfg['H_MEDIA_BONUS']
    b_vol = ra.get('camp', 0) * rp.media_ability * cfg['R_INV_BONUS'] if rp.name == game.party_B.name else ha.get('camp', 0) * hp.media_ability * cfg['H_MEDIA_BONUS']
    a_camp, b_camp = calculate_campaign_effect(a_vol, b_vol, cfg['CAMPAIGN_MAGNITUDE'])
    
    game.party_A.support += a_camp; game.party_B.support += b_camp
    final_h_shift = shift['actual_shift'] - (5.0 if caught else 0.0)
    hp.support = max(0.0, min(100.0, hp.support + final_h_shift))
    rp.support = 100.0 - hp.support
    
    gdp_grw_bonus = ((new_gdp - game.gdp)/max(1.0, game.gdp)) * 100.0 if game.gdp > 0 else 0
    game.emotion = max(0.0, min(100.0, game.emotion + (ha.get('incite', 0) + ra.get('incite', 0)) * 0.1 - gdp_grw_bonus - (game.sanity * 20.0)))
    game.sanity = max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + ((ra.get('edu_up', 0)+ha.get('edu_up', 0)) * 0.005) - ((ra.get('edu_down', 0)+ha.get('edu_down', 0)) * 0.005)))
    
    game.last_year_report = {
        'old_gdp': game.gdp, 'old_san': game.sanity, 'old_emo': game.emotion, 'old_budg': game.total_budget, 'old_h_fund': game.h_fund,
        'target_gdp': d.get('target_gdp'), 'target_h_fund': d.get('target_h_fund'), 'h_party_name': hp.name, 'caught_corruption': caught,
        'h_perf': shift['h_perf'], 'h_inc': hp_inc, 'r_inc': rp_inc,
        'h_sup_shift': final_h_shift + (a_camp if hp.name == game.party_A.name else b_camp),
        'r_sup_shift': -final_h_shift + (a_camp if rp.name == game.party_A.name else b_camp),
        'est_h_inc': d.get('est_h_n', 0), 'est_r_inc': d.get('est_r_n', 0),
        'est_h_sup_shift': d.get('est_h_sup', 0), 'est_r_sup_shift': d.get('est_r_sup', 0),
        'real_decay': game.current_real_decay, 'view_party_forecast': game.proposing_party.current_forecast
    }
    game.h_fund, game.gdp, game.total_budget = new_h_fund, new_gdp, budg + confiscated
    hp.wealth += hp_inc; rp.wealth += rp_inc

def execute_poll(game, view_party, cost):
    view_party.wealth -= cost
    error = max(0.0, 15.0 - (view_party.predict_ability * 0.5) - (cost * 0.4))
    a_poll = max(0.0, min(100.0, game.party_A.support + random.uniform(-error, error)))
    game.party_A.current_poll_result = a_poll
    game.party_B.current_poll_result = 100.0 - a_poll

class Party:
    def __eq__(self, other): return self.name == other.name if hasattr(other, 'name') else False
    def __init__(self, name, cfg):
        self.name = name; self.wealth = cfg['INITIAL_WEALTH']; self.support = 50.0 
        self.build_ability = cfg['ABILITY_DEFAULT']; self.investigate_ability = cfg['ABILITY_DEFAULT']
        self.edu_ability = cfg['ABILITY_DEFAULT']; self.media_ability = cfg['ABILITY_DEFAULT']
        self.predict_ability = cfg['ABILITY_DEFAULT']
        self.current_forecast = 0.0; self.current_poll_result = None

class GameEngine:
    def __init__(self, cfg):
        self.year = 1; self.party_A = Party(cfg['PARTY_A_NAME'], cfg); self.party_B = Party(cfg['PARTY_B_NAME'], cfg)
        self.gdp = cfg['CURRENT_GDP']; self.total_budget = cfg['BASE_TOTAL_BUDGET'] + (self.gdp * cfg['HEALTH_MULTIPLIER'])
        self.h_fund = cfg['H_FUND_DEFAULT']; self.phase = 1; self.p1_step = 'draft_r' 
        self.p1_proposals = {'R': None, 'H': None}; self.p1_selected_plan = None
        self.ruling_party = self.party_A; self.r_role_party = self.party_A; self.h_role_party = self.party_B  
        self.sanity = cfg['SANITY_DEFAULT']; self.emotion = cfg['EMOTION_DEFAULT']
        self.current_real_decay = 0.0; self.proposal_count = 1; self.proposing_party = self.party_A
        self.history = []; self.swap_triggered_this_year = False; self.last_year_report = None
        self.poll_done_this_year = False

    def record_history(self, is_election):
        self.history.append({
            'Year': self.year, 'GDP': self.gdp, 'Sanity': self.sanity, 'Emotion': self.emotion,
            'A_Support': self.party_A.support, 'B_Support': self.party_B.support,
            'A_Wealth': self.party_A.wealth, 'B_Wealth': self.party_B.wealth,
            'Is_Election': is_election, 'Is_Swap': self.swap_triggered_this_year
        })
        self.swap_triggered_this_year = False
