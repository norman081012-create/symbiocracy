# ==========================================
# formulas.py
# ==========================================
import math

def get_ability_maintenance(eff, cfg):
    return cfg['MAINTENANCE_BASE'] + max(0, (eff - cfg['EFF_DEFAULT']) * 0.5)

def calc_upgrade(dept, new_target, invest_this_turn, cfg):
    dept.target = new_target
    total_cost = max(0, (dept.target - dept.eff) * cfg['UPGRADE_COST_PER_PCT'])
    dept.invested += invest_this_turn
    if dept.invested >= total_cost and total_cost > 0:
        dept.eff = dept.target
        dept.invested = 0.0
    elif total_cost > 0:
        # 按比例推進效率
        progress = invest_this_turn / total_cost
        dept.eff += (dept.target - dept.eff) * progress
    return dept

def calculate_civic_shifts(cfg, old_san, old_emo, gdp_growth_pct, edu_up_fund, edu_down_fund, incite_fund, edu_eff, media_eff):
    # 資訊辨識度 = 投入教育資金 * 效率權重
    san_delta = (edu_up_fund * (edu_eff/100.0) * 0.002) - (edu_down_fund * (edu_eff/100.0) * 0.002)
    new_san = max(0.0, min(1.0, old_san + san_delta))
    
    # 選民情緒 = (GDP變化 * 民生權重 * (1-思辨度)) + 煽動
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
