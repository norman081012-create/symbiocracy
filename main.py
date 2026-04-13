# ==========================================
# main.py
# ==========================================
import streamlit as st
import random
import config
import engine
import ui_core
import phase1
import phase2
import phase3

st.set_page_config(page_title="Symbiocracy v3.0.0", layout="wide")

if 'cfg' not in st.session_state:
    st.session_state.cfg = config.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = engine.GameEngine(cfg)
    st.session_state.turn_data = {}

game = st.session_state.game

if game.year > cfg['END_YEAR']:
    ui_core.render_endgame_charts(game.history, cfg)
    st.stop()

if 'turn_initialized' not in st.session_state:
    # 1. 真實衰退率與預測
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = 1.0 / max(0.1, p.depts['predict'].eff)
        p.current_forecast = max(0.0, round(game.current_real_decay + random.uniform(-error_margin, error_margin), 2))
    
    # 2. 年初預算編列與撥款 (年金與去年殘值/獎勵)
    total_tax = game.gdp * cfg['TAX_RATE']
    pb_amt = total_tax * cfg['P_B_RATE']
    pr_amt = total_tax * cfg['P_R_RATE']
    
    game.party_A.wealth += pb_amt + game.pending_payouts['A']
    game.party_B.wealth += pb_amt + game.pending_payouts['B']
    game.ruling_party.wealth += pr_amt
    
    game.pending_payouts = {'A': 0.0, 'B': 0.0} # 清空已發放
    game.current_budget_pool = total_tax - (pb_amt * 2) - pr_amt # 剩下的放入標案池
    
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A

with st.sidebar:
    ui_core.render_global_settings(cfg, game)
    ui_core.render_sidebar_intel_audit(game, view_party, cfg)
    god_mode = st.toggle("👁️ 上帝視角", False)
    if st.button("🔄 重新開始遊戲", use_container_width=True): 
        st.session_state.clear(); st.rerun()

st.title("🏛️ Symbiocracy 共生民主模擬器 v3.0.0 (遊戲年數:12)")
elec_status = config.get_election_icon(game.year, cfg['ELECTION_CYCLE'])
st.subheader(f"📅 {cfg['CALENDAR_NAME']} {game.year} 年 ({elec_status})")

if god_mode: 
    st.error(f"👁️ **上帝視角：** 真實衰退率為 **{game.current_real_decay:.2f}**")

is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

if game.phase == 1:
    ui_core.render_dashboard(game, view_party, cfg)
    ui_core.render_party_cards(game, view_party, god_mode, is_election_year, cfg)
    phase1.render(game, view_party, cfg)
elif game.phase == 2:
    ui_core.render_party_cards(game, view_party, god_mode, is_election_year, cfg)
    phase2.render(game, view_party, opponent_party, cfg)
elif game.phase == 3:
    phase3.render(game, cfg)

ui_core.render_debug_panel(game, cfg)
