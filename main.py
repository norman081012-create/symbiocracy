# ==========================================
# main.py
# 主程式入口：負責路由、全局初始化與整合
# ==========================================
import streamlit as st
import random
import config
import engine
import ui_core
import phase1
import phase2
import phase3  # 記得引入全新的 Phase 3

st.set_page_config(page_title="Symbiocracy 共生民主模擬器 v3.0.0", layout="wide")
st.components.v1.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)

if 'cfg' not in st.session_state: st.session_state.cfg = config.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = engine.GameEngine(cfg)
    st.session_state.turn_data = {}

game = st.session_state.game

# 動畫處理
if st.session_state.get('anim') == 'balloons':
    st.balloons()
    st.session_state.anim = None
elif st.session_state.get('anim') == 'snow':
    st.snow()
    st.session_state.anim = None

if game.year > cfg['END_YEAR']:
    # 如果有實作 endgame_charts 可以呼叫，這裡給予重置按鈕
    if st.button("🔄 重新開始全新遊戲", use_container_width=True): st.session_state.clear(); st.rerun()
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        # 🐛 修正：不再依賴舊的 PREDICT_DIFF，改用 V3.1 的 0~100 能力值動態計算誤差
        # 當能力為預設 20 時，誤差為 ±0.5；當能力升級到 100 時，誤差縮小到 ±0.1
        error_margin = 10.0 / max(1.0, p.predict_ability)
        p.current_forecast = max(0.0, round(game.current_real_decay + random.uniform(-error_margin, error_margin), 2))
    st.session_state.turn_initialized = True

# ==========================================
# 解決 NameError 的關鍵：定義全域視角變數
# ==========================================
view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

# 左側邊欄
with st.sidebar:
    ui_core.render_global_settings(cfg, game)
    god_mode = st.toggle("👁️ 上帝視角", False)
    if st.button("🔄 重新開始遊戲", use_container_width=True): st.session_state.clear(); st.rerun()

# 標題與年份
st.title(f"🏛️ Symbiocracy 共生民主模擬器 v3.0.0 (遊戲年數:{cfg['END_YEAR']})")
elec_status = config.get_election_icon(game.year, cfg['ELECTION_CYCLE'])
st.subheader(f"📅 {cfg['CALENDAR_NAME']} {game.year} 年 ({elec_status})")

if god_mode: st.error(f"👁️ **上帝視角：** 真實衰退率為 **{game.current_real_decay:.2f}**")

# 渲染玩家卡片
ui_core.render_party_cards(game, view_party, god_mode, is_election_year, cfg)

# ==========================================
# 階段路由
# ==========================================
if game.phase == 1:
    phase1.render(game, view_party, cfg)
elif game.phase == 2:
    phase2.render(game, view_party, opponent_party, cfg)
elif game.phase == 3:
    phase3.render(game, cfg)
