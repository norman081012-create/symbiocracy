# ==========================================
# formulas.py
# Responsible for core stateless pure mathematical model calculations
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
    discount_factor = 1.0 - (build_ability * 0.02)
    return decay_amt * max(0.1, discount_factor) * 0.1

def calculate_upgrade_cost(current_val, target_val, cfg, is_build=False, build_ability=0.0):
    a_c = (2**current_val - 1) * 50.0
    a_t = (2**target_val - 1) * 50.0
    max_decay = cfg.get('DECAY_AMOUNT_BUILD', 500.0) if is_build else cfg.get('DECAY_AMOUNT_DEFAULT', 1500.0)
    a_base = max(0.0, a_c - max_decay)
    if a_t <= a_base: return 0.0
    req_amt = a_t - a_base
    discount_factor = 1.0 - (build_ability * 0.02)
    return req_amt * max(0.1, discount_factor) * 0.1

def calc_unit_cost(cfg, gdp, build_abi, decay):
    b_norm = max(0.01, build_abi / 10.0)
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

def distribute_points_by_dice(total_points, correct_prob):
    """
    Point-by-point rolling mechanism: splits total points into 1 by 1 and rolls based on accuracy probability.
    Returns: (Points earned by correct attribution, Points earned by wrong attribution)
    """
    correct_pts = 0.0
    wrong_pts = 0.0
    sign = 1.0 if total_points >= 0 else -1.0
    abs_total = abs(total_points)
    int_parts = int(abs_total)
    remainder = abs_total - int_parts
    
    # Roll for each integer point
    for _ in range(int_parts):
        if random.random() < correct_prob:
            correct_pts += 1.0
        else:
            wrong_pts += 1.0
            
    # Final roll for decimal remainder
    if remainder > 0:
        if random.random() < correct_prob:
            correct_pts += remainder
        else:
            wrong_pts += remainder
            
    return correct_pts * sign, wrong_pts * sign

def calc_performance_amounts(cfg, hp, rp, ruling_party_name, new_gdp, curr_gdp, claimed_decay, sanity, emotion, bid_cost, c_net, is_preview=True):
    expected_drop_pct = claimed_decay * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE']
    expected_drop_amt = curr_gdp * expected_drop_pct
    actual_drop_amt = curr_gdp - new_gdp
    perf_const = 0.01 
    
    if expected_drop_amt > 0.001:
        gdp_perf_base = - (actual_drop_amt / expected_drop_amt) * curr_gdp * perf_const
    else:
        gdp_perf_base = - actual_drop_amt * perf_const
        
    # Voter sanity filter (Correct attribution rate)
    crit_think = sanity / 100.0
    emo_val = emotion / 100.0
    correct_prob = max(0.05, min(0.95, crit_think * (1.0 - emo_val * 0.5))) 
    
    shifts = {
        hp.name: {'perf': 0.0, 'perf_gdp': 0.0, 'perf_proj': 0.0, 'camp': 0.0, 'backlash': 0.0}, 
        rp.name: {'perf': 0.0, 'perf_gdp': 0.0, 'perf_proj': 0.0, 'camp': 0.0, 'backlash': 0.0}
    }
    
    # 1. Macro-Environment GDP Performance Attribution
    if is_preview:
        ruling_gdp_perf = gdp_perf_base * correct_prob
        exec_wrong_gdp_perf = gdp_perf_base * (1.0 - correct_prob)
    else:
        ruling_gdp_perf, exec_wrong_gdp_perf = distribute_points_by_dice(gdp_perf_base, correct_prob)
        
    shifts[ruling_party_name]['perf_gdp'] += ruling_gdp_perf
    shifts[ruling_party_name]['perf'] += ruling_gdp_perf
    
    shifts[hp.name]['perf_gdp'] += exec_wrong_gdp_perf
    shifts[hp.name]['perf'] += exec_wrong_gdp_perf
    
    # 2. Project Performance (Labor Bonus) Attribution
    completion_rate = min(1.0, c_net / max(1.0, bid_cost))
    project_perf_base = (c_net / max(1.0, curr_gdp)) * 250.0 * completion_rate
    
    if is_preview:
        h_proj_perf = project_perf_base * correct_prob
        r_wrong_proj_perf = project_perf_base * (1.0 - correct_prob)
    else:
        # Correctly attributed to executor, incorrectly judged means free-ride by oversight
        h_proj_perf, r_wrong_proj_perf = distribute_points_by_dice(project_perf_base, correct_prob)
        
    shifts[hp.name]['perf_proj'] += h_proj_perf
    shifts[hp.name]['perf'] += h_proj_perf
    
    shifts[rp.name]['perf_proj'] += r_wrong_proj_perf
    shifts[rp.name]['perf'] += r_wrong_proj_perf
    
    shifts['project_perf'] = project_perf_base
    shifts['correct_prob'] = correct_prob
    shifts['h_proj_preview'] = h_proj_perf
    shifts['r_proj_preview'] = r_wrong_proj_perf
    
    return shifts

def get_formula_explanation(game, view_party, plan, cfg):
    tt_drop = view_party.current_forecast
    build_abi = game.h_role_party.build_ability
    res = calc_economy(cfg, game.gdp, game.total_budget, plan['proj_fund'], plan['bid_cost'], build_abi, tt_drop, r_pays=plan.get('r_pays', 0.0), h_wealth=game.h_role_party.wealth)
    
    lines = []
    lines.append(f"**Our estimation calculation is complete.**")
    lines.append(f"**Expected GDP Shift:** `{res['est_gdp']:.1f}`")
    lines.append(f"> Est Construction Net (C_net): {res['c_net']:.1f} / Bid Commitment (Bid_cost): {plan['bid_cost']:.1f}")
    return lines
