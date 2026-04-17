# ==========================================
# formulas.py
# ==========================================
import math
import random
import numpy as np
import i18n
t = i18n.t

def calc_log_gain(invest_amount, base_cost=50.0):
    return math.log2(1 + (invest_amount / base_cost)) if invest_amount > 0 else 0.0

def calc_unit_cost(cfg, gdp, build_abi, decay):
    discount_factor = 1.0 - (build_abi / 10.0) * 0.5 
    inflation = max(0.0, (gdp - cfg.get('CURRENT_GDP', 5000.0)) / cfg.get('GDP_INFLATION_DIVISOR', 10000.0))
    base_cost = 0.85 * (2 ** (2 * decay - 1))
    return base_cost * discount_factor * (1 + inflation)

def calc_fake_ev_dice(total_fake_ev: float, catch_prob: float, fine_mult: float, chunk_size: float = 5.0, unit_cost: float = 1.0):
    if total_fake_ev <= 0 or catch_prob <= 0 or chunk_size == float('inf'):
        return 0.0, total_fake_ev, 0.0, 0.0
        
    num_chunks = int(total_fake_ev / chunk_size)
    remainder = total_fake_ev - (num_chunks * chunk_size)
    
    caught_chunks = float(np.random.binomial(n=num_chunks, p=catch_prob)) if num_chunks > 0 else 0.0
    caught_remainder = remainder if random.random() < catch_prob else 0.0
    
    caught_fake_ev = (caught_chunks * chunk_size) + caught_remainder
    safe_fake_ev = total_fake_ev - caught_fake_ev
    
    caught_value = caught_fake_ev * unit_cost
    fine = caught_value * fine_mult
    
    return caught_fake_ev, safe_fake_ev, caught_value, fine

def calc_economy(cfg, gdp, budget_t, proj_fund, bid_cost, build_abi, forecast_decay, r_pays=0.0, h_wealth=0.0, c_net_override=None, override_unit_cost=None, fake_ev_spent=0.0, fake_ev_safe=0.0):
    l_gdp = gdp * (forecast_decay * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE'])
    unit_cost = override_unit_cost if override_unit_cost is not None else calc_unit_cost(cfg, gdp, build_abi, forecast_decay)
    req_cost = bid_cost * unit_cost
    
    available_fund = max(0.0, proj_fund + r_pays + h_wealth)
    
    if c_net_override is not None:
        c_net_real = min(float(bid_cost), c_net_override)
        c_net_total = c_net_real + fake_ev_safe
        act_fund = (c_net_real + fake_ev_spent * cfg.get('FAKE_EV_COST_RATIO', 0.2)) * unit_cost
        h_idx = min(1.0, c_net_total / max(1.0, float(bid_cost)))
    else:
        if req_cost <= available_fund:
            act_fund = req_cost
            c_net_real = float(bid_cost)
            c_net_total = c_net_real + fake_ev_safe
            h_idx = min(1.0, c_net_total / max(1.0, float(bid_cost)))
        else:
            act_fund = available_fund
            c_net_real = act_fund / max(0.01, unit_cost)
            c_net_total = c_net_real + fake_ev_safe
            h_idx = min(1.0, c_net_total / max(1.0, float(bid_cost)))

    payout_h = min(budget_t, proj_fund * h_idx)
    total_bonus_deduction = budget_t * ((cfg['BASE_INCOME_RATIO'] * 2) + cfg['RULING_BONUS_RATIO'])
    payout_r = max(0.0, budget_t - total_bonus_deduction - proj_fund)
    
    est_gdp = max(0.0, gdp - l_gdp + (c_net_real * cfg.get('GDP_CONVERSION_RATE', 0.2)))
    
    h_project_profit = payout_h + r_pays - act_fund
    
    return {
        'est_gdp': est_gdp, 'payout_h': payout_h, 'payout_r': payout_r,
        'h_idx': h_idx, 'c_net': c_net_real, 'c_net_total': c_net_total, 'l_gdp': l_gdp, 
        'unit_cost': unit_cost, 'act_fund': act_fund, 
        'h_project_profit': h_project_profit, 'req_cost': req_cost
    }

def generate_raw_support(cfg, new_gdp, curr_gdp, claimed_decay, bid_cost, c_net_total):
    delta_A = ((new_gdp - curr_gdp) / max(1.0, curr_gdp)) * 100.0
    expected_loss_pct = (claimed_decay * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE']) * 100.0
    delta_E = -expected_loss_pct

    gap = delta_A - delta_E
    p_plan = (delta_A * 0.05) + (gap * 0.15)

    completion_rate = c_net_total / max(1.0, float(bid_cost))
    delta_C = (completion_rate - 0.5) * 2.0 
    
    target_gdp_growth = (bid_cost * cfg.get('GDP_CONVERSION_RATE', 0.2)) / max(1.0, curr_gdp) * 100.0
    p_exec = target_gdp_growth * delta_C * 0.1

    support_mult = cfg.get('AMMO_MULTIPLIER', 50.0) 
    return p_plan * support_mult, p_exec * support_mult, delta_A, delta_E, delta_C

def calc_incite_success(base_incite_rolls, current_emotion, is_preview=False):
    if is_preview:
        success_rate = (100.0 - current_emotion) / 100.0
        return base_incite_rolls * success_rate

    successful_incites = 0.0
    temp_emotion = current_emotion
    int_rolls = int(base_incite_rolls)
    
    for _ in range(int_rolls):
        if temp_emotion >= 100.0: break
        success_prob = (100.0 - temp_emotion) / 100.0
        if random.random() < success_prob:
            successful_incites += 1.0
            temp_emotion += 1.0 
            
    return successful_incites

def get_base_rigidity(i, buff_amt=0.0, buff_party=None, h_boundary=100, party_a_name=None):
    x = (i - 100.5) / 99.5
    base_rigidity = 0.95 * (x**2) + 0.05
    if buff_amt > 0 and buff_party and party_a_name:
        belongs_to_A = (i <= h_boundary)
        if (buff_party == party_a_name and belongs_to_A) or (buff_party != party_a_name and not belongs_to_A):
            base_rigidity += buff_amt
    return min(1.0, base_rigidity)

def get_defense_modifier(sanity, emotion, edu_stance):
    return (sanity / 100.0) * 0.5 - (emotion / 100.0) * 0.5 + (edu_stance / 100.0) * 0.5

def get_perf_rigidity(i, sanity, emotion, edu_stance, buff_amt=0.0, buff_party=None, h_boundary=100, party_a_name=None):
    base_rigidity = get_base_rigidity(i, buff_amt, buff_party, h_boundary, party_a_name)
    modifier = get_defense_modifier(sanity, emotion, edu_stance)
    return max(0.01, min(1.0, base_rigidity - modifier))

def get_spin_rigidity(i, sanity, emotion, edu_stance, buff_amt=0.0, buff_party=None, h_boundary=100, party_a_name=None):
    base_rigidity = get_base_rigidity(i, buff_amt, buff_party, h_boundary, party_a_name)
    modifier = get_defense_modifier(sanity, emotion, edu_stance)
    return max(0.01, min(1.0, base_rigidity + modifier))

def run_conquest_split(boundary_B, net_perf_A, net_spin_A, sanity=50.0, emotion=30.0, edu_stance=0.0, buff_amt=0.0, buff_party=None, party_a_name=None):
    B = int(boundary_B)
    perf_used = 0.0; perf_conquered = 0
    
    if net_perf_A > 0:
        sup = net_perf_A
        while sup >= 1.0 and B < 200:
            sup -= 1.0; perf_used += 1.0
            rigidity = get_perf_rigidity(B + 1, sanity, emotion, edu_stance, buff_amt, buff_party, boundary_B, party_a_name)
            if random.random() < (1.0 - rigidity):
                B += 1; perf_conquered += 1
    elif net_perf_A < 0:
        sup = abs(net_perf_A)
        while sup >= 1.0 and B > 0:
            sup -= 1.0; perf_used += 1.0
            rigidity = get_perf_rigidity(B, sanity, emotion, edu_stance, buff_amt, buff_party, boundary_B, party_a_name)
            if random.random() < (1.0 - rigidity):
                B -= 1; perf_conquered += 1
            
    spin_used = 0.0; spin_conquered = 0
    if net_spin_A > 0:
        sup = net_spin_A
        while sup >= 1.0 and B < 200:
            sup -= 1.0; spin_used += 1.0
            rigidity = get_spin_rigidity(B + 1, sanity, emotion, edu_stance, buff_amt, buff_party, boundary_B, party_a_name)
            if random.random() < (1.0 - rigidity):
                B += 1; spin_conquered += 1
    elif net_spin_A < 0:
        sup = abs(net_spin_A)
        while sup >= 1.0 and B > 0:
            sup -= 1.0; spin_used += 1.0
            rigidity = get_spin_rigidity(B, sanity, emotion, edu_stance, buff_amt, buff_party, boundary_B, party_a_name)
            if random.random() < (1.0 - rigidity):
                B -= 1; spin_conquered += 1

    return B, perf_used, perf_conquered, spin_used, spin_conquered

def calc_performance_preview(cfg, hp, rp, ruling_party_name, new_gdp, curr_gdp, claimed_decay, sanity, emotion, bid_cost, c_net_total, h_spin_pwr=0.0, r_spin_pwr=0.0, avg_edu=0.0):
    p_plan, p_exec, d_a, d_e, d_c = generate_raw_support(cfg, new_gdp, curr_gdp, claimed_decay, bid_cost, c_net_total)

    # 監管方 (Regulator) 嚴格且唯一地取得大環境/預期政績 (p_plan)
    # 執行方 (Executive) 嚴格且唯一地取得專案執行表現 (p_exec)
    h_perf = p_exec 
    r_perf = p_plan

    perf_ap_center = 1.0 - get_perf_rigidity(100, sanity, emotion, avg_edu)
    spin_ap_center = 1.0 - get_spin_rigidity(100, sanity, emotion, avg_edu)

    return {
        hp.name: {'perf': h_perf, 'spin': h_spin_pwr},
        rp.name: {'perf': r_perf, 'spin': r_spin_pwr},
        'perf_ap_center': perf_ap_center,
        'spin_ap_center': spin_ap_center,
        'p_plan': p_plan, 'p_exec': p_exec,
        'delta_A': d_a, 'delta_E': d_e, 'delta_C': d_c
    }
