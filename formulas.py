# formulas.py
import math

def calculate_economics_and_payouts(cfg, gdp, budget_t, c_funds, r_decay, h_invest_funds, h_build_abi):
    """回傳: 結算後的 GDP, H-Index, C_net, L_gdp"""
    # 4. 環境物理
    l_gdp = gdp * (r_decay * cfg['DECAY_COEFF'] / 0.5)
    resistance = l_gdp * cfg['RESISTANCE_MULT']
    
    # 5. 實質產出
    gross_build = h_invest_funds * (1.0 + (h_build_abi / 100.0))
    c_net = max(0.0, gross_build - resistance)
    
    new_gdp = max(0.0, gdp + c_net - l_gdp)
    h_idx = c_net / max(1.0, float(c_funds)) if c_funds > 0 else 0.0
    
    return new_gdp, h_idx, c_net, l_gdp

def calc_support_shift_v3(v, weight, sanity, emotion, h_media, r_media, is_positive):
    """計算支持度單項位移 (回傳對政績黨的淨位移量)"""
    s_mult = (sanity / 100.0) * (1.0 - (emotion / 100.0))
    media_delta = (h_media - r_media) / 100.0
    
    if is_positive:
        if media_delta >= 0:
            return v * weight * (1 + media_delta) * s_mult
        else:
            return -(v * weight * abs(media_delta) * s_mult)
    else:
        v_abs = abs(v)
        if media_delta < 0:
            return -(v_abs * weight * (1 + abs(media_delta)) * s_mult)
        else:
            return v_abs * weight * media_delta * s_mult

def get_upgrade_cost_and_time(current_lvl, target_lvl, cfg):
    """計算對數升級成本與預估時間"""
    if target_lvl <= current_lvl: return 0.0, 0
    # 簡單的對數/指數成長：每 10 級成本翻倍
    cost = 0
    for lvl in range(int(current_lvl), int(target_lvl)):
        cost += cfg['BASE_UPGRADE_COST'] * (1.2 ** (lvl / 10.0))
    
    # 假設玩家每年全力投入 50 元，預估需要幾年
    est_years = math.ceil(cost / 50.0)
    return cost, est_years

def get_maintenance_fee(level, cfg):
    return level * cfg['MAINTENANCE_RATE']

def calc_preview(cfg, gdp, budget_t, c_funds, r_decay, h_build_abi):
    """給 Phase 1 智庫使用的預覽算式"""
    # 假設 H 投入資金等於 C_funds 進行估算
    new_gdp, h_idx, _, _ = calculate_economics_and_payouts(cfg, gdp, budget_t, c_funds, r_decay, c_funds, h_build_abi)
    
    # 預估次年收益
    h_est_income = c_funds * h_idx
    r_est_income = c_funds * (1 - h_idx) + (budget_t - c_funds)
    
    # 粗估 ROI
    h_roi = ((h_est_income - c_funds) / max(1.0, float(c_funds))) * 100 if c_funds > 0 else 0
    r_roi = ((r_est_income) / max(1.0, float(c_funds))) * 100 if c_funds > 0 else 0
    
    # 粗估支持度 (假設媒體對抗為 0)
    gdp_v = (new_gdp - gdp) / max(1.0, gdp)
    sup_shift = (h_idx - 1.0) * 10.0 + gdp_v * 100.0 # 簡易版預估
    
    return new_gdp, h_est_income, r_est_income, h_roi, r_roi, sup_shift
