# ==========================================
# phase2.py
# 負責 第二階段 (執行)
# ==========================================
import streamlit as st
import ui_core

def t(en, zh): return zh if st.session_state.get('lang') == 'ZH' else en

def render(game, view_party, opponent_party, cfg):
    st.subheader(t(f"🛠️ Phase 2: Execution - {view_party.name}", f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name}"))
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(t("#### 📣 Policy & Media", "#### 📣 政策與媒體"))
        media_ctrl = st.slider(t("📺 Media Control", "📺 媒體操控"), 0, 500, 0)
        camp_amt = st.slider(t("🎉 Campaigning", "🎉 舉辦競選"), 0, 500, 0)
        
    if st.button(t("Confirm & Settle", "確認行動/結算"), type="primary"):
        st.success(t("Turn ended.", "回合結束"))
