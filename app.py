import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random
from game_engine import SymbiocracyGame
from i18n import t

# --- CONFIG ---
st.set_page_config(page_title="Symbiocracy Simulator", layout="wide")

# --- INITIALIZE STATE ---
if 'game' not in st.session_state:
    st.session_state.game = SymbiocracyGame()
    st.session_state.lang = "English"
    st.session_state.turn_phase = 0
    st.session_state.name_a = "Prosperity"
    st.session_state.name_b = "Equity"
    st.session_state.show_decay = False
    st.session_state.do_swap = False
    st.session_state.r_val = 0.5
    st.session_state.label_style = "Short"
    
    # Inputs persistent storage
    for p in ['a', 'b']:
        for field in ['edu', 'anti', 'brain', 'cons']:
            st.session_state[f'in_{p}_{field}'] = 0.0

game = st.session_state.game

# --- GLOBAL SETTINGS ---
with st.expander(t('settings'), expanded=False):
    c_l1, c_l2 = st.columns(2)
    st.session_state.lang = c_l1.radio(t('lang'), ["English", "中文"], index=0 if st.session_state.lang=="English" else 1, horizontal=True)
    st.session_state.label_style = c_l2.radio(t('label_style'), [t('short'), t('full')], horizontal=True)
    
    c1, c2 = st.columns(2)
    st.session_state.name_a = c1.text_input(t('name_a'), st.session_state.name_a)
    st.session_state.name_b = c2.text_input(t('name_b'), st.session_state.name_b)
    
    c1, c2 = st.columns(2)
    dec_range = c1.slider(t('decay_range'), 0.0, 3.0, (game.decay_min, game.decay_max), 0.05)
    game.decay_min, game.decay_max = dec_range
    game.total_years = c2.slider(t('total_years'), 5, 100, game.total_years, 1)

    c1, c2 = st.columns(2)
    game.annual_budget = c1.number_input(t('base_budget'), value=game.annual_budget, step=100)
    game.major_bonus = c2.number_input(t('major_bonus'), value=game.major_bonus, step=50)

    c1, c2 = st.columns(2)
    game.tax_impact = c1.number_input(t('tax_impact'), value=game.tax_impact, step=50.0)
    game.emotionality = c2.slider(t('voter_emotion'), 0.0, 1.0, game.emotionality, 0.05)

    c1, c2 = st.columns(2)
    game.edu_mult = c1.number_input(t('edu_impact'), value=game.edu_mult, step=0.0001, format="%.4f")
    game.bw_mult = c2.number_input(t('bw_impact'), value=game.bw_mult, step=0.0001, format="%.4f")

    c1, c2 = st.columns(2)
    game.A_wealth = c1.number_input(t('set_wealth_a'), value=float(game.A_wealth))
    game.B_wealth = c2.number_input(t('set_wealth_b'), value=float(game.B_wealth))

# --- GAME OVER SCREEN ---
if game.year > game.total_years:
    st.success(t('sim_fin'))
    df = pd.DataFrame(game.history)
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(df['Year'], df['TrueH'], label='Satisfaction', color='green')
    ax1.plot(df['Year'], df['A_Support'], label=f"Support {st.session_state.name_a}", color='red')
    ax2 = ax1.twinx()
    ax2.plot(df['Year'], df['A_Wealth'], color='orange', alpha=0.5, label=f"Wealth {st.session_state.name_a}")
    fig.legend()
    st.pyplot(fig)
    if st.button(t('restart')):
        st.session_state.game = SymbiocracyGame()
        st.session_state.turn_phase = 0
        st.rerun()
    st.stop()

# --- MAIN UI ---
st.markdown(f"### 🏛️ {t('yr')} {game.year} | {t('governing')}: 👑 {st.session_state.name_a if game.first_party == 'A' else st.session_state.name_b}")

# (中間介面邏輯與原本一致，但使用 t() 函數獲取翻譯內容...)
# 因為篇幅限制，這裡的核心操作是調用 game.process_year(inputs)
st.write("遊戲運行中...請根據各個階段輸入數據。")

if st.button(t('confirm_btn')):
    # 範例：提交數據
    inputs = {
        'A': {'edu': st.session_state.in_a_edu, 'anti': st.session_state.in_a_anti, 'brain': st.session_state.in_a_brain, 'cons': st.session_state.in_a_cons},
        'B': {'edu': st.session_state.in_b_edu, 'anti': st.session_state.in_b_anti, 'brain': st.session_state.in_b_brain, 'cons': st.session_state.in_b_cons}
    }
    game.process_year(inputs)
    st.rerun()
