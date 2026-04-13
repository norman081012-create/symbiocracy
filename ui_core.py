# ==========================================
# ui_core.py
# 負責共用 UI 渲染
# ==========================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import config
import formulas
import engine
import random

def t(en, zh): return zh if st.session_state.get('lang') == 'ZH' else en

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_global_settings(cfg, game):
    is_zh = (st.session_state.lang == 'ZH')
    st.sidebar.title(t("🎛️ Control Panel", "🎛️ 控制台"))
    if st.sidebar.button(t("🌐 切換至中文", "🌐 Switch to English"), use_container_width=True):
        st.session_state.lang = 'EN' if is_zh else 'ZH'
        st.rerun()

    with st.sidebar.expander(t("📝 Real-time Config", "📝 參數調整(即時)"), expanded=False):
        trans = config.get_config_translations()
        for key, default_val in config.DEFAULT_CONFIG.items():
            label = trans.get(key, key)
            if 'COLOR' in key: cfg[key] = st.color_picker(label, value=cfg[key], key=f"cfg_{key}")
            elif isinstance(default_val, float): cfg[key] = st.number_input(label, value=float(cfg[key]), step=0.1, format="%.2f", key=f"cfg_{key}")
            elif isinstance(default_val, int): cfg[key] = st.number_input(label, value=int(cfg[key]), step=1, key=f"cfg_{key}")
            elif isinstance(default_val, str): cfg[key] = st.text_input(label, value=str(cfg[key]), key=f"cfg_{key}")
    sync_party_names(game, cfg)

def render_dashboard(game, view_party, cfg, is_preview=False, preview_data=None):
    rep = game.last_year_report
    st.markdown("---")
    
    disp_gdp = preview_data['gdp'] if is_preview else game.gdp
    disp_san = preview_data['san'] if is_preview else game.sanity
    disp_emo = preview_data['emo'] if is_preview else game.emotion
    disp_h_fund = preview_data['h_fund'] if is_preview else game.h_fund
    disp_budg = preview_data['budg'] if is_preview else game.total_budget
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(t("### 🌐 National Status", "### 🌐 國家總體現況"))
        san_chg = (disp_san - rep['old_san']) if rep else 0
        st.markdown(f"**{t('Civic Literacy', '資訊辨識')}:** `{config.get_civic_index_text(disp_san)}` *({t('Change', '變動')}: {san_chg:+.1f})*")
        emo_chg = disp_emo - rep['old_emo'] if rep else 0
        st.markdown(f"**{t('Voter Emotion', '選民情緒')}:** `{config.get_emotion_text(disp_emo)}` *({t('Change', '變動')}: {emo_chg:+.1f})*")
        if is_preview: st.markdown(f"**{t('Est. GDP', '預估 GDP')}:** `{disp_gdp:.0f}`")
        else: st.markdown(f"**{t('Current GDP', '當前 GDP')}:** `{disp_gdp:.1f}`")

    with c2:
        st.markdown(t("### 💰 H-System Resources", "### 💰 執行系統資源"))
        if game.year == 1 and not is_preview: st.info(t("Year 1: Reorganizing.", "首年重整中，尚未配發獎勵。"))
        else:
            st.markdown(f"**{t('Total Budget', '總預算池')}:** `{disp_budg:.0f}`")
            st.markdown(f"**{t('Reward Fund', '獎勵基金')}:** `{disp_h_fund:.0f}`")

    with c3:
        fc = view_party.current_forecast
        acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
        st.markdown(f"### 🕵️ {t('Think Tank', '智庫')} {t('Accuracy', '準確度')}: {acc}%")
        st.write(t(f"Forecast: {config.get_economic_forecast_text(fc)} (-{fc:.2f})", f"經濟預估: {config.get_economic_forecast_text(fc)}(預估衰退值: -{fc:.2f})"))

    with c4:
        st.markdown(f"### 📊 {t('Finance', '財報')}")
        if is_preview:
            st.markdown(t("Evaluating Plan...", "智庫評估報告中..."))
        else:
            st.write(t(f"Net Assets: {int(view_party.wealth)}", f"可用淨資產: {int(view_party.wealth)}"))
    st.markdown("---")

def render_message_board(game):
    if st.session_state.get('news_flash'): st.warning(st.session_state.news_flash); st.session_state.news_flash = None
    if game.phase == 1: st.info(t("📢 Start negotiating budget.", "📢 請盡快展開預算與目標協商。"))
    elif game.phase == 2: st.info(t("📢 Bill passed. Allocate funds.", "📢 法案已通過，請分配黨產資金。"))

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    st.header(t("👤 Player View", "👤 玩家頁面"))
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    for col, party in zip([c1, c2], [view_party, opp]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role_badge = t("🛡️ [H-System]", "🛡️ [執行系統]") if is_h else t("⚖️ [R-System]", "⚖️ [監管系統]")
            eye = "👁️ " if party.name == view_party.name else ""
            st.markdown(f"## {eye}{party.name} {role_badge}")
            st.markdown(f"### 📊 {t('Support', '支持度')}: {party.support:.1f}%")

def render_sidebar_intel_audit(game, view_party, cfg):
    st.sidebar.markdown("---")
    st.sidebar.title(t("🕵️ Intelligence Audit", "🕵️ 情報處 - 對手機構指標"))
    st.sidebar.title(t("📈 Audit - Internal", "📈 審計處 - 內部部門投資"))

def ability_slider(label, key, current_val, wealth, cfg):
    t_pct = st.slider(f"{label} ({t('Current', '當前')}: {current_val*10:.1f}%)", 0.0, 100.0, float(current_val*10), 1.0, key=key)
    t_val = t_pct / 10.0
    cost = formulas.calculate_upgrade_cost(current_val, t_val)
    st.caption(t(f"Upgrade Cost: ${int(cost)}", f"升級花費: ${int(cost)}"))
    return t_val, cost

def render_endgame_charts(history_data, cfg):
    st.title(t("🏁 Game Over!", "🏁 遊戲結束！"))
