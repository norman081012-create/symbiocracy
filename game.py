# --- ACTION BUTTONS ---
def commit_turn():
    if cost_A > game.A_wealth or cost_B > game.B_wealth:
        st.session_state.error_msg = "Error: Over Budget"
        return
    st.session_state.error_msg = ""
    game.R_value = st.session_state.r_val if st.session_state.r_val != 0 else 0.000001
    
    if st.session_state.do_swap and game.swap_available:
        game.current_H_party, game.current_R_party = game.current_R_party, game.current_H_party
        game.swap_available = False
        game.events.append({'year': game.year, 'type': 'Swap'})

    inputs = {
        'A': {'edu': st.session_state.in_a_edu if sim_R == "A" else 0, 'anti': st.session_state.in_a_anti if sim_R == "A" else 0, 'brain': st.session_state.in_a_brain, 'cons': st.session_state.in_a_cons},
        'B': {'edu': st.session_state.in_b_edu if sim_R == "B" else 0, 'anti': st.session_state.in_b_anti if sim_R == "B" else 0, 'brain': st.session_state.in_b_brain, 'cons': st.session_state.in_b_cons}
    }
    game.process_year(inputs)
    
    # Reset inputs for next year
    st.session_state.in_a_edu = st.session_state.in_a_anti = st.session_state.in_a_brain = st.session_state.in_a_cons = 0.0
    st.session_state.in_b_edu = st.session_state.in_b_anti = st.session_state.in_b_brain = st.session_state.in_b_cons = 0.0
    st.session_state.do_swap = False
    st.session_state.turn_phase = 0

# --- Turn-Based Phase Control ---
if not is_hvh:
    # PvE Mode (Human vs Bot or Bot vs Bot) -> Skip phases, just one button
    if st.button(t('confirm_btn'), type="primary", use_container_width=True):
        commit_turn()
        st.rerun()
else:
    # PvP Mode (Human vs Human) -> 3-Phase Proposal System
    c1, c2 = st.columns(2)
    if st.session_state.turn_phase == 0:
        if c2.button(t('btn_submit_prop'), type="primary", use_container_width=True):
            st.session_state.turn_phase = 1
            st.rerun()
    elif st.session_state.turn_phase == 1:
        if c2.button(t('btn_submit_react'), type="primary", use_container_width=True):
            st.session_state.turn_phase = 2
            st.rerun()
    elif st.session_state.turn_phase == 2:
        if c1.button(t('btn_revise'), use_container_width=True):
            st.session_state.turn_phase = 0
            st.rerun()
        if c2.button(t('confirm_btn'), type="primary", use_container_width=True):
            commit_turn()
            st.rerun()
