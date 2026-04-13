# ==========================================
# formulas.py
# ==========================================
import math

def get_ability_maintenance(dept, cfg):
    # 維護費依照「目標 (target)」收取，降級馬上省錢
    return cfg['MAINTENANCE_BASE'] + max(0, (dept.target - cfg['EFF_DEFAULT']) * 0.5)

def calc_upgrade(dept, new_target, invest_this_turn, cfg):
    dept.target = new_target
    refund = 0.0

    # 1. 升級邏輯
    if dept.target > dept.eff:
        total_cost = (dept.target - dept.eff) * cfg['UPGRADE_COST_PER_PCT']
        dept.invested += invest_this_turn

        if dept.invested >= total_cost and total_cost > 0:
            refund = dept.invested - total_cost # 計算溢出的退款
            dept.eff = dept.target
            dept.invested = 0.0 # 達標清空池子
        elif total_cost > 0:
            progress = invest_this_turn / total_cost
            dept.eff += (dept.target - dept.eff) * progress

    # 2. 降級邏輯 (不需要投錢，每年自然衰退，維護費即刻降低)
    elif dept.target < dept.eff:
        dept.invested = 0.0 # 清空舊資金
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
