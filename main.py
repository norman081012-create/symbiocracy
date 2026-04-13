# ==========================================
# main.py
# 主程式入口
# ==========================================
import streamlit as st
import random
import config
import engine
import ui_core
import phase1
import phase2

st.set_page_config(page_title="Symbiocracy v3.0.0", layout="wide")
st.components.v1.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)

if 'lang' not in st.session_state: st.session_state.lang = 'EN'
def t(en, zh): return zh if st.session_state.lang == 'ZH' else en

if 'cfg' not in st.session_state: st.session_state.cfg = config.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = engine.GameEngine(cfg)
    st.session_state.turn_data = {
        'r_value': 1.0, 'target_h_fund': 600.0, 'target_gdp_growth': 0.0,
        'r_pays': 0, 'total_funds': 0, 'agreed': False, 'target_gdp': 5000.0, 'h_ratio': 1.0
    }

game = st.session_state.game

if st.session_state.get('anim') == 'balloons': st.balloons(); st.session_state.anim = None
elif st.session_state.get('anim') == 'snow': st.snow(); st.session_state.anim = None

if game.year > cfg['END_YEAR']:
    ui_core.render_endgame_charts(game.history, cfg)
    if st.button(t("🔄 Restart Game", "🔄 重新開始全新遊戲"), use_container_width=True): st.session_state.clear(); st.rerun()
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = cfg['PREDICT_DIFF'] / max(0.1, p.predict_ability)
        p.current_forecast = max(0.0, round(game.current_real_decay + random.uniform(-error_margin, error_margin), 2))
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

with st.sidebar:
    ui_core.render_global_settings(cfg, game)
    ui_core.render_sidebar_intel_audit(game, view_party, cfg)
    god_mode = st.toggle(t("👁️ God Mode", "👁️ 上帝視視角"), False)
    if st.button(t("🔄 Restart", "🔄 重新開始遊戲"), use_container_width=True): st.session_state.clear(); st.rerun()

st.title(t("🏛️ Symbiocracy Simulation v3.0.0", "🏛️ Symbiocracy 共生民主模擬器 v3.0.0"))
elec_status = config.get_election_icon(game.year, cfg['ELECTION_CYCLE'])
st.subheader(f"📅 {cfg['CALENDAR_NAME']} Year {game.year} ({elec_status})")

if god_mode: st.error(t(f"👁️ God Mode: Real Decay is {game.current_real_decay:.2f}", f"👁️ 上帝視角： 真實衰退率為 {game.current_real_decay:.2f}"))

if game.phase == 1: ui_core.render_dashboard(game, view_party, cfg, is_preview=False)
ui_core.render_message_board(game)
ui_core.render_party_cards(game, view_party, god_mode, is_election_year, cfg)

if game.phase == 1: phase1.render(game, view_party, cfg)
elif game.phase == 2: phase2.render(game, view_party, opponent_party, cfg)
