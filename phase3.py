# ==========================================
# phase3.py
# ==========================================
import streamlit as st
import random
import formulas

def render(game, cfg):
    st.header("⚖️ Phase 3: 年度結算與跨年物理演算")
    
    hp, rp = game.h_role_party, game.r_role_party
    ha = st.session_state[f"{hp.name}_acts"]
    ra = st.session_state[f"{rp.name}_acts"]
    
    if game.pending_payouts['H'] > 0 or game.pending_payouts['R'] > 0:
        hp.wealth += game.pending_payouts['H']
        rp.wealth += game.pending_payouts['R'] + game.pending_payouts['R_residual']
        st.success(f"💰 [年初入帳] 執行系統獲得獎勵: {game.pending_payouts['H']:.0f} | 監管系統回收尾款: {(game.pending_payouts['R']+game.pending_payouts['R_residual']):.0f}")
    
    ab = game.budget_t * cfg['BASE_ANNUITY']
    ar = game.budget_t * cfg['RULING_ANNUITY']
    hp.wealth += ab + (ar if game.ruling_party.name == hp.name else 0)
    rp.wealth += ab + (ar if game.ruling_party.name == rp.name else 0)
    
    # 扣除雙方出資與行動花費
    c_funds = st.session_state.turn_data.get('c_funds', 0)
    d_cost = st.session_state.turn_data.get('d_cost', 0)
    rp.wealth -= st.session_state.turn_data.get('r_pays', 0)
    hp.wealth -= st.session_state.turn_data.get('h_pays', 0)
    
    # 扣除當局行動花費
    for p, a in [(hp, ha), (rp, ra)]:
        p.wealth -= sum([a.get(k,0) for k in ['media','camp','incite','judicial','inv_pre','inv_inv','inv_med','inv_stl','inv_bld']])
        p.wealth -= abs(a.get('edu_amt', 0))

    # 貪污與抓弊結算
    corr_amt = c_funds * (ha['corr'] / 100.0)
    crony_base = c_funds * (ha['crony'] / 100.0)
    crony_income = crony_base * 0.1
    suspicious_total = corr_amt + crony_base
    act_build = c_funds - corr_amt # 實際進入建設的錢
    
    caught = False; fine = 0.0
    if suspicious_total > 0:
        catch_prob = min(1.0, (rp.investigate_ability / max(0.1, hp.stealth_ability)) * (suspicious_total / max(1.0, hp.wealth)) * 5.0)
        if random.random() < catch_prob:
            caught = True; fine = suspicious_total * cfg['CORRUPTION_PENALTY']
            st.error(f"🚨 [貪污被捕] 執行系統遭查獲！罰款: {fine:.0f}")
            hp.wealth -= fine; act_build += corr_amt; corr_amt = 0; crony_income = 0
            
    hp.wealth += corr_amt + crony_income
    
    # 經濟結算
    new_gdp, h_idx, c_net, l_gdp = formulas.calculate_economics_and_payouts(
        cfg, game.gdp, game.budget_t, c_funds, game.current_real_decay, act_build, hp.build_ability
    )
    
    st.info(f"🏗️ [建設結算] 實質產出: {c_net:.0f} | 阻力損耗: {l_gdp:.0f} | 最終 GDP: {game.gdp:.0f} ➔ {new_gdp:.0f}")
    
    game.pending_payouts['H'] = c_funds * h_idx
    game.pending_payouts['R'] = c_funds * max(0.0, (1.0 - h_idx))
    game.pending_payouts['R_residual'] = max(0.0, game.budget_t - c_funds)
    
    # 支持度結算
    v_r = (new_gdp - game.gdp) / max(1.0, game.gdp)
    v_h = h_idx - 1.0 
    r_shift = formulas.calc_support_shift_v3(v_r, cfg['GDP_PERF_WEIGHT'], game.sanity, game.emotion, ra['media'], ha['media'], v_r > 0)
    h_shift = formulas.calc_support_shift_v3(v_h, cfg['H_INDEX_PERF_WEIGHT'], game.sanity, game.emotion, ha['media'], ra['media'], v_h > 0)
    camp_shift = (ha['camp'] - ra['camp']) * (1.0 - (game.sanity / 100.0)) * 0.05
    
    total_h_shift = h_shift - r_shift + camp_shift
    if caught: total_h_shift -= 5.0
    hp.support = max(0.0, min(100.0, hp.support + total_h_shift))
    rp.support = 100.0 - hp.support
    
    # 資訊辨識與情緒更新
    t_san = max(0.0, min(100.0, 50.0 + (ra.get('edu_amt', 0) / 500.0) * 50.0))
    game.sanity = max(0.0, min(100.0, game.sanity - (game.emotion * 0.02) + (t_san - game.sanity) * 0.2))
    emo_delta = (ha['incite'] + ra['incite']) * 0.1 - (v_r * 100.0) - (game.sanity * 0.20)
    game.emotion = max(0.0, min(100.0, game.emotion + emo_delta))

    # 處理部門升級 (資金池累積)
    for p, acts, is_h in [(hp, ha, True), (rp, ra, False)]:
        p.invest_pools['pre'] += acts.get('inv_pre', 0)
        p.invest_pools['inv'] += acts.get('inv_inv', 0)
        p.invest_pools['med'] += acts.get('inv_med', 0)
        p.invest_pools['stl'] += acts.get('inv_stl', 0)
        if is_h: p.invest_pools['build'] += acts.get('inv_bld', 0)
        
        p.predict_ability, p.invest_pools['pre'] = formulas.process_upgrades(p.predict_ability, p.invest_pools['pre'], is_h, cfg)
        p.investigate_ability, p.invest_pools['inv'] = formulas.process_upgrades(p.investigate_ability, p.invest_pools['inv'], is_h, cfg)
        p.media_ability, p.invest_pools['med'] = formulas.process_upgrades(p.media_ability, p.invest_pools['med'], is_h, cfg)
        p.stealth_ability, p.invest_pools['stl'] = formulas.process_upgrades(p.stealth_ability, p.invest_pools['stl'], is_h, cfg)
        if is_h: p.build_ability, p.invest_pools['build'] = formulas.process_upgrades(p.build_ability, p.invest_pools['build'], is_h, cfg)
    
    game.last_year_report = {
        'old_gdp': game.gdp, 'old_san': game.sanity, 'old_emo': game.emotion,
        'h_party_name': hp.name, 'h_inc': game.pending_payouts['H'], 'r_inc': game.pending_payouts['R'] + game.pending_payouts['R_residual'],
        'real_decay': game.current_real_decay, 'view_party_forecast': game.proposing_party.current_forecast
    }

    game.gdp = new_gdp
    game.budget_t = new_gdp * cfg['TAX_RATE']
    
    if st.button("進入下一年", type="primary", use_container_width=True):
        game.year += 1; game.phase = 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party
        game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
        for k in list(st.session_state.keys()):
            if k.endswith('_acts'): del st.session_state[k]
        del st.session_state.turn_initialized; st.rerun()
