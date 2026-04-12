# ==========================================
# main.py
# 主程式：負責狀態轉移、UI 拼裝與即時數值分發
# ==========================================
import streamlit as st
import random

st.set_page_config(page_title="Symbiocracy Simulator v3.0.0", layout="wide")

import content
import formulas
import interface

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
    if st.button("🔄 重新開始全新遊戲", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = cfg['PREDICT_DIFF'] / max(0.1, p.predict_ability)
        forecast = game.current_real_decay + random.uniform(-error_margin, error_margin)
        p.current_forecast = max(0.0, round(forecast, 2))
    game.proposal_count = 0
    game.p1_state = 'drafting'
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

with st.sidebar:
    interface.render_global_settings(cfg)
    god_mode = st.toggle("👁️ 上帝視角", False)
    if st.button("🔄 重新開始遊戲", use_container_width=True): st.session_state.clear(); st.rerun()
    
    st.markdown("---")
    elec_status = "🗳️ 【大選年】" if is_election_year else f"⏳ 距大選 {cfg['ELECTION_CYCLE'] - (game.year % cfg['ELECTION_CYCLE'])} 年"
    st.write(f"**年份:** {game.year} / {cfg['END_YEAR']} ({elec_status})")
    if god_mode: st.error(f"👁️ **上帝視角：**\n真實衰退率為 **{game.current_real_decay:.2f}**")

st.title("🏛️ Symbiocracy 共生民主模擬器 v3.0.0")

# 頂部戰報 Banner
interface.render_yearly_review_banner(game)
if st.session_state.get('news_flash'): 
    st.info(st.session_state.news_flash); st.session_state.news_flash = None 

interface.render_party_cards(game, view_party, god_mode, is_election_year, cfg)
interface.render_status_bar(game, view_party, cfg)

rt_req_funds=0; rt_h_ratio=1.0; rt_r_pays=0; rt_h_pays=0; rt_r_val=1.0; rt_t_h=600; rt_t_gdp=5000; rt_net_inc=0; rt_opp_inc=0; rt_my_sup=0; rt_opp_sup=0

def handle_trust_breakdown():
    game.party_A.wealth -= 100.0; game.party_B.wealth -= 100.0
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True
    st.session_state.news_flash = "🚨 **談判破裂！** 觸發換位，雙方各扣 100 資金！"
    game.phase = 2

if not hasattr(game, 'p1_proposals'):
    game.p1_proposals = {'R': None, 'H': None, 'Neutral': None}
    game.p1_selected_plan = None; game.p1_step = 'draft_r' 

if game.phase == 1:
    st.subheader(f"🤝 Phase 1: 目標與預算協商 (輪數: {game.proposal_count})")
    
    if view_party.name == game.ruling_party.name and game.p1_step != 'ultimatum':
        c1, c2 = st.columns(2)
        if c1.button("🚨 1. 下達最後通牒", use_container_width=True, type="primary"):
            if game.p1_selected_plan: game.p1_step = 'ultimatum'; game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()
            else: st.error("⚠️ 需先完成一次表決！")
        if c2.button("⚡ 2. 強行通過調節者方案並換位", use_container_width=True, type="primary"):
            if game.p1_proposals.get('R'):
                st.session_state.turn_data.update(game.p1_proposals['R'])
                game.party_A.wealth -= 50; game.party_B.wealth -= 50
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            else: st.error("⚠️ R 黨尚未提案！")

    if game.p1_step in ['draft_r', 'draft_h']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H'
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手擬定草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({active_role} 黨) 草案擬定室")
            col_l, col_r = st.columns(2)
            with col_l:
                strategy = st.radio("🤖 策略", ["自訂", "🤝 友善", "⚖️ 公平", "🔥 極限"], horizontal=True)
                r_ratio = 0.5; def_r = 1.0
                if strategy == "🤝 友善": r_ratio = 0.7 if active_role == 'R' else 0.3; def_r = 0.8 if active_role == 'R' else 1.2
                elif strategy == "🔥 極限": r_ratio = 0.3 if active_role == 'R' else 0.7; def_r = 1.8 if active_role == 'R' else 0.5
                
                claimed_decay = st.number_input("公告預估衰退值 (高估可索更多預算)", value=float(view_party.current_forecast), step=0.05)
                max_h = max(10.0, float(game.total_budget))
                t_h_fund = st.slider("目標執行獎勵基金 (外包業務量)", 0.0, max_h, float(min(game.h_fund, max_h)), 10.0)
                t_gdp_growth = st.slider("目標 GDP 成長率 (%)", -5.0, 15.0, 0.0, 0.5)
                r_val = st.slider("績效達成嚴格度 (平方級影響)", 0.5, 3.0, float(def_r), 0.1)
                
                t_gdp = game.gdp * (1 + (t_gdp_growth / 100.0))
                req_funds, h_ratio = formulas.calculate_
