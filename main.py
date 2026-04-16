# ==========================================
# main.py
# ==========================================
import ui_formulas
import streamlit as st
import random
import config
import engine
import ui_core
import ui_proposal 
import phase1
import phase2
import phase3
import phase4
import i18n
import ai_bot  # 📌 引入全新的 AI 神經中樞

st.set_page_config(page_title="Symbiocracy Simulator v3.0.0", layout="wide")
st.components.v1.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)

if 'lang' not in st.session_state: st.session_state.lang = 'EN'
t = i18n.t

if 'cfg' not in st.session_state: st.session_state.cfg = config.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = engine.GameEngine(cfg)
    st.session_state.turn_data = {
        'r_value': 1.0, 'target_h_fund': 600.0, 'target_gdp_growth': 0.0,
        'r_pays': 0, 'total_funds': 0, 'agreed': False, 'target_gdp': 5000.0, 'h_ratio': 1.0
    }

game = st.session_state.game

if st.session_state.get('anim') == 'balloons':
    st.balloons()
    st.session_state.anim = None
elif st.session_state.get('anim') == 'snow':
    st.snow()
    st.session_state.anim = None

if game.phase == 4:
    phase4.render(game, cfg)
    st.stop()

# ==========================================
# PHASE 0: 遊戲初始設定
# ==========================================
if game.phase == 0:
    st.title("🏛️ Symbiocracy Simulator - Game Setup")
    st.markdown("---")
    
    st.markdown("### Choose Game Mode")
    mode = st.radio("Select how you want to play:", ["PvE (Single Player vs AI)", "PvP (Local 2 Players)"], label_visibility="collapsed")
    
    human_party = None
    if mode == "PvE (Single Player vs AI)":
        st.markdown("### Choose Your Party")
        human_party = st.radio("Select your faction:", [f"{cfg['PARTY_A_NAME']} (Prosperity)", f"{cfg['PARTY_B_NAME']} (Equity)"], label_visibility="collapsed")
        # 清除附帶的說明文字，抓取純黨名
        human_party = human_party.split(" (")[0]
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Start Simulation 🚀", type="primary"):
        game.phase = 1
        if mode == "PvE (Single Player vs AI)":
            game.is_pve = True
            game.human_party_name = human_party
            game.ai_party_name = cfg['PARTY_B_NAME'] if human_party == cfg['PARTY_A_NAME'] else cfg['PARTY_A_NAME']
        else:
            game.is_pve = False
        st.rerun()
    st.stop()  # 阻擋渲染，直到玩家按下開始

# ==========================================
# AI 自動攔截系統
# ==========================================
if getattr(game, 'is_pve', False) and game.phase in [1, 2] and game.proposing_party.name == game.ai_party_name:
    st.title("🏛️ Symbiocracy Simulator v3.0.0")
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.spinner(f"🤖 **{game.ai_party_name}** is formulating strategies and taking actions..."):
        import time
        time.sleep(0.8) # 稍微延遲 0.8 秒，讓玩家有對方在操作的代入感
        ai_bot.take_turn(game, cfg)
        st.rerun()
# ==========================================

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 3))
    real_infra_loss = game.gdp * (game.current_real_decay * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE'])
    
    for p in [game.party_A, game.party_B]:
        p_acc_weight = cfg.get('PREDICT_ACCURACY_WEIGHT', 0.8)
        error_margin_pct = 1.0 - ((p.predict_ability / 10.0) * p_acc_weight)
        error_range = real_infra_loss * error_margin_pct
        observed_loss = max(0.0, real_infra_loss + random.uniform(-error_range, error_range))
        
        p.current_forecast = max(0.0, round(((observed_loss / max(1.0, game.gdp)) - cfg['BASE_DECAY_RATE']) / cfg['DECAY_WEIGHT_MULT'], 3))
        p.poll_history = {'Small': [], 'Medium': [], 'Large': []}
        p.latest_poll = None
        p.poll_count = 0 
    
    if not hasattr(game, 'p1_step'):
        game.p1_step = 'draft_r'
        game.p1_proposals = {'R': None, 'H': None}
        game.p1_selected_plan = None

    for k in list(st.session_state.keys()):
        if k.startswith('ui_decay_') or k.endswith('_acts'): del st.session_state[k]
    
    st.session_state.turn_initialized = True
    
    if game.year == 1:
        st.session_state.news_flash = f"🎉 **[FOUNDING ELECTION]** Simulation Commenced! {game.ruling_party.name} secures the first term."

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

with st.sidebar:
    ui_core.render_global_settings(cfg, game)
    ui_core.render_sidebar_intel_audit(game, view_party, cfg)
    god_mode = st.toggle(t("👁️ God Mode"), False)
    st.session_state.god_mode = god_mode 
    if st.button(t("🔄 Restart Game"), use_container_width=True): st.session_state.clear(); st.rerun()

st.title(t("🏛️ Symbiocracy Simulator v3.0.0"))

elec_status = config.get_election_icon(game.year, cfg['ELECTION_CYCLE'])
st.subheader(t(f"📅 {cfg['CALENDAR_NAME']} Year {game.year} ({elec_status})"))

if god_mode:
    real_loss = game.gdp * (game.current_real_decay * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE'])
    st.error(t(f"👁️ **GOD MODE:** True Decay is **{game.current_real_decay:.3f}** (EV Loss: {real_loss:.1f})"))

if game.phase == 1 or game.phase == 2:
    if game.phase == 1: ui_core.render_dashboard(game, view_party, cfg, is_preview=False)
    ui_core.render_party_cards(game, view_party, god_mode, is_election_year, cfg)
    ui_core.render_message_board(game)

if game.phase == 1: phase1.render(game, view_party, cfg)
elif game.phase == 2: phase2.render(game, view_party, opponent_party, cfg)
elif game.phase == 3: phase3.render(game, cfg)

if game.phase != 4: ui_formulas.render_formula_panel(game, view_party, cfg)
