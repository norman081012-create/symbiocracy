import streamlit as st
import random
import content, formulas, interface, manager

st.set_page_config(page_title="Symbiocracy v3.0.0", layout="wide")

if 'cfg' not in st.session_state: st.session_state.cfg = content.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = formulas.GameEngine(cfg)
    st.session_state.turn_data = {}

game = st.session_state.game

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        p.current_forecast = max(0.0, round(game.current_real_decay + random.uniform(-0.1, 0.1), 2))
    game.p1_step = 'draft_r'; game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A

# UI: 儀表板
with st.sidebar:
    interface.render_global_settings(cfg, game)
    if st.button("🔄 重新開始"): st.session_state.clear(); st.rerun()

interface.render_dashboard(game, view_party, cfg)
interface.render_message_board(game, game.phase)
interface.render_party_cards(game, view_party, False, (game.year % cfg['ELECTION_CYCLE'] == 1), cfg)

# --- Phase 1 Logic ---
if game.phase == 1:
    st.subheader(f"🤝 Phase 1: 預算標案協商 (輪數: {game.proposal_count})")
    
    if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_final']:
        if view_party.name != (game.r_role_party.name if 'r' in game.p1_step else game.h_role_party.name):
            st.warning("⏳ 等待對手擬定草案...")
        else:
            col_l, col_r = st.columns(2)
            with col_l:
                claimed_decay = st.number_input("公告衰退值", value=float(view_party.current_forecast), step=0.01)
                t_gdp_growth = st.number_input("目標 GDP 成長 (%)", value=0.0, step=0.5)
                max_h = max(10.0, float(game.total_budget))
                t_h_fund = st.slider("標案達標付款 (目標獎勵)", 0.0, max_h, float(min(game.h_fund, max_h)))
                r_val = st.slider("標案利潤 (嚴格度)", 0.5, 3.0, 1.0)
                
                req_funds, h_ratio = formulas.calculate_required_funds(cfg, t_h_fund, game.gdp*(1+t_gdp_growth/100), game.h_fund, game.gdp, r_val, claimed_decay, game.h_role_party.build_ability)
                r_pays = st.slider(f"監管系統出資 (總額: {req_funds})", 0, int(req_funds), int(req_funds*0.5))
                h_pays = req_funds - r_pays
                
                if st.button("📤 送出提案", use_container_width=True, type="primary"):
                    plan = {'r_value': r_val, 'target_h_fund': t_h_fund, 'target_gdp_growth': t_gdp_growth, 'total_funds': req_funds, 'r_pays': r_pays, 'h_pays': h_pays, 'h_ratio': h_ratio, 'claimed_decay': claimed_decay}
                    if game.p1_step == 'ultimatum_final':
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.h_role_party
                    else:
                        game.p1_proposals['R'] = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.h_role_party
                    st.rerun()

    elif game.p1_step == 'voting_confirm':
        interface.render_proposal_component("待覆議標案內容", game.p1_proposals['R'] if not game.p1_selected_plan else game.p1_selected_plan, game, view_party, cfg)
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("✅ 同意並執行"):
            st.session_state.turn_data.update(game.p1_proposals['R']); game.phase = 2; st.rerun()
        if c2.button("❌ 拒絕並重談"):
            game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()
        if c3.button("🔄 同意但換位"):
            fee = cfg['THIRD_PARTY_FEE']
            st.warning(f"⚠️ 警告：換位將使兩黨各支付 ${fee} 給公益團體。")
            if st.button("確認換位"):
                st.session_state.turn_data.update(game.p1_proposals['R'])
                game.party_A.wealth -= fee; game.party_B.wealth -= fee
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.phase = 2; st.rerun()
        if c4.button("💥 最後通牒"):
            game.p1_step = 'ultimatum_final'; game.proposing_party = game.r_role_party; st.rerun()

# --- Phase 2 Logic ---
elif game.phase == 2:
    st.subheader(f"🛠️ Phase 2: 行動階段 - {view_party.name}")
    d = st.session_state.turn_data
    is_h = (view_party.name == game.h_role_party.name)
    c1, c2 = st.columns(2)
    with c1:
        med = st.slider("媒體操控", 0, int(view_party.wealth), 100)
        inc = st.slider("煽動情緒", 0, int(view_party.wealth), 0)
        edu_up = st.slider("推行教育", 0, int(view_party.wealth), 0)
        edu_down = st.slider("推行降智", 0, int(view_party.wealth), 0)
        corr = st.slider("秘密貪污 (%)", 0, 100, 0) if is_h else 0
    with c2:
        up_inv = interface.ability_slider("調查能力", "inv", view_party.investigate_ability, view_party.wealth, cfg)
        up_pre = interface.ability_slider("預測能力", "pre", view_party.predict_ability, view_party.wealth, cfg)
        up_med = interface.ability_slider("媒體實力", "med", view_party.media_ability, view_party.wealth, cfg)
        
    if st.button("確認並結算", type="primary"):
        st.session_state[f"{view_party.name}_acts"] = {'media': med, 'incite': inc, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': corr, 'p_inv': up_inv, 'p_pre': up_pre, 'p_med': up_med}
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            manager.process_year_end(game, cfg, st.session_state[f"{game.r_role_party.name}_acts"], st.session_state[f"{game.h_role_party.name}_acts"], d)
            game.year += 1; game.phase = 1; del st.session_state.turn_initialized; st.rerun()
