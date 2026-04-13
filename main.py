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

st.set_page_config(page_title="Symbiocracy v3.1.0", layout="wide")

if 'cfg' not in st.session_state: st.session_state.cfg = config.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = engine.GameEngine(cfg)
    st.session_state.turn_data = {
        'r_value': 1.0, 'target_h_fund': 600.0, 'target_gdp_growth': 0.0,
        'r_pays': 0, 'total_funds': 0, 'agreed': False, 'target_gdp': 5000.0, 'h_ratio': 1.0
    }

game = st.session_state.game

if game.year > cfg['END_YEAR']:
    ui_core.render_endgame_charts(game.history, cfg)
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = cfg['PREDICT_DIFF'] / max(0.1, p.depts['predict'].eff)
        p.current_forecast = max(0.0, round(game.current_real_decay + random.uniform(-error_margin, error_margin), 2))
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A

with st.sidebar:
    ui_core.render_global_settings(cfg, game)
    god_mode = st.toggle("👁️ 上帝視角", False)

st.title("🏛️ Symbiocracy 共生民主模擬器 v3.1.0")

if game.phase == 1:
    ui_core.render_dashboard(game, view_party, cfg, is_preview=False)
    ui_core.render_party_cards(game, view_party, god_mode, False, cfg)
    phase1.render(game, view_party, cfg)
elif game.phase == 2:
    ui_core.render_party_cards(game, view_party, god_mode, False, cfg)
    phase2.render(game, view_party, opponent_party, cfg)
elif game.phase == 3:
    phase3.render(game, cfg)

ui_core.render_debug_panel(game, cfg)
