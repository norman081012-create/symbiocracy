# ==========================================
# main.py
# 主程式：負責狀態轉移、UI 拼裝與即時數值分發
# ==========================================
import streamlit as st
import random
import content
import formulas
import interface

st.set_page_config(page_title="Symbiocracy 共生民主模擬器 v3.0.0", layout="wide")
st.components.v1.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)

if 'cfg' not in st.session_state: st.session_state.cfg = content.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = formulas.GameEngine(cfg)
    st.session_state.turn_data = {
        'r_value': 1.0, 'target_h_fund': 600.0, 'target_gdp_growth': 0.0,
        'r_pays': 0, 'total_funds': 0, 'agreed': False, 'target_gdp': 5000.0, 'h_ratio': 1.0
    }

game = st.session_state.game

if game.year > cfg['END_YEAR']:
    interface.render_endgame_charts(game.history, cfg)
    if st.button("🔄 重新開始全新遊戲", use_container_width=True): st.session_state.clear(); st.rerun()
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = cfg['PREDICT_DIFF'] / max(0.1, p.predict_ability)
        p.current_forecast = max(0.0, round(game.current_real_decay + random.uniform(-error_margin, error_margin), 2))
    
    if not hasattr(game, 'p1_step'):
        game.p1_step = 'draft_r'
        game.p1_proposals = {'R': None, 'H': None}
        game.p1_selected_plan = None

    for k in list(st.session_state.keys()):
        if k.startswith('ui_decay_') or k.endswith('_acts'): del st.session_state[k]
    
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

with st.sidebar:
    interface.render_global_settings(cfg, game)
    god_mode = st.toggle("👁️ 上帝視角", False)
    if st.button("🔄 重新開始遊戲", use_container_width=True): st.session_state.clear(); st.rerun()
    
    st.markdown("---")
    elec_status = "🗳️ 【大選年】" if is_election_year else f"⏳ 距大選 {cfg['ELECTION_CYCLE'] - (game.year % cfg['ELECTION_CYCLE'])} 年"
    st.write(f"**年份:** {game.year} / {cfg['END_YEAR']} ({elec_status})")
    if god_mode: st.error(f"👁️ **上帝視角：**\n真實衰退率為 **{game.current_real_decay:.2f}**")

st.title("🏛️ Symbiocracy 共生民主模擬器 v3.0.0")

acc_percent = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))

# 通知欄
if st.session_state.get('news_flash'): 
    st.info(st.session_state.news_flash); st.session_state.news_flash = None 

# Phase 2 不顯示智庫推估
interface.render_think_tank_toast(view_party, acc_percent, view_party.current_forecast, game.phase)

interface.render_party_cards(game, view_party, god_mode, is_election_year, cfg)
interface.render_status_bar(game, view_party, cfg)

def handle_trust_breakdown():
    penalty = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
    game.party_A.wealth -= penalty; game.party_B.wealth -= penalty
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True
    game.emotion = min(100.0, game.emotion + 30.0) 
    st.session_state.news_flash = f"🗞️ **【快訊】政局動盪！** 兩黨談判破裂觸發憲政危機，被迫換位！\n💸 雙方各遭強制捐款 {penalty} 資金給社福團體作為懲罰，社會情緒激憤！"
    game.phase = 2

if game.phase == 1:
    st.subheader(f"🤝 Phase 1: 目標與預算協商 (輪數: {game.proposal_count})")
    st.info(content.generate_phase1_flavor_text(game, view_party))
    
    if view_party.name == game.ruling_party.name and game.p1_step != 'ultimatum':
        c1, c2 = st.columns(2)
        if c1.button("🚨 1. 下達最後通牒", use_container_width=True, type="primary"):
            if game.p1_selected_plan: game.p1_step = 'ultimatum'; game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()
            else: st.error("⚠️ 需先完成一次表決！")
        if c2.button("⚡ 2. 強行通過調節者方案並換位", use_container_width=True, type="primary"):
            if game.p1_proposals.get('R'):
                st.session_state.turn_data.update(game.p1_proposals['R'])
                penalty = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
                game.party_A.wealth -= penalty; game.party_B.wealth -= penalty
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.swap_triggered_this_year = True
                game.emotion = min(100.0, game.emotion + 20.0)
                st.session_state.news_flash = f"🗞️ **【快訊】執政黨強行闖關！** 執政黨強行通過草案並啟動倒閣！\n💸 雙方遭社會唾棄，被罰捐 {penalty} 資金！"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            else: st.error("⚠️ 調節者尚未提案！")

    if game.p1_step in ['draft_r', 'draft_h']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H'
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手擬定草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({'調節者' if active_role == 'R' else '執行者'}黨) 草案擬定室")
            col_l, col_r = st.columns(2)
            with col_l:
                opp_role = 'H' if active_role == 'R' else 'R'
                opp_plan = game.p1_proposals.get(opp_role)
                opp_claimed = opp_plan['claimed_decay'] if opp_plan else None
                
                my_plan = game.p1_proposals.get(active_role)
                my_last_claimed = my_plan['claimed_decay'] if my_plan else view_party.current_forecast
                
                c_decay, c_gdp = st.columns(2)
                input_key = f"ui_decay_val_{game.year}_{active_role}"
                if input_key not in st.session_state: 
                    # 預設帶入智庫值，確保平均按鈕能吃到自己的預測值
                    st.session_state[input_key] = float(view_party.current_forecast)
                
                with c_decay:
                    st.markdown(f"**公告衰退值** *(當前: {my_last_claimed:.2f})*")
                    if opp_claimed is not None:
                        st.caption(f"對手公告: {opp_claimed:.2f}")
                    
                    claimed_decay = st.number_input("公告衰退值", value=float(st.session_state[input_key]), step=0.01, key=f"num_{input_key}", label_visibility="collapsed")
                    
                    if opp_claimed is not None:
                        b1, b2, b3 = st.columns(3)
                        my_fc = view_party.current_forecast
                        b1.button("平均", on_click=lambda: st.session_state.update({input_key: round((my_fc + opp_claimed)/2, 2)}))
                        b2.button("偏我", on_click=lambda: st.session_state.update({input_key: round(my_fc*0.75 + opp_claimed*0.25, 2)}))
                        b3.button("偏他", on_click=lambda: st.session_state.update({input_key: round(my_fc*0.25 + opp_claimed*0.75, 2)}))
                    st.session_state[input_key] = claimed_decay
                    
                with c_gdp:
                    st.markdown("**目標 GDP 成長率 (%)**")
                    t_gdp_growth = st.number_input("GDP成長", value=0.0, step=0.5, label_visibility="collapsed")

                max_h = max(10.0, float(game.total_budget))
                t_h_fund = st.slider("目標執行獎勵基金 (最高不超過當年總預算)", 0.0, max_h, float(min(game.h_fund, max_h)), 10.0)
                r_val = st.slider("績效達成嚴格度 (平方級影響)", 0.5, 3.0, 1.0, 0.1)
                
                t_gdp = game.gdp * (1 + (t_gdp_growth / 100.0))
                req_funds, h_ratio = formulas.calculate_required_funds(cfg, t_h_fund, t_gdp, game.h_fund, game.gdp, r_val, claimed_decay, game.h_role_party.build_ability)
                
                safe_req = max(1, int(req_funds))
                
                col_pays1, col_pays2 = st.columns(2)
                with col_pays1:
                    r_pays = st.slider(f"💰 調節者出資 (總需 {req_funds})", 0, safe_req, int(safe_req * 0.5))
                with col_pays2:
                    h_pays = req_funds - r_pays
                    st.markdown(f"**執行者出資:**\n\n`{h_pays}`")
                
                o_gdp_pct, o_h_g, o_h_n, o_r_g, o_r_n, o_h_sup, o_r_sup, o_est_gdp, o_est_h_fund, o_h_roi, o_r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, view_party.current_forecast, game.h_role
