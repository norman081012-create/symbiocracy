# phase3.py
import streamlit as st
import formulas

def render(game, cfg):
    st.header("⚖️ Phase 3: 年度結算與跨年物理演算")
    
    hp, rp = game.h_role_party, game.r_role_party
    ha = st.session_state[f"{hp.name}_acts"]
    ra = st.session_state[f"{rp.name}_acts"]
    
    # 1. 處理上年度跨年款項
    if game.pending_payouts['H'] > 0:
        hp.wealth += game.pending_payouts['H']
        rp.wealth += game.pending_payouts['R']
        rp.wealth += game.pending_payouts['R_residual']
        st.success(f"💰 [年初入帳] 執行系統獲得 H-Index 獎勵: {game.pending_payouts['H']:.0f} | 監管系統回收尾款與殘值: {(game.pending_payouts['R']+game.pending_payouts['R_residual']):.0f}")
    
    # 2. 扣除今年年金
    ab = game.budget_t * cfg['BASE_ANNUITY']
    ar = game.budget_t * cfg['RULING_ANNUITY']
    hp.wealth += ab + (ar if game.ruling_party.name == hp.name else 0)
    rp.wealth += ab + (ar if game.ruling_party.name == rp.name else 0)
    
    # 3. 物理與經濟結算
    c_funds = st.session_state.turn_data.get('c_funds', 0)
    d_cost = st.session_state.turn_data.get('d_cost', 0)
    
    # H 必須花費 D_cost 來建設，不足則產生懲罰
    actual_h_invest = min(hp.wealth, d_cost)
    hp.wealth -= actual_h_invest
    
    new_gdp, h_idx, c_net, l_gdp = formulas.calculate_economics_and_payouts(
        cfg, game.gdp, game.budget_t, c_funds, game.current_real_decay, actual_h_invest, hp.build_ability
    )
    
    st.info(f"🏗️ [建設結算] 投入資金: {actual_h_invest:.0f} | 實質產出: {c_net:.0f} | 阻力損耗: {l_gdp:.0f} | 最終 GDP: {game.gdp:.0f} ➔ {new_gdp:.0f}")
    st.info(f"📊 [政績結算] 本年度 H-Index 達標率: {h_idx:.2f}")
    
    # 準備明年的 Payouts
    game.pending_payouts['H'] = c_funds * h_idx
    game.pending_payouts['R'] = c_funds * max(0.0, (1.0 - h_idx))
    game.pending_payouts['R_residual'] = max(0.0, game.budget_t - c_funds)
    
    # 4. 支持度結算 (實作 Rule 8 嚴格公式)
    v_r = (new_gdp - game.gdp) / max(1.0, game.gdp)
    v_h = h_idx - 1.0 # >1.0 為正政績
    
    r_shift = formulas.calc_support_shift_v3(v_r, cfg['GDP_PERF_WEIGHT'], game.sanity, game.emotion, ra['media'], ha['media'], v_r > 0)
    h_shift = formulas.calc_support_shift_v3(v_h, cfg['H_INDEX_PERF_WEIGHT'], game.sanity, game.emotion, ha['media'], ra['media'], v_h > 0)
    
    # 純宣傳結算
    s_mult_camp = (1.0 - (game.sanity / 100.0))
    camp_shift = (ha['camp'] - ra['camp']) * s_mult_camp * 0.05
    
    total_h_shift = h_shift - r_shift + camp_shift
    hp.support = max(0.0, min(100.0, hp.support + total_h_shift))
    rp.support = 100.0 - hp.support
    
    # 5. 更新變數與換屆
    game.gdp = new_gdp
    game.budget_t = new_gdp * cfg['TAX_RATE']
    
    if st.button("進入下一年", type="primary", use_container_width=True):
        game.year += 1; game.phase = 1; game.p1_step = 'draft_r'
        game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
        for k in list(st.session_state.keys()):
            if k.endswith('_acts'): del st.session_state[k]
        del st.session_state.turn_initialized; st.rerun()
