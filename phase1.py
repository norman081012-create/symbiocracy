# ==========================================
# phase1.py
# 負責 第一階段 (提案與談判)
# ==========================================
import streamlit as st
import formulas
import engine
import ui_core

def t(en, zh): return zh if st.session_state.get('lang') == 'ZH' else en

def render(game, view_party, cfg):
    st.subheader(t(f"🤝 Phase 1: Negotiation (Round: {game.proposal_count})", f"🤝 Phase 1: 監管系統委託提案 (輪數: {game.proposal_count})"))
    
    if game.p1_step in ['draft_r', 'draft_h']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H'
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(t("⏳ Waiting for opponent...", "⏳ 等待對手公布草案..."))
        else:
            st.markdown(f"#### 📝 {t('Draft Room', '草案擬定室')}")
            claimed_decay = st.number_input(t("Claimed Decay", "公告衰退值"), value=float(view_party.current_forecast), step=0.01)
            t_gdp_growth = st.number_input(t("Target GDP Growth (%)", "目標 GDP 成長率"), value=0.0, step=0.5)
            t_h_fund = st.slider(t("Target Reward Fund", "標案達標付款"), 0.0, float(game.total_budget), 600.0)
            
            if st.button(t("📤 Submit Draft", "📤 送出常規草案"), type="primary"):
                game.p1_proposals[active_role] = {'claimed_decay': claimed_decay, 'target_gdp_growth': t_gdp_growth, 'total_funds': 500} # 簡化範例
                game.p1_step = 'voting_pick' if active_role == 'H' else 'draft_h'
                st.rerun()
