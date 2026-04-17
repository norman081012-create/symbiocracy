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
import ai_bot 

st.set_page_config(page_title="Symbiocracy Simulator v4.0.0", layout="wide")
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
# PHASE 0: 遊戲初始設定與官方百科
# ==========================================
if game.phase == 0:
    st.title(t("🏛️ Symbiocracy Simulator - Game Setup"))
    
    st.markdown("""
    <div style='background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid #FF4B4B; margin-bottom: 20px;'>
    <h2 style='color:#FFFFFF; margin-top: 0;'>🏛️ Symbiocracy: Official Survival Guide & Codex</h2>
    <p style='color:#CCCCCC;'><em>"Do not trust the promises of politicians; trust the checks and balances of the system." — Star Era Founding Charter</em></p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🌍 Prologue: Worldview & Power Asymmetry", expanded=True):
        st.markdown("""
        **Year 2077. World War III has reduced the old global order to ashes.**
        From the radioactive ruins, the nation of **Star Era** emerges as the first state to adopt a revolutionary governance system: **Symbiocracy**. To eradicate the absolute power and corruption that destroyed the old world, the state apparatus is forcefully split into two interdependent yet opposing cores. 
        
        Every 4 years, the election decides the **Ruling Party**, which is locked into the Regulator role. The opposition becomes the Executive. Each role monopolizes specific resources with a **1.2x output dominance**:
        
        * ⚖️ **Regulator (Client)**: The Ruling Party. 
            * **Power**: Controls the national budget and drafts reconstruction contracts. 
            * **Dominance**: Controls the top of the state apparatus, enjoying a **1.2x multiplier to Intel & Ops** and **PR & Media**.
            * **Limit**: Strictly forbidden from interfering with physical construction.
        * 🛡️ **Executive (Contractor)**: The Opposition Party.
            * **Power**: Fully responsible for physical construction and monopolizes the **National Education Policy (Edu Shift)**.
            * **Dominance**: Ground-level operations grant a **1.2x multiplier to Engineering** and **Think Tank (EP)**.
            * **Limit**: No budget allocation power; must earn party funds by accepting contracts.
            
        *(Note: If contract negotiations break down, immense penalties are paid, triggering a **Cabinet Swap**, instantly reversing the roles!)*
        """)

    with st.expander("🧠 Chapter 1: Society, Sanity & Brainwashing"):
        st.markdown("""
        Voters are not perfectly rational. Winning elections requires manipulating the cognitive foundation of society:
        
        * 📚 **Edu Shift (Education Policy)**: *Exclusive to Executive.* Invest Media Power to shift education. Moving Left (**Rote/Obedience**) strips independent thought. Moving Right (**Critical Thinking**) builds a strong civic society.
        * 🔥 **Voter Emotion**: Rises with national turmoil and targeted **Incite** operations. High emotion blinds voters and negates civic sanity.
        * ⚖️ **Sanity Accuracy**: The ultimate metric `(Sanity - Emotion/2)`.
            * **High Accuracy**: Voter **Performance Armor becomes thin** (real deeds easily win votes), while **Spin Armor becomes thick** (highly immune to media propaganda).
            * **Low Accuracy**: Voters ignore objective facts (performance is nullified) and blindly follow media brainwashing (Spin).
        """)

    with st.expander("⚙️ Chapter 2: Underground Ops & Resources"):
        st.markdown("""
        Beyond the budget, your 5 departments generate three types of underground resources:
        
        1. **EP (Evaluation Points)** - *From Think Tank*: Your brain.
            * `Observe Decay/Proj`: Accurately predict economic crashes or **see through the opponent's project conversions** (counters Hide Org).
            * `Optimize Proj`: Invest in the future to increase the base multipliers of projects generated next year.
        2. **Ops (Operations)** - *From Intel & Ops Div.*: Your hidden hand.
            * `Censorship / Anti-Censor`: Censor opponent media to forcibly strip their voters' "Spin Armor," allowing your propaganda to penetrate.
            * `Audit / Hide Org`: Hide your organization to artificially inflate your project's perceived efficiency to the opponent.
            * `Trace / Hide Finances`: Hunt down Fake EV or launder your embezzled funds.
        3. **Pwr (Power)** - *From PR & Media Div.*: Your megaphone.
            * `Campaign`: Generate positive spin.
            * `Incite`: Whip voters into an emotional frenzy.
            * `Control`: Defend against opponent spin.
            * `Edu Shift`: Brainwash the next generation (Executive only).
        """)

    with st.expander("🏗️ Chapter 3: Contracts, Corruption & Failing Projects"):
        st.markdown("""
        * **Real EV**: Legitimate construction that converts to GDP and Performance.
        * **Fake EV**: Shoddy construction that costs only 20% of Real EV. Used by the Executive to embezzle contract funds.
            * **The Price of Corruption**: If caught by Intel, face massive fines and confiscation.
            * **Permanent Dilution**: Even if uncaught, Fake EV **permanently dilutes** the project's Performance and GDP multipliers upon completion `(Real + 0.2*Fake / Total EV)`. Shoddy work buys no legacy!
        * **Min Req (Minimum Requirement)**: Large projects span multiple years. You must invest at least **20% of the remaining EV annually**. Failing to meet this threshold will cause the project to **Fail (abandoned)**, wasting all prior investments.
        """)

    with st.expander("🏆 Chapter 4: The Trifecta of Performance & Elections"):
        st.markdown("""
        Performance is strictly divided. **All performance faces a 6-Year Linear Depreciation**—you cannot rest on past laurels:
        
        1. 🏛️ **Ruling Perf.**: Belongs to the Ruling Party. Gained from the gap between Real GDP growth and the Think Tank's Claimed Decay. 
        2. 📜 **Prop Perf. (Proposal Perf.)**: Belongs to the **Contract Author**. Earned from the completed project's actual GDP contribution. Write good contracts!
        3. 🛡️ **Exec Perf. (Execution Perf.)**: Belongs to the Executive. Earned upon 100% completion based on EV invested × Exec Multiplier.
        
        **🗳️ Electoral Conquest (The Shift)**
        At the end of the year, the system calculates the **Net Performance** and **Net Spin** between the two parties, launching an assault on the swing voters:
        * **Net Perf** crashes against the voters' *Performance Armor*.
        * **Net Spin** crashes against the voters' *Spin Armor*.
        Every layer of armor pierced shifts the electoral boundary in your favor. In Star Era, truth and lies only matter if they convert into votes.
        """)

    st.markdown("---")
    st.markdown(t("### Choose Game Mode"))
    mode = st.radio("Select how you want to play:", ["PvE (Single Player vs AI)", "PvP (Local 2 Players)"], label_visibility="collapsed")
    
    human_party = None
    if mode == "PvE (Single Player vs AI)":
        st.markdown(t("### Choose Your Party"))
        human_party = st.radio("Select your faction:", [f"{cfg['PARTY_A_NAME']} (Prosperity)", f"{cfg['PARTY_B_NAME']} (Equity)"], label_visibility="collapsed")
        human_party = human_party.split(" (")[0]
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(t("Start Simulation 🚀"), type="primary"):
        game.phase = 1
        if mode == "PvE (Single Player vs AI)":
            game.is_pve = True
            game.human_party_name = human_party
            game.ai_party_name = cfg['PARTY_B_NAME'] if human_party == cfg['PARTY_A_NAME'] else cfg['PARTY_A_NAME']
        else:
            game.is_pve = False
        st.rerun()
    st.stop()

# ==========================================
# AI 自動攔截系統
# ==========================================
if getattr(game, 'is_pve', False) and game.phase in [1, 2] and game.proposing_party.name == game.ai_party_name:
    st.title("🏛️ Symbiocracy Simulator v4.0.0")
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.spinner(f"🤖 **{game.ai_party_name}** is evaluating projects and taking actions..."):
        import time
        time.sleep(0.8)
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
        
        p.projects = engine.generate_projects(p.predict_ability, p.name)
    
    if not hasattr(game, 'p1_step'):
        game.p1_step = 'draft_r'
        game.p1_proposals = {'R': None, 'H': None}
        game.p1_selected_plan = None

    for k in list(st.session_state.keys()):
        if k.startswith('ui_decay_') or k.endswith('_acts'): del st.session_state[k]
    
    st.session_state.turn_initialized = True
    
    if game.year == 1:
        st.session_state.news_flash = t(f"🎉 **[FOUNDING ELECTION]** Simulation Commenced! {game.ruling_party.name} secures the first term.")

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

with st.sidebar:
    ui_core.render_global_settings(cfg, game)
    ui_core.render_sidebar_intel_audit(game, view_party, cfg)
    god_mode = st.toggle(t("👁️ God Mode"), False)
    st.session_state.god_mode = god_mode 
    if st.button(t("🔄 Restart Game"), use_container_width=True): st.session_state.clear(); st.rerun()

st.title("🏛️ Symbiocracy Simulator v4.0.0")

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
