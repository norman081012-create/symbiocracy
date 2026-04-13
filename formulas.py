# ==========================================
# formulas.py
# 負責核心無狀態的純數學模型計算 (完全替換為 v3 邏輯)
# ==========================================
import math

def calculate_economics_and_payouts(cfg, gdp, budget_t, c_funds, r_decay, h_invest_funds, h_build_abi):
    l_gdp = gdp * (r_decay * cfg['DECAY_COEFF'] / 0.5)
    resistance = l_gdp * cfg['RESISTANCE_MULT']
    
    gross_build = h_invest_funds * (1.0 + (h_build_abi / 100.0))
    c_net = max(0.0, gross_build - resistance)
    
    new_gdp = max(0.0, gdp + c_net - l_gdp)
    h_idx = c_net / max(1.0, float(c_funds)) if c_funds > 0 else 0.0
    
    return new_gdp, h_idx, c_net, l_gdp

def calc_support_shift_v3(v, weight, sanity, emotion, h_media, r_media, is_positive):
    s_mult = (sanity / 100.0) * (1.0 - (emotion / 100.0))
    media_delta = (h_media - r_media) / 100.0
    
    if is_positive:
        if media_delta >= 0: return v * weight * (1 + media_delta) * s_mult
        else: return -(v * weight * abs(media_delta) * s_mult)
    else:
        v_abs = abs(v)
        if media_delta < 0: return -(v_abs * weight * (1 + abs(media_delta)) * s_mult)
        else: return v_abs * weight * media_delta * s_mult

def get_cost_to_next_level(current_lvl, cfg):
    return cfg['BASE_UPGRADE_COST'] * (1.2 ** (current_lvl / 10.0))

def get_upgrade_cost_and_time(current_lvl, target_lvl, cfg):
    if target_lvl <= current_lvl: return 0.0, 0
    cost = 0
    for lvl in range(int(current_lvl), int(target_lvl)):
        cost += get_cost_to_next_level(lvl, cfg)
    est_years = math.ceil(cost / 50.0)
    return cost, est_years

def process_upgrades(current_level, pool, is_h, cfg):
    mult = 1.2 if is_h else 1.0 # 執行系統工程處 buff
    effective_pool = pool * mult
    
    while current_level < cfg['MAX_ABILITY']:
        cost_to_next = get_cost_to_next_level(current_level, cfg)
        if effective_pool >= cost_to_next:
            effective_pool -= cost_to_next
            current_level += 1
        else:
            break
            
    new_pool = effective_pool / mult if mult > 0 else effective_pool
    return min(current_level, cfg['MAX_ABILITY']), new_pool

def get_maintenance_fee(level, cfg):
    return level * cfg['MAINTENANCE_RATE']

def calc_preview(cfg, gdp, budget_t, c_funds, r_decay, h_build_abi):
    new_gdp, h_idx, _, _ = calculate_economics_and_payouts(cfg, gdp, budget_t, c_funds, r_decay, c_funds, h_build_abi)
    h_est_income = c_funds * h_idx
    r_est_income = c_funds * (1 - h_idx) + (budget_t - c_funds)
    
    h_roi = ((h_est_income - c_funds) / max(1.0, float(c_funds))) * 100 if c_funds > 0 else 0
    r_roi = ((r_est_income) / max(1.0, float(c_funds))) * 100 if c_funds > 0 else 0
    
    gdp_v = (new_gdp - gdp) / max(1.0, gdp)
    sup_shift = (h_idx - 1.0) * 10.0 + gdp_v * 100.0 
    
    return new_gdp, h_est_income, r_est_income, h_roi, r_roi, sup_shift
