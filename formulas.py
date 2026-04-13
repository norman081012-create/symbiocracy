# ==========================================
# formulas.py
# ==========================================
import math

def get_dept_cost_cumulative(eff, cfg):
    # 使用等比級數或指數累加模擬對數曲線，越高等級越貴
    return cfg['UPGRADE_BASE_COST'] * (math.pow(cfg['UPGRADE_EXP_MULT'], eff) - 1) / (cfg['UPGRADE_EXP_MULT'] - 1)

def get_ability_maintenance(dept, cfg):
    # 維護費為升級總成本的 10%
    return get_dept_cost_cumulative(dept.target, cfg) * 0.1

def calc_upgrade(dept, new_target, invest_this_turn, cfg):
    dept.target = new_target
    refund = 0.0
    if dept.target > dept.eff:
        current_total_value = get_dept_cost_cumulative(dept.eff, cfg)
        target_total_value = get_dept_cost_cumulative(dept.target, cfg)
        total_cost_needed = target_total_value - current_total_value
        
        dept.invested += invest_this_turn
        if dept.invested >= total_cost_needed and total_cost_needed > 0:
            refund = dept.invested - total_cost_needed 
            dept.eff = dept.target
            dept.invested = 0.0 
        elif total_cost_needed > 0:
            progress = invest_this_turn / total_cost_needed
            dept.eff += (dept.target - dept.eff) * progress

    elif dept.target < dept.eff:
        dept.invested = 0.0 
        dept.eff -= cfg['DOWNGRADE_RATE_PER_YEAR']
        if dept.eff <= dept.target:
            dept.eff = dept.target
    return dept, refund

def calc_economic_preview(cfg, forecast_decay, gdp, budget_pool, proj_fund, strictness, build_eff):
    # 2. 衰退與阻力
    r_decay = forecast_decay * cfg['DECAY_COEFF']
    l_gdp = gdp * r_decay
    resistance = l_gdp * cfg['RESISTANCE_MULT']
    
    # 3. 建設與達標 (預估若投入全部 proj_fund)
    gross_output = proj_fund * (build_eff / 100.0)
    c_net = max(0.0, gross_output - resistance)
    
    # Target 定義為標案資金 * 實質成本(嚴格度)
    target_req = proj_fund * strictness
    h_index = min(1.0, c_net / max(1.0, target_req))
    
    # 4. GDP 結算預估
    est_gdp = max(0.0, gdp - l_gdp + c_net)
    
    # 5. 跨年資金預估
    residual = budget_pool - proj_fund
    est_h_income = proj_fund * h_index
    est_r_income = proj_fund * (1.0 - h_index) + residual
    
    return est_gdp, est_h_income, est_r_income, h_index, c_net

def calculate_civic_shifts(cfg, old_san, old_emo, gdp_growth_pct, edu_up, edu_down, incite, edu_eff, media_eff):
    san_delta = (edu_up * (edu_eff/100.0) * 0.002) - (edu_down * (edu_eff/100.0) * 0.002)
    new_san = max(0.0, min(1.0, old_san + san_delta))
    gdp_emo_effect = -(gdp_growth_pct * cfg['LIVELIHOOD_WEIGHT'] * (1.0 - new_san))
    incite_effect = incite * (media_eff/100.0) * 0.5
    new_emo = max(0.0, min(100.0, old_emo + gdp_emo_effect + incite_effect))
    return new_san, new_emo
