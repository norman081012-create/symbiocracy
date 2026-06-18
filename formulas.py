# ==========================================
# formulas.py
# ==========================================
import math
import random
import numpy as np
import i18n
t = i18n.t

# 📌 全局裝甲權重 (用來調整擊穿難度)
RIGIDITY_WEIGHT = 2.5

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

def calc_economy(cfg, gdp, budget_t, proj_fund, total_bid_cost, build_abi, real_decay, override_unit_cost=None, r_pays=0.0, h_wealth=0.0, c_net_override=None, fake_ev_spent=0.0, fake_ev_safe=0.0, active_projects=None, allocations=None, fake_ev_caught=0.0, current_year=1):
    active_projects = active_projects or []
    allocations = allocations or {}
    
    l_gdp = gdp * (real_decay * cfg.get('DECAY_WEIGHT_MULT', 0.05) + cfg.get('BASE_DECAY_RATE', 0.0))
    unit_cost = override_unit_cost if override_unit_cost is not None else calc_unit_cost(cfg, gdp, build_abi, real_decay)
    
    unit_cost_eff = unit_cost / 1.2
    
    req_cost = total_bid_cost * unit_cost
    available_fund = max(0.0, proj_fund + r_pays + h_wealth)
    
    c_net_real = sum(data.get('real', 0.0) for data in allocations.values()) if isinstance(allocations, dict) else 0.0
    total_fake_spent = sum(data.get('fake', 0.0) for data in allocations.values()) if isinstance(allocations, dict) else 0.0
    c_net_total = c_net_real + total_fake_spent
    
    h_idx = min(1.0, c_net_total / max(1.0, float(total_bid_cost))) if total_bid_cost > 0 else 0.0
    act_fund = (c_net_real + total_fake_spent * cfg.get('FAKE_EV_COST_RATIO', 0.2)) * unit_cost_eff
    
    scale_down_ratio = 1.0
    if act_fund > available_fund and act_fund > 0:
        scale_down_ratio = available_fund / act_fund
        act_fund = available_fund
        c_net_real *= scale_down_ratio
        total_fake_spent *= scale_down_ratio
        c_net_total = c_net_real + total_fake_spent
        h_idx = min(1.0, c_net_total / max(1.0, float(total_bid_cost))) if total_bid_cost > 0 else 0.0

    payout_h = min(budget_t, proj_fund * h_idx)
    total_bonus_deduction = budget_t * ((cfg.get('BASE_INCOME_RATIO', 0.05) * 2) + cfg.get('RULING_BONUS_RATIO', 0.10))
    payout_r = max(0.0, budget_t - total_bonus_deduction - proj_fund)
    
    total_allocated = sum(d.get('real', 0) + d.get('fake', 0) for d in allocations.values()) if isinstance(allocations, dict) else 0.0
    effective_allocs = {}
    if isinstance(allocations, dict):
        for pid, data in allocations.items():
            real_amt = data.get('real', 0.0) * scale_down_ratio
            fake_amt = data.get('fake', 0.0) * scale_down_ratio
            
            total_fake_this_year = sum(d.get('fake', 0.0) * scale_down_ratio for d in allocations.values())
            if fake_ev_caught > 0 and total_fake_this_year > 0:
                caught_ratio = fake_ev_caught / total_fake_this_year
                fake_amt = max(0.0, fake_amt * (1.0 - caught_ratio))
                
            effective_allocs[pid] = {'real': real_amt, 'fake': fake_amt}

    completed_projects = []
    failed_projects = []
    ongoing_projects = []
    total_gdp_addition = 0.0

    for p in active_projects:
        p_copy = dict(p)
        p_copy['investments'] = list(p.get('investments', []))
        
        invested_so_far = sum(inv.get('real', inv.get('amount', 0.0)) + inv.get('fake', 0.0) for inv in p_copy['investments'])
        remaining_ev = p_copy.get('ev', 1.0) - invested_so_far
        
        alloc_data = effective_allocs.get(p_copy.get('id'), {'real': 0.0, 'fake': 0.0})
        alloc_real = alloc_data['real']
        alloc_fake = alloc_data['fake']
        alloc_total = alloc_real + alloc_fake
        
        if alloc_total > 0:
            p_copy['investments'].append({'year': current_year, 'amount': alloc_total, 'real': alloc_real, 'fake': alloc_fake})
            
        total_invested_now = invested_so_far + alloc_total
        
        if total_invested_now >= p_copy.get('ev', 1.0) * 0.99:
            tot_real = sum(inv.get('real', inv.get('amount', 0.0)) for inv in p_copy['investments'])
            tot_fake = sum(inv.get('fake', 0.0) for inv in p_copy['investments'])
            tot_amt = tot_real + tot_fake
            
            quality_ratio = (tot_real + 0.2 * tot_fake) / max(1.0, tot_amt)
            
            p_copy['exec_mult'] = p_copy.get('exec_mult', 1.0) * quality_ratio
            p_copy['macro_mult'] = p_copy.get('macro_mult', 1.0) * quality_ratio
            
            completed_projects.append(p_copy)
            total_gdp_addition += p_copy.get('ev', 0.0) * p_copy['macro_mult'] * cfg.get('GDP_CONVERSION_RATE', 0.2)
        else:
            min_req = remaining_ev * 0.2
            effective_survival_alloc = alloc_real + (alloc_fake * 0.2)
            
            if effective_survival_alloc < min_req - 0.01:
                failed_projects.append(p_copy)
            else:
                ongoing_projects.append(p_copy)
    
    est_gdp = max(0.0, gdp - l_gdp + total_gdp_addition)
    cost_real_ev = c_net_real * unit_cost_eff
    cost_fake_ev = (total_fake_spent * cfg.get('FAKE_EV_COST_RATIO', 0.2)) * unit_cost_eff
    h_project_profit = payout_h + r_pays - (cost_real_ev + cost_fake_ev)
    
    return {
        'est_gdp': est_gdp, 'payout_h': payout_h, 'payout_r': payout_r,
        'h_idx': h_idx, 'c_net': c_net_real, 'c_net_total': c_net_total, 'l_gdp': l_gdp, 
        'unit_cost': unit_cost_eff, 'act_fund': act_fund, 
        'cost_real_ev': cost_real_ev, 'cost_fake_ev': cost_fake_ev,
        'h_project_profit': h_project_profit, 'req_cost': req_cost,
        'completed_projects': completed_projects,
        'failed_projects': failed_projects,
        'ongoing_projects': ongoing_projects,
        'total_fake_spent': total_fake_spent * scale_down_ratio
    }

def get_depreciated_perf(party, perf_type, current_year):
    if not hasattr(party, 'perf_history'):
        return 0.0
    total = 0.0
    history = party.perf_history.get(perf_type, [])
    history = [item for item in history if (current_year - item.get('year', current_year)) < 6]
    party.perf_history[perf_type] = history
    
    for item in history:
        age = current_year - item.get('year', current_year)
        retention = max(0.0, (6.0 - age) / 6.0)
        total += item.get('amount', 0.0) * retention
        
    return total

def generate_raw_support(cfg, curr_gdp, claimed_decay, completed_projects, real_decay, current_year):
    target_gdp_growth_val = sum(p.get('ev', 0.0) * p.get('macro_mult', 1.0) * cfg.get('GDP_CONVERSION_RATE', 0.2) for p in completed_projects)
    delta_A = (target_gdp_growth_val / max(1.0, curr_gdp)) * 100.0
    
    real_loss_pct = (real_decay * cfg.get('DECAY_WEIGHT_MULT', 0.05) + cfg.get('BASE_DECAY_RATE', 0.0)) * 100.0
    expected_loss_pct = (claimed_decay * cfg.get('DECAY_WEIGHT_MULT', 0.05) + cfg.get('BASE_DECAY_RATE', 0.0)) * 100.0
    
    actual_net_growth = delta_A - real_loss_pct
    expected_net_growth = -expected_loss_pct
    
    gap = actual_net_growth - expected_net_growth
    
    p_ruling = 0.0
    p_opp = 0.0
    
    if actual_net_growth >= 0:
        p_ruling_raw = (actual_net_growth * 0.05) + (gap * 0.15)
        p_ruling = max(0.0, p_ruling_raw * cfg.get('AMMO_MULTIPLIER', 50.0))
    else:
        p_opp_raw = abs(actual_net_growth * 0.05) + (abs(gap) * 0.15 if gap < 0 else 0.0)
        p_opp = max(0.0, p_opp_raw * cfg.get('AMMO_MULTIPLIER', 50.0))
        
    exec_perf = 0.0
    proposal_perf = {}
    inflation_corr = 5000.0 / max(1.0, curr_gdp)
    
    for p in completed_projects:
        depreciated_ev = 0.0
        for inv in p.get('investments', []):
            age = current_year - inv.get('year', current_year)
            retention = max(0.1, 1.0 - real_decay) ** age
            depreciated_ev += inv.get('amount', 0.0) * retention
            
        base_perf = (depreciated_ev * p.get('exec_mult', 1.0) * inflation_corr) / 20.0
        exec_perf += base_perf
        
        author = p.get('author', 'System')
        proposal_perf[author] = proposal_perf.get(author, 0.0) + base_perf
        
    return p_ruling, p_opp, exec_perf, proposal_perf, actual_net_growth, expected_net_growth

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

def get_sanity_accuracy(sanity, emotion):
    acc = (sanity / 100.0) - (emotion / 200.0)
    return max(0.01, min(1.0, acc))

# 📌 全新改版的征服演算法：雙軌道 (政績理智放大 vs 洗腦無知放大)
def run_conquest_split(boundary_B, net_perf_A, net_spin_A, spin_A, spin_B, sanity=50.0, emotion=30.0, censor_penalty_A=0.0, censor_penalty_B=0.0, buff_amt=0.0, buff_party=None, party_a_name=None):
    B = float(boundary_B)
    sanity_acc = get_sanity_accuracy(sanity, emotion)

    # ==========================================
    # 軌道 A：政績影響力 (Fact Track)
    # ==========================================
    perf_raw = abs(net_perf_A)
    perf_core = 0.0
    perf_ratio = 0.0
    perf_ex = 0.0
    perf_conquered = 0

    if net_perf_A != 0:
        is_a_atk = (net_perf_A > 0)
        
        # 階段 1：理智共鳴放大 (1 + 理智準確率)
        perf_core = perf_raw * (1.0 + sanity_acc)

        # 階段 2：媒體宣傳 EX (1 + 媒體落差比例)
        if spin_A + spin_B > 0:
            perf_ratio = (spin_A - spin_B) / (spin_A + spin_B) if is_a_atk else (spin_B - spin_A) / (spin_A + spin_B)
        else:
            perf_ratio = 0.0
        
        perf_multiplier = max(0.0, 1.0 + perf_ratio)
        perf_ex = perf_core * perf_multiplier

        # 階段 3：鐵票剛性最終擊穿
        sup = perf_ex
        while sup >= 1.0:
            sup -= 1.0
            idx = int(B) + 1 if is_a_atk else int(B)
            if not (1 <= idx <= 200): break
            rigidity = get_base_rigidity(idx, buff_amt, buff_party, boundary_B, party_a_name)
            if random.random() < (1.0 - rigidity):
                B = B + 1 if is_a_atk else B - 1
                perf_conquered += 1

    # ==========================================
    # 軌道 B：純粹公關洗腦 (Spin Track)
    # ==========================================
    spin_raw = abs(net_spin_A)
    spin_core = 0.0
    spin_ratio = 0.0
    spin_ex = 0.0
    spin_blocked = 0.0
    spin_eff = 0.0
    spin_conquered = 0

    if net_spin_A != 0:
        is_a_atk_spin = (net_spin_A > 0)
        
        # 階段 1：無知/情緒放大 (1 + (1 - 理智準確率))
        spin_core = spin_raw * (1.0 + (1.0 - sanity_acc))

        # 階段 2：媒體宣傳 EX (1 + 媒體落差比例)
        if spin_A + spin_B > 0:
            spin_ratio = (spin_A - spin_B) / (spin_A + spin_B) if is_a_atk_spin else (spin_B - spin_A) / (spin_A + spin_B)
        else:
            spin_ratio = 0.0
            
        spin_multiplier = max(0.0, 1.0 + spin_ratio)
        spin_ex = spin_core * spin_multiplier

        # 階段 3：理智裝甲最終格擋
        censor_opp = censor_penalty_B if is_a_atk_spin else censor_penalty_A
        eff_sanity_acc = max(0.0, sanity_acc - censor_opp) # 審查會剝奪理智防禦力
        
        spin_blocked = spin_ex * eff_sanity_acc
        spin_eff = spin_ex - spin_blocked

        # 階段 4：鐵票剛性最終擊穿
        sup = spin_eff
        while sup >= 1.0:
            sup -= 1.0
            idx = int(B) + 1 if is_a_atk_spin else int(B)
            if not (1 <= idx <= 200): break
            rigidity = get_base_rigidity(idx, buff_amt, buff_party, boundary_B, party_a_name)
            if random.random() < (1.0 - rigidity):
                B = B + 1 if is_a_atk_spin else B - 1
                spin_conquered += 1

    B = max(0.0, min(200.0, B))

    return {
        'new_boundary': B,
        'perf_raw': perf_raw,
        'perf_core': perf_core,
        'perf_multiplier': 1.0 + perf_ratio,
        'perf_ex': perf_ex,
        'perf_conquered': perf_conquered,
        'spin_raw': spin_raw,
        'spin_core': spin_core,
        'spin_multiplier': 1.0 + spin_ratio,
        'spin_ex': spin_ex,
        'spin_blocked': spin_blocked,
        'spin_eff': spin_eff,
        'spin_conquered': spin_conquered
    }

def calc_performance_preview(cfg, hp, rp, ruling_party_name, curr_gdp, claimed_decay, sanity, emotion, projects, h_spin_pwr=0.0, r_spin_pwr=0.0, real_decay=0.0, current_year=1):
    hp_name = getattr(hp, 'name', str(hp))
    rp_name = getattr(rp, 'name', str(rp))
    
    p_ruling, p_opp, p_exec, p_prop, d_a, d_e = generate_raw_support(cfg, curr_gdp, claimed_decay, projects, real_decay, current_year)

    h_perf = p_exec + p_prop.get(hp_name, 0.0)
    r_perf = p_prop.get(rp_name, 0.0)
    
    if ruling_party_name == hp_name: 
        h_perf += p_ruling
        r_perf += p_opp
    if ruling_party_name == rp_name: 
        r_perf += p_ruling
        h_perf += p_opp

    perf_ap_center = 1.0 - get_sanity_accuracy(sanity, emotion)
    spin_ap_center = 1.0 - get_sanity_accuracy(sanity, emotion)

    return {
        hp_name: {'perf': h_perf, 'spin': h_spin_pwr, 'ruling': p_ruling if ruling_party_name==hp_name else p_opp, 'exec': p_exec, 'prop': p_prop.get(hp_name, 0)},
        rp_name: {'perf': r_perf, 'spin': r_spin_pwr, 'ruling': p_ruling if ruling_party_name==rp_name else p_opp, 'exec': 0, 'prop': p_prop.get(rp_name, 0)},
        'perf_ap_center': perf_ap_center,
        'spin_ap_center': spin_ap_center,
        'delta_A': d_a, 'delta_E': d_e
    }
