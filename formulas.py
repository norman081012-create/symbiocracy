# ==========================================
# formulas.py
# ==========================================
import math

def get_ability_maintenance(dept, cfg):
    return cfg['MAINTENANCE_BASE'] + max(0, (dept.target - cfg['EFF_DEFAULT']) * 0.5)

def calc_upgrade(dept, new_target, invest_this_turn, cfg):
    dept.target = new_target
    refund = 0.0

    if dept.target > dept.eff:
        total_cost = (dept.target - dept.eff) * cfg['UPGRADE_COST_PER_PCT']
        dept.invested += invest_this_turn

        if dept.invested >= total_cost and total_cost > 0:
            refund = dept.invested - total_cost 
            dept.eff = dept.target
            dept.invested = 0.0 
        elif total_cost > 0:
            progress = invest_this_turn / total_cost
            dept.eff += (dept.target - dept.eff) * progress

    elif dept.target < dept.eff:
        dept.invested = 0.0 
        dept.eff -= cfg['DOWNGRADE_RATE_PER_YEAR']
        if dept.eff <= dept.target:
            dept.eff = dept.target

    return dept, refund

def calculate_civic_shifts(cfg, old_san, old_emo, gdp_growth_pct, edu_up_fund, edu_down_fund, incite_fund, edu_eff, media_eff):
    san_delta = (edu_up_fund * (edu_eff/100.0) * 0.002) - (edu_down_fund * (edu_eff/100.0) * 0.002)
    new_san = max(0.0, min(1.0, old_san + san_delta))
    gdp_emo_effect = -(gdp_growth_pct * cfg['LIVELIHOOD_WEIGHT'] * (1.0 - new_san))
    incite_effect = incite_fund * (media_eff/100.0) * 0.5
    new_emo = max(0.0, min(100.0, old_emo + gdp_emo_effect + incite_effect))
    return new_san, new_emo

def calculate_required_funds(cfg, t_h_fund, t_gdp, curr_h_fund, curr_gdp, r_val, forecast_decay, build_eff):
    strictness_multiplier = r_val ** 2 
    eff_decay_h = forecast_decay * strictness_multiplier * 0.2 * curr_h_fund
    req_boost_h = (t_h_fund - curr_h_fund) + eff_decay_h
    funds_h = (req_boost_h * max(0.1, strictness_multiplier)) / max(0.01, build_eff/100.0) if req_boost_h > 0 else 0

    eff_decay_gdp = forecast_decay * 1000
    req_boost_gdp = (t_gdp - curr_gdp) + eff_decay_gdp
    funds_gdp = (req_boost_gdp * cfg['BUILD_DIFF']) / max(0.01, build_eff/100.0) if req_boost_gdp > 0 else 0

    req_funds = max(0, int(funds_h + funds_gdp))
    h_ratio = funds_h / req_funds if req_funds > 0 else 1.0
    return req_funds, h_ratio

def calc_support_shift(cfg, hp, rp, act_h, act_gdp, t_h, t_gdp, curr_gdp, ha, ra):
    h_fail_pct = ((t_h - act_h) / max(1, float(t_h))) if act_h < t_h else 0.0
    r_fail_pct = ((t_gdp - act_gdp) / max(1, float(t_gdp))) if act_gdp < t_gdp else 0.0

    h_media_pow = ha['media'] * (hp.depts['media'].eff/100.0) * cfg['H_MEDIA_BONUS'] * cfg['MEDIA_DIFF']
    r_media_pow = ra['media'] * (rp.depts['media'].eff/100.0) * cfg['MEDIA_DIFF']

    h_blame_qty = h_fail_pct * cfg['PERF_IMPACT_BASE'] * max(1.0, r_media_pow * 0.01)
    r_blame_qty = r_fail_pct * cfg['PERF_IMPACT_BASE'] * max(1.0, h_media_pow * 0.01)

    h_camp_pow = ha['camp'] * (hp.depts['media'].eff/100.0) * cfg['MEDIA_DIFF']
    r_camp_pow = ra['camp'] * (rp.depts['media'].eff/100.0) * cfg['MEDIA_DIFF']
    total_camp_pow = max(1.0, h_camp_pow + r_camp_pow)
    
    h_eff_camp_qty = (h_camp_pow / total_camp_pow) * ha['camp']
    r_eff_camp_qty = (r_camp_pow / total_camp_pow) * ra['camp']

    hp_shift = (h_eff_camp_qty - h_blame_qty + r_blame_qty) * cfg['SUPPORT_CONVERSION_RATE']
    act_h_shift = hp_shift * ((100.0 - hp.support) / 100.0) if hp_shift > 0 else hp_shift * (hp.support / 100.0)
    
    return {'actual_shift': act_h_shift}

def calculate_preview(cfg, game, req_funds, h_ratio, r_val, fc_decay, hp_build_eff, r_pays, h_pays):
    # 此處加入 hp_build_eff/100.0 換算回原本的百分比邏輯
    gdp_bst = (req_funds * (hp_build_eff/100.0)) / cfg['BUILD_DIFF']
    est_gdp = max(0.0, game.gdp + gdp_bst - (fc_decay * 1000))
    gdp_change_pct = ((est_gdp - game.gdp) / max(1.0, game.gdp)) * 100.0

    actual_h_funds = req_funds * h_ratio
    strict_mult = r_val ** 2
    h_bst = (actual_h_funds * (hp_build_eff/100.0)) / max(0.1, strict_mult)
    eff_decay_h = fc_decay * strict_mult * 0.2 * game.h_fund
    est_h_fund = max(0.0, game.h_fund + h_bst - eff_decay_h)

    future_budget = cfg['BASE_TOTAL_BUDGET'] + (est_gdp * cfg['HEALTH_MULTIPLIER'])
    h_share_ratio = est_h_fund / max(1.0, future_budget) if future_budget > 0 else 0.5
    
    h_gross = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.h_role_party.name else 0) + (future_budget * h_share_ratio)
    r_gross = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.r_role_party.name else 0) + (future_budget * (1 - h_share_ratio))
    
    h_net = h_gross - h_pays
    r_net = r_gross - r_pays
    h_roi = (h_net / max(1.0, float(h_pays))) * 100.0 if h_pays > 0 else float('inf')
    r_roi = (r_net / max(1.0, float(r_pays))) * 100.0 if r_pays > 0 else float('inf')

    current_share = game.h_fund / max(1.0, game.total_budget)
    net_h_shift = (h_share_ratio - current_share) * 100.0
    
    return gdp_change_pct, h_gross, h_net, r_gross, r_net, net_h_shift, -net_h_shift, est_gdp, est_h_fund, h_roi, r_roi
