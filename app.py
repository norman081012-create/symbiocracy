import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from game_engine import SymbiocracyGame
from i18n import t

st.set_page_config(page_title="Symbiocracy Simulator", layout="wide")

if 'game' not in st.session_state:
    st.session_state.game = SymbiocracyGame()
    st.session_state.lang = "English"
    st.session_state.turn_phase = 0
    st.session_state.name_a = "Prosperity"
    st.session_state.name_b = "Equity"
    
    # 預算暫存
    for p in ['a', 'b']:
        for field in ['edu', 'anti', 'brain', 'cons']:
            st.session_state[f'in_{p}_{field}'] = 0.0
            
    # Swap 決策狀態
    st.session_state.p1_swap = False
    st.session_state.p2_swap = False
    st.session_state.final_swap = False

game = st.session_state.game

# --- GLOBAL SETTINGS ---
with st.expander(t('settings'), expanded=False):
    st.session_state.lang = st.radio(t('lang'), ["English", "中文"], index=0 if st.session_state.lang=="English" else 1, horizontal=True)
    c1, c2 = st.columns(2)
    st.session_state.name_a = c1.text_input(t('name_a'), st.session_state.name_a)
    st.session_state.name_b = c2.text_input(t('name_b'), st.session_state.name_b)
    # (其他全域設定如常，略為節省空間但保持完整運行邏輯)

if game.year > game.total_years:
    st.success(t('sim_fin'))
    if st.button(t('restart')):
        st.session_state.game = SymbiocracyGame()
        st.session_state.turn_phase = 0
        st.rerun()
    st.stop()

# --- MAIN UI ---
st.markdown(f"### 🏛️ {t('yr')} {game.year} | {t('governing')}: 👑 {st.session_state.name_a if game.first_party == 'A' else st.session_state.name_b}")

# 定義變數以應對當前執政與在野黨
is_A_ruling = (game.first_party == "A")
ruling_prefix = 'a' if is_A_ruling else 'b'
opp_prefix = 'b' if is_A_ruling else 'a'
ruling_name = st.session_state.name_a if is_A_ruling else st.session_state.name_b
opp_name = st.session_state.name_b if is_A_ruling else st.session_state.name_a

# ----------------- PHASE 0: RULING PARTY -----------------
if st.session_state.turn_phase == 0:
    st.header(t('turn_p0'))
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"👑 {ruling_name} (預算分配)")
        st.session_state[f'in_{ruling_prefix}_edu'] = st.number_input(t('edu'), value=st.session_state[f'in_{ruling_prefix}_edu'], key="p0_edu")
        st.session_state[f'in_{ruling_prefix}_anti'] = st.number_input(t('anti'), value=st.session_state[f'in_{ruling_prefix}_anti'], key="p0_anti")
        st.session_state[f'in_{ruling_prefix}_brain'] = st.number_input(t('brain'), value=st.session_state[f'in_{ruling_prefix}_brain'], key="p0_brain")
        st.session_state[f'in_{ruling_prefix}_cons'] = st.number_input(t('cons'), value=st.session_state[f'in_{ruling_prefix}_cons'], key="p0_cons")
        
    with c2:
        st.subheader("系統參數與策略")
        game.R_value = st.number_input(t('r_value_gov'), min_value=1.0, max_value=1000.0, value=float(game.R_value), step=0.5)
        st.info(t('r_explanation'))
        st.caption(t('swap_instruction'))
        
        # 退回修改時，若在野黨曾提出Swap，詢問是否接受
        if st.session_state.p2_swap and not st.session_state.p1_swap:
            st.warning(t('opp_proposed_swap'))
            st.session_state.p1_swap = st.checkbox(t('opp_proposed_swap_accept'), value=st.session_state.p1_swap)
        else:
            st.session_state.p1_swap = st.checkbox(t('execute_swap'), value=st.session_state.p1_swap)
            
    if st.button(t('btn_submit_prop')):
        st.session_state.turn_phase = 1
        st.rerun()

# ----------------- PHASE 1: OPPOSITION PARTY -----------------
elif st.session_state.turn_phase == 1:
    st.header(t('turn_p1'))
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"🛡️ {opp_name} (預算分配)")
        st.session_state[f'in_{opp_prefix}_edu'] = st.number_input(t('edu'), value=st.session_state[f'in_{opp_prefix}_edu'], key="p1_edu")
        st.session_state[f'in_{opp_prefix}_anti'] = st.number_input(t('anti'), value=st.session_state[f'in_{opp_prefix}_anti'], key="p1_anti")
        st.session_state[f'in_{opp_prefix}_brain'] = st.number_input(t('brain'), value=st.session_state[f'in_{opp_prefix}_brain'], key="p1_brain")
        st.session_state[f'in_{opp_prefix}_cons'] = st.number_input(t('cons'), value=st.session_state[f'in_{opp_prefix}_cons'], key="p1_cons")
        
    with c2:
        st.subheader("執政黨提案檢視")
        st.text(f"{t('r_value_lock')} {game.R_value}")
        
        if st.session_state.p1_swap:
            st.warning(t('ruling_locked_swap'))
            st.session_state.p2_swap = True # 被迫強制鎖定
        else:
            st.session_state.p2_swap = st.checkbox(t('execute_swap_opp'), value=st.session_state.p2_swap)

    if st.button(t('btn_submit_react')):
        st.session_state.turn_phase = 2
        st.rerun()

# ----------------- PHASE 2: FINAL REVIEW -----------------
elif st.session_state.turn_phase == 2:
    st.header(t('turn_p2'))
    
    st.write(f"**{ruling_name} 總支出:** {sum([st.session_state[f'in_{ruling_prefix}_{x}'] for x in ['edu','anti','brain','cons']])}")
    st.write(f"**{opp_name} 總支出:** {sum([st.session_state[f'in_{opp_prefix}_{x}'] for x in ['edu','anti','brain','cons']])}")
    
    # Swap 最終決議
    if st.session_state.p2_swap and not st.session_state.p1_swap:
        st.warning(t('opp_proposed_swap'))
        st.session_state.final_swap = st.checkbox(t('opp_proposed_swap_accept'), value=st.session_state.final_swap)
    else:
        st.session_state.final_swap = st.session_state.p1_swap
        if st.session_state.final_swap:
            st.info(t('execute_swap_lock'))

    c1, c2 = st.columns(2)
    with c1:
        if st.button(t('btn_revise')):
            st.session_state.turn_phase = 0
            st.rerun()
    with c2:
        if st.button(t('confirm_btn'), type="primary"):
            inputs = {
                'A': {'edu': st.session_state.in_a_edu, 'anti': st.session_state.in_a_anti, 'brain': st.session_state.in_a_brain, 'cons': st.session_state.in_a_cons},
                'B': {'edu': st.session_state.in_b_edu, 'anti': st.session_state.in_b_anti, 'brain': st.session_state.in_b_brain, 'cons': st.session_state.in_b_cons}
            }
            game.process_year(inputs, execute_swap=st.session_state.final_swap)
            
            # Reset Phase Variables
            st.session_state.turn_phase = 0
            st.session_state.p1_swap = False
            st.session_state.p2_swap = False
            st.session_state.final_swap = False
            for p in ['a', 'b']:
                for field in ['edu', 'anti', 'brain', 'cons']:
                    st.session_state[f'in_{p}_{field}'] = 0.0
                    
            st.rerun()
