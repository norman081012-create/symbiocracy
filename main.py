import streamlit as st
import random
import math

st.set_page_config(page_title="Symbiocracy Simulator v2.9", layout="wide")

# 引入重構後的模組
import content
import formulas
import interface

# ==========================================
# 初始化區 (Session State)
# ==========================================
if 'cfg' not in st.session_state:
    st.session_state.cfg = content.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = formulas.GameEngine(cfg)
    st.session_state.turn_data = {
        'r_value': 1.0, 'target_h_fund': 600.0, 'target_gdp_growth': 0.0,
        'r_pay_ratio': 50, 'total_funds': 0, 'agreed': False,
        'target_gdp': 5000.0, 'h_ratio': 1.0
    }
    st.session_state.news_flash = "🗞️ **首長就職：** 歡迎來到共生內閣的第一年！請雙方展開預算與目標協商。"

game = st.session_state.game

# ==========================================
# 終局判定與圖表生成
# ==========================================
if game.year > cfg['END_YEAR']:
    interface.render_endgame_charts(game.history, cfg)
    st.stop() # 停止渲染後續的遊戲畫面

# ==========================================
# 年度初始化邏輯
# ==========================================
if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = cfg['PREDICT_DIFF'] / max(0.1, p.predict_ability)
        forecast = game.current_real_decay + random.uniform(-error_margin, error_margin)
        p.current_forecast = max(0.0, round(forecast, 2))
    
    game.proposal_count = 0
    game.p1_state = 'drafting'
    st.session_state.turn_data['agreed'] = False
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
god_mode = st.sidebar.toggle("👁️ 上帝視角 (God Mode)", False)

# ==========================================
# 側邊欄與 UI 渲染
# ==========================================
# 1. 渲染動態變數選單
interface.render_global_settings(cfg)

if st.sidebar.button("🔄 重新開始遊戲", use_container_width=True):
    st.session_state.clear()
    st.rerun()

is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

# 2. 共用狀態列與首頁資訊 (將原碼直接放此或封裝)
st.title("🏛️ Symbiocracy 共生民主模擬器 v2.9")
if st.session_state.news_flash: 
    st.info(st.session_state.news_flash)
    st.session_state.news_flash = None 

# ==========================================
# 遊戲流程控制
# ==========================================
def handle_trust_breakdown():
    penalty_funds = 100.0
    game.party_A.wealth -= penalty_funds
    game.party_B.wealth -= penalty_funds
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True # 紀錄事件供畫圖
    st.session_state.news_flash = f"🚨 **談判破裂！** 觸發憲政危機並強制換位！📉 雙方各扣 {penalty_funds:.0f} 資金！"
    game.phase = 2

if game.phase == 1:
    # 這裡放入你原本 Phase 1 的所有 st.columns / 提案按鈕判斷邏輯
    # (為了精簡回答篇幅，請將原本 Phase 1 的邏輯區塊貼至此處，並確保計算時呼叫 formulas.py 內的函數)
    # 例如：req_funds, h_ratio = formulas.calculate_required_funds(cfg, t_h_fund, t_gdp, ...)
    st.info("請於此貼上 Phase 1 的 UI 控制代碼。")
    if st.button("臨時按鈕: 假裝完成提案進入 Phase 2 (測試用)"):
        game.phase = 2
        st.rerun()

elif game.phase == 2:
    # 這裡放入你原本 Phase 2 行動面板與結算的邏輯
    st.info("請於此貼上 Phase 2 的 UI 控制代碼。")
    if st.button("結算本年度 (測試用)"):
        # 結算完畢後觸發歷史紀錄並前進
        game.record_history(is_election=is_election_year)
        game.year += 1
        del st.session_state.turn_initialized
        st.rerun()
