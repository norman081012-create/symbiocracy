# main.py
import streamlit as st
import random
import config
import engine
import ui_core
import phase1
import phase2
import phase3 # 新增

st.set_page_config(page_title="Symbiocracy 共生民主模擬器 v3.0.0", layout="wide")
st.components.v1.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)

if 'cfg' not in st.session_state: st.session_state.cfg = config.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = engine.GameEngine(cfg)
    st.session_state.turn_data = {}

game = st.session_state.game

# --- 處理標題 Rule 2 ---
st.title(f"🏛️ Symbiocracy 共生民主模擬器 v3.0.0 (遊戲年數:{cfg['END_YEAR']})")
elec_status = config.get_election_icon(game.year, cfg['ELECTION_CYCLE'])
st.subheader(f"📅 {cfg['CALENDAR_NAME']} {game.year} 年 ({elec_status})")

# ... 略過初始化邏輯 (同你原本的 main.py) ...

# 階段路由
if game.phase == 1:
    phase1.render(game, view_party, cfg)
elif game.phase == 2:
    phase2.render(game, view_party, opponent_party, cfg)
elif game.phase == 3:
    phase3.render(game, cfg)
