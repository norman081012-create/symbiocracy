# ==========================================
# formulas.py
# Handles Core Stateless Pure Math Model Calculation
# ==========================================
import math
import random
import i18n
t = i18n.t

def calc_log_gain(invest_amount, base_cost=50.0):
    return math.log2(1 + (invest_amount / base_cost)) if invest_amount > 0 else 0.0

def get_ability_maintenance(current_val, cfg, is_build=False, build_ability=0.0):
    amount = (2**current_val - 1) * 50.0
    max_decay = cfg.get('DECAY_AMOUNT_BUILD', 500.0) if is_build else cfg.get('DECAY_AMOUNT_DEFAULT', 1500.0)
    decay_amt = min(amount, max_decay)
    # Higher engineering ability provides higher discount on maintenance
    discount_factor = 1.0 / (1.0 + build_ability / 5.0)
    return decay_amt * discount_factor * 0.1

def calc_unit_cost(cfg, gdp, build_abi, decay):
    # 🚀 Fix: Engineering department 30% actually exerts 60% building efficiency
    effective_build = build_abi * 2.0
    b_norm = max(0.01, effective_build / 10.0)
    inflation = max(0.0, (gdp - cfg.get('CURRENT_GDP', 5000.0)) / cfg.get('GDP_INFLATION_DIVISOR', 10000.0))
    base_cost = (0.5 / b_norm) * (2 ** (2 * decay - 1))
    return base_cost * (1 + inflation)

def calc_economy(cfg, gdp, budget_t, proj_fund, bid_cost, build_abi, forecast_decay, corr_amt=0.0, crony_base=0.0, override_unit_cost=None, r_pays=0.0, h_wealth=0.0):
    l_gdp = gdp * (forecast_decay * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE'])
    unit_cost = override_unit_cost if override_unit_cost is not None else calc_unit_cost(cfg, gdp, build_abi, forecast_decay)
    req_cost = bid_cost * unit_cost
    available_fund = max(0.0, proj_fund + r_pays - corr_amt + h_wealth)
    
    if req_cost <= available_fund:
        act_fund = req_cost
        c_net = float(bid_cost)
        h_idx = 1.0
    else:
        act_fund = available_fund
        c_net = act_fund / max(0.01, unit_cost)
        h_idx = c_net / max(1.0, float(bid_cost))

    payout_h = min(budget_t, proj_fund * h_idx)
    total_bonus_deduction = budget_t * ((cfg['BASE_INCOME_RATIO'] * 2) + cfg['RULING_BONUS_RATIO'])
    payout_r = max(0.0, budget_t - total_bonus_deduction - proj_fund)
    est_gdp = max(0.0, gdp - l_gdp + (c_net * cfg.get('GDP_CONVERSION_RATE', 0.2)))
    h_project_profit = payout_h + r_pays - act_fund
    
    return {
        'est_gdp': est_gdp, 'payout_h': payout_h, 'payout_r': payout_r,
        'h_idx': h_idx, 'c_net': c_net, 'l_gdp': l_gdp, 
        'unit_cost': unit_cost, 'act_fund': act_fund, 
        'h_project_profit': h_project_profit, 'req_cost': req_cost
    }

def generate_raw_support(cfg, new_gdp, curr_gdp, claimed_decay, bid_cost, c_net):
    delta_A = ((new_gdp - curr_gdp) / max(1.0, curr_gdp)) * 100.0
    expected_loss_pct = (claimed_decay * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE']) * 100.0
    delta_E = -expected_loss_pct

    gap = delta_A - delta_E
    weight = cfg.get('CLAIMED_DECAY_WEIGHT', 0.2)
    p_plan = delta_A + gap * weight

    completion_rate = c_net / max(1.0, float(bid_cost))
    delta_C = (completion_rate - 0.5) * 2.0 
    p_exec = abs(p_plan) * delta_C

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

def get_rigidity(i):
    x = (i - 100.5) / 99.5
    return 0.95 * (x**2) + 0.05

def run_conquest(boundary_B, net_support_A):
    B = int(boundary_B)
    support_used = 0.0
    conquered = 0

    if net_support_A > 0: 
        sup = net_support_A
        while sup >= 1.0 and B < 200:
            sup -= 1.0
            support_used += 1.0
            target = B + 1
            rigidity = get_rigidity(target)
            if random.random() < (1.0 - rigidity):
                B += 1
                conquered += 1
    elif net_support_A < 0: 
        sup = abs(net_support_A)
        while sup >= 1.0 and B > 0:
            sup -= 1.0
            support_used += 1.0
            target = B
            rigidity = get_rigidity(target)
            if random.random() < (1.0 - rigidity):
                B -= 1
                conquered += 1

    return B, support_used, conquered

def calc_performance_preview(cfg, hp, rp, ruling_party_name, new_gdp, curr_gdp, claimed_decay, sanity, emotion, bid_cost, c_net):
    p_plan, p_exec, d_a, d_e, d_c = generate_raw_support(cfg, new_gdp, curr_gdp, claimed_decay, bid_cost, c_net)

    plan_correct, plan_wrong, correct_prob = apply_sanity_filter(p_plan, sanity, emotion, is_preview=True)
    exec_correct, exec_wrong, _ = apply_sanity_filter(p_exec, sanity, emotion, is_preview=True)

    if ruling_party_name == hp.name:
        h_plan_sup = plan_correct; r_plan_sup = plan_wrong
    else:
        r_plan_sup = plan_correct; h_plan_sup = plan_wrong

    return {
        hp.name: {'perf_gdp': h_plan_sup, 'perf_proj': exec_correct},
        rp.name: {'perf_gdp': r_plan_sup, 'perf_proj': exec_wrong},
        'correct_prob': correct_prob,
        'p_plan': p_plan, 'p_exec': p_exec,
        'delta_A': d_a, 'delta_E': d_e, 'delta_C': d_c
    }
