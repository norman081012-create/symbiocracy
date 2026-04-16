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
    # 0 級無折扣 (1.0)，10 級打 5 折 (0.5)
    discount_factor = 1.0 - (build_abi / 10.0) * 0.5 
    inflation = max(0.0, (gdp - cfg.get('CURRENT_GDP', 5000.0)) / cfg.get('GDP_INFLATION_DIVISOR', 10000.0))
    base_cost = 0.85 * (2 ** (2 * decay - 1))
    return base_cost * discount_factor * (1 + inflation)

def calc_fake_ev_dice(total_fake_ev: float, catch_prob: float, fine_mult: float, chunk_size: float = 1.0, unit_cost: float = 1.0):
    if total_fake_ev <= 0 or chunk_size <= 0:
        return 0.0, total_fake_ev, 0.0, 0.0
        
    num_full_chunks = int(total_fake_ev / chunk_size)
    remainder = total_fake_ev - (num_full_chunks * chunk_size)
    
    caught_chunks = float(np.random.binomial(n=num_full_chunks, p=catch_prob)) if num_full_chunks > 0 else 0.0
    caught_int_amount = caught_chunks * chunk_size
    
    caught_remainder = remainder if random.random() < catch_prob else 0.0
    
    caught_fake_ev = caught_int_amount + caught_remainder
    safe_fake_ev = total_fake_ev - caught_fake_ev
    
    caught_value = caught_fake_ev * unit_cost
    fine = caught_value * fine_mult
    
    return caught_fake_ev, safe_fake_ev, caught_value, fine

def calc_economy(cfg, gdp, budget_t, proj_fund, bid_cost, build_abi, forecast_decay, r_pays=0.0, h_wealth=0.0, c_net_override=None, override_unit_cost=None, fake_ev=0.0):
    l_gdp = gdp * (forecast_decay * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE'])
    unit_cost = override_unit_cost if override_unit_cost is not None else calc_unit_cost(cfg, gdp, build_abi, forecast_decay)
    req_cost = bid_cost * unit_cost
    
    available_fund = max(0.0, proj_fund + r_pays + h_wealth)
    
    if c_net_override is not None:
        c_net_real = min(float(bid_cost), c_net_override)
        c_net_total = c_net_real + fake_ev
        act_fund = (c_net_real + fake_ev * cfg.get('FAKE_EV_COST_RATIO', 0.2)) * unit_cost
        h_idx = min(1.0, c_net_total / max(1.0, float(bid_cost)))
    else:
        if req_cost <= available_fund:
            act_fund = req_cost
            c_net_real = float(bid_cost)
            c_net_total = c_net_real + fake_ev
            h_idx = 1.0
        else:
            act_fund = available_fund
            c_net_real = act_fund / max(0.01, unit_cost)
            c_net_total = c_net_real + fake_ev
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

def apply_sanity_filter(raw_support, sanity, emotion, is_preview=False):
    crit_think = sanity / 100.0
    emo_val = emotion / 100.0
    correct_prob = max(0.05, min(0.95, crit_think * (1.0 - emo_val * 0.5)))

    if is_preview:
        return raw_support * correct_prob, raw_support * (1.0 - correct_prob), correct_prob

    correct_support = 0.0
    wrong_support = 0.0
    sign = 1.0 if raw_support >= 0 else -1.0
    abs_total = abs(raw_support)
    int_parts = int(abs_total)
    remainder = abs_total - int_parts

    for _ in range(int_parts):
        if random.random() < correct_prob:
            correct_support += 1.0
        else:
            wrong_support += 1.0
            
    if remainder > 0:
        if random.random() < correct_prob:
            correct_support += remainder
        else:
            wrong_support += remainder

    return correct_support * sign, wrong_support * sign, correct_prob

def apply_media_spin(blind_support, rightful_media, opp_media, is_preview=False):
    base_inertia = 5.0 
    total_power = rightful_media + opp_media + base_inertia
    
    if blind_support >= 0:
        move_prob = rightful_media / total_power
    else:
        move_prob = opp_media / total_power

    if is_preview:
        goes_to_rightful = blind_support * move_prob
        stays_with_opp = blind_support * (1.0 - move_prob)
        return goes_to_rightful, stays_with_opp

    goes_to_rightful = 0.0
    stays_with_opp = 0.0
    sign = 1.0 if blind_support >= 0 else -1.0
    abs_total = abs(blind_support)
    int_parts = int(abs_total)
    remainder = abs_total - int_parts

    for _ in range(int_parts):
        if random.random() < move_prob:
            goes_to_rightful += 1.0
        else:
            stays_with_opp += 1.0
            
    if remainder > 0:
        if random.random() < move_prob:
            goes_to_rightful += remainder
        else:
            stays_with_opp += remainder

    return goes_to_rightful * sign, stays_with_opp * sign

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

# 🛡️ 新增：公關火力專屬裝甲 (包含 Sanity 理智度防禦)
def get_spin_rigidity(i, sanity=50.0, buff_amt=0.0, buff_party=None, h_boundary=100, party_a_name=None):
    x = (i - 100.5) / 99.5
    base_rigidity = 0.95 * (x**2) + 0.05
    sanity_defense = (sanity / 100.0) * 0.5 
    final_rigidity = base_rigidity + sanity_defense
    if buff_amt > 0 and buff_party and party_a_name:
        belongs_to_A = (i <= h_boundary)
        if (buff_party == party_a_name and belongs_to_A) or (buff_party != party_a_name and not belongs_to_A):
            final_rigidity += buff_amt
    return min(1.0, final_rigidity)

# ⚔️ 新增：雙軌戰鬥結算 (真實政績 vs 公關操弄)
def run_conquest_split(boundary_B, net_perf_A, net_spin_A, sanity=50.0, buff_amt=0.0, buff_party=None, party_a_name=None):
    B = int(boundary_B)
    perf_used = 0.0; perf_conquered = 0
    if net_perf_A > 0:
        sup = net_perf_A
        while sup >= 1.0 and B < 200:
            sup -= 1.0; perf_used += 1.0; B += 1; perf_conquered += 1
    elif net_perf_A < 0:
        sup = abs(net_perf_A)
        while sup >= 1.0 and B > 0:
            sup -= 1.0; perf_used += 1.0; B -= 1; perf_conquered += 1
            
    spin_used = 0.0; spin_conquered = 0
    if net_spin_A > 0:
        sup = net_spin_A
        while sup >= 1.0 and B < 200:
            sup -= 1.0; spin_used += 1.0
            rigidity = get_spin_rigidity(B + 1, sanity, buff_amt, buff_party, boundary_B, party_a_name)
            if random.random() < (1.0 - rigidity):
                B += 1; spin_conquered += 1
    elif net_spin_A < 0:
        sup = abs(net_spin_A)
        while sup >= 1.0 and B > 0:
            sup -= 1.0; spin_used += 1.0
            rigidity = get_spin_rigidity(B, sanity, buff_amt, buff_party, boundary_B, party_a_name)
            if random.random() < (1.0 - rigidity):
                B -= 1; spin_conquered += 1

    return B, perf_used, perf_conquered, spin_used, spin_conquered

def calc_performance_preview(cfg, hp, rp, ruling_party_name, new_gdp, curr_gdp, claimed_decay, sanity, emotion, bid_cost, c_net_total, h_media_pwr=0.0, r_media_pwr=0.0):
    p_plan, p_exec, d_a, d_e, d_c = generate_raw_support(cfg, new_gdp, curr_gdp, claimed_decay, bid_cost, c_net_total)

    plan_correct, plan_wrong, correct_prob = apply_sanity_filter(p_plan, sanity, emotion, is_preview=True)
    exec_correct, exec_wrong, _ = apply_sanity_filter(p_exec, sanity, emotion, is_preview=True)
    
    if ruling_party_name == hp.name:
        ruling_media_pwr = h_media_pwr; opp_media_pwr = r_media_pwr
    else:
        ruling_media_pwr = r_media_pwr; opp_media_pwr = h_media_pwr
        
    ruling_reclaimed, opp_kept_plan = apply_media_spin(plan_wrong, ruling_media_pwr, opp_media_pwr, is_preview=True)
    h_reclaimed_exec, r_kept_exec = apply_media_spin(exec_wrong, h_media_pwr, r_media_pwr, is_preview=True)

    if ruling_party_name == hp.name:
        h_plan_sup = plan_correct + ruling_reclaimed
        r_plan_sup = opp_kept_plan
    else:
        r_plan_sup = plan_correct + ruling_reclaimed
        h_plan_sup = opp_kept_plan
        
    h_exec_sup = exec_correct + h_reclaimed_exec
    r_exec_sup = r_kept_exec

    return {
        hp.name: {'perf_gdp': h_plan_sup, 'perf_proj': h_exec_sup, 'spun_gdp': ruling_reclaimed if ruling_party_name == hp.name else opp_kept_plan, 'spun_proj': h_reclaimed_exec},
        rp.name: {'perf_gdp': r_plan_sup, 'perf_proj': r_exec_sup, 'spun_gdp': ruling_reclaimed if ruling_party_name == rp.name else opp_kept_plan, 'spun_proj': r_kept_exec},
        'correct_prob': correct_prob,
        'p_plan': p_plan, 'p_exec': p_exec,
        'delta_A': d_a, 'delta_E': d_e, 'delta_C': d_c
    }
