# ==========================================
# formulas.py
# 負責核心量化、維護費、ROI 與 競選量計算
# ==========================================
import math
import random

def calc_log_gain(invest_amount, base_cost=50.0):
    return math.log2(1 + (invest_amount / base_cost)) if invest_amount > 0 else 0.0

def get_ability_preview(current, invest, cfg):
    maint = max(0, (current - 3.0) * cfg['MAINTENANCE_RATE'])
    if invest < maint:
        drop = (maint - invest) * 0.02
        return max(3.0, current - drop), maint
    else:
        gain = calc_log_gain(invest - maint)
        return min(cfg['MAX_ABILITY'], current + gain), maint

def calculate_campaign_effect(a_media_volume, b_media_volume, base_mag):
    """媒體競選邏輯：按操控量比例分配支持度變更"""
    total_vol = a_media_volume + b_media_volume
    if total_vol <= 0: return 0.0, 0.0
    a_share = a_media_volume / total_vol
    b_share = b_media_volume / total_vol
    # 轉換成支持度百分比
    return (a_share - 0.5) * base_mag, (b_share - 0.5) * base_mag

def calculate_required_funds(cfg, t_h_fund, t_gdp, curr_h_fund, curr_gdp, r_val, forecast_decay, build_abi):
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

def calculate_preview(cfg, game, req_funds, h_ratio, r_val, fc_decay, hp_build, r_pays, h_pays):
    gdp_bst = (req_funds * hp_build) / cfg['BUILD_DIFF']
    est_gdp = max(0.0, game.gdp + gdp_bst - (fc_decay * 1000))
    gdp_change_pct = ((est_gdp - game.gdp) / max(1.0, game.gdp)) * 100.0
    actual_h_funds = req_funds * h_ratio
    strict_mult = r_val ** 2
    h_bst = (actual_h_funds * hp_build) / max(0.1, strict_mult)
    eff_decay_h = fc_decay * strict_mult * 0.2 * game.h_fund
    est_h_fund = max(0.0, game.h_fund + h_bst - eff_decay_h)
    future_budget = cfg['BASE_TOTAL_BUDGET'] + (est_gdp * cfg['HEALTH_MULTIPLIER'])
    h_share_ratio = est_h_fund / max(1.0, future_budget) if future_budget > 0 else 0.5
    h_gross = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.h_role_party.name else 0) + (future_budget * h_share_ratio)
    r_gross = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.r_role_party.name else 0) + (future_budget * (1 - h_share_ratio))
    h_net = h_gross - h_pays; r_net = r_gross - r_pays
    h_roi = (h_net / max(1.0, float(h_pays))) * 100.0 if h_pays > 0 else float('inf')
    r_roi = (r_net / max(1.0, float(r_pays))) * 100.0 if r_pays > 0 else float('inf')
    current_share = game.h_fund / max(1.0, game.total_budget)
    net_h_shift = (h_share_ratio - current_share) * 100.0
    return gdp_change_pct, h_gross, h_net, r_gross, r_net, net_h_shift, -net_h_shift, est_gdp, est_h_fund, h_roi, r_roi

class Party:
    def __init__(self, name, cfg):
        self.name = name; self.wealth = cfg['INITIAL_WEALTH']; self.support = 50.0 
        self.build_ability = cfg['ABILITY_DEFAULT']; self.investigate_ability = cfg['ABILITY_DEFAULT']
        self.edu_ability = cfg['ABILITY_DEFAULT']; self.media_ability = cfg['ABILITY_DEFAULT']
        self.predict_ability = cfg['ABILITY_DEFAULT']
        self.current_forecast = 0.0; self.current_poll_result = None
        self.active_campaign_bonus = 0.0 # 競選殘留效果

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
