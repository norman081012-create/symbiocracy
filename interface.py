# ==========================================
# interface.py
# 負責 UI 渲染、動態戰報、標準化組件
# ==========================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
import content
import formulas

def render_global_settings(cfg, game):
    st.sidebar.title("⚙️ 全域變數控制台")
    with st.sidebar.expander("📝 動態調整遊戲參數", expanded=False):
        for key, default_val in content.DEFAULT_CONFIG.items():
            label = content.CONFIG_TRANSLATIONS.get(key, key)
            if isinstance(default_val, float): cfg[key] = st.number_input(label, value=float(cfg[key]), step=0.1, format="%.2f", key=f"cfg_{key}")
            elif isinstance(default_val, int): cfg[key] = st.number_input(label, value=int(cfg[key]), step=1, key=f"cfg_{key}")
            elif isinstance(default_val, str): cfg[key] = st.text_input(label, value=str(cfg[key]), key=f"cfg_{key}")
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_dashboard(game, view_party, cfg, is_preview=False, preview_data=None):
    st.markdown(f"### 年份: {game.year} / {cfg['END_YEAR']} &nbsp;&nbsp;|&nbsp;&nbsp; {content.get_election_icon(game.year, cfg['ELECTION_CYCLE'])}")
    
    show_last = st.toggle("顯示去年對比", value=False) if game.year > 1 else False
    rep = game.last_year_report
    
    d_gdp = preview_data['gdp'] if is_preview else game.gdp
    d_san = preview_data['san'] if is_preview else game.sanity
    d_emo = preview_data['emo'] if is_preview else game.emotion
    d_h_fund = preview_data['h_fund'] if is_preview else game.h_fund
    d_budg = preview_data['budg'] if is_preview else game.total_budget

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("#### 🌐 國家總體現況")
        san_val = d_san * 100
        san_str = f"{san_val:.1f} ({san_val - (rep['old_san']*100 if rep and show_last else san_val):+.1f})" if show_last else f"{san_val:.1f}"
        st.write(f"**公民識讀:** {content.get_civic_index_text(d_san)}")
        st.write(f"**選民情緒:** {content.get_emotion_text(d_emo)}")
        
        gdp_base = rep['old_gdp'] if rep and show_last else game.gdp
        st.write(f"**當前 GDP:** `{d_gdp:.0f}` ({d_gdp - gdp_base:+.0f})")
        if rep and show_last: st.caption(f"判定: {content.get_performance_eval(game.gdp, rep['target_gdp'])}")

    with c2:
        st.markdown("#### 💰 執行系統資源")
        budg_base = rep['old_budg'] if rep and show_last else game.total_budget
        st.write(f"**預算池:** `{d_budg:.0f}` ({d_budg - budg_base:+.0f})")
        st.write(f"**獎勵基金:** `{d_h_fund:.0f}`")
        if rep and show_last: st.caption(f"判定: {content.get_performance_eval(game.h_fund, rep['target_h_fund'])}")

    with c3:
        if not is_preview:
            st.markdown("#### 🕵️ 智庫機密通報")
            fc = view_party.current_forecast
            acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
            st.info(f"經濟預估: {content.get_economic_forecast_text(fc)} (-{fc:.2f})\n\n準確度: {acc}%")
        else:
            st.markdown("#### 🔮 智庫實時預演")
            my_is_h = (view_party.name == game.h_role_party.name)
            my_inc = preview_data['h_net'] if my_is_h else preview_data['r_net']
            my_roi = preview_data['h_roi'] if my_is_h else preview_data['r_roi']
            my_sup = preview_data['h_sup'] if my_is_h else preview_data['r_sup']
            st.success(f"🟢 我方預計: `${my_inc:.0f}`\n\n(ROI: {my_roi:.1f}%) | 支持: {my_sup:+.2f}%")

    with c4:
        if not is_preview:
            st.markdown("#### 📊 智庫檢討")
            if rep:
                diff = abs(rep['view_party_forecast'] - rep['real_decay'])
                st.write(f"**評語:** {content.get_thinktank_eval(view_party.predict_ability, diff)}")
            else: st.info("新任期暫無數據")
        else:
            my_is_h = (view_party.name == game.h_role_party.name)
            opp_inc = preview_data['r_net'] if my_is_h else preview_data['h_net']
            opp_roi = preview_data['r_roi'] if my_is_h else preview_data['h_roi']
            opp_sup = preview_data['r_sup'] if my_is_h else preview_data['h_sup']
            st.error(f"🔴 對手預計: `${opp_inc:.0f}`\n\n(ROI: {opp_roi:.1f}%) | 支持: {opp_sup:+.2f}%")
    st.markdown("---")

def render_message_board(game, phase):
    with st.container():
        if phase == 1:
            if game.year == 1:
                st.info("🏛️ **年度通報**: 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商，確立今年的施政方向。")
            else:
                strategy = "建議策略: 監管系統應在標案利潤與嚴格度間取得平衡，避免激怒執行系統引發倒閣。" if game.proposing_party.name == game.r_role_party.name else "建議策略: 執行系統應檢視標案是否具備足夠 ROI，若利潤太薄，可考慮退回或提最後通牒。"
                st.info(f"🏛️ **年度通報**: {strategy}")
        
        if st.session_state.get('news_flash'):
            st.warning(f"🗞️ **新聞快訊**: {st.session_state.news_flash}")
            st.session_state.news_flash = None
            
        rep = game.last_year_report
        if rep:
            with st.expander("📊 去年財報與實績對比", expanded=False):
                c1, c2, c3 = st.columns(3)
                my_is_h = game.proposing_party.name == rep['h_party_name']
                r_inc, e_inc = (rep['h_inc'], rep['est_h_inc']) if my_is_h else (rep['r_inc'], rep['est_r_inc'])
                r_sup, e_sup = (rep['h_sup_shift'], rep['est_h_sup_shift']) if my_is_h else (rep['r_sup_shift'], rep['est_r_sup_shift'])
                c1.write(f"**真實衰退:** `{rep['real_decay']:.2f}`\n\n**我方原估:** `{rep['view_party_forecast']:.2f}`")
                c2.write(f"**去年實質淨利:** `${r_inc:.0f}`\n\n**去年原估淨利:** `${e_inc:.0f}`")
                c3.write(f"**實質支持度變化:** `{r_sup:+.2f}%`\n\n**原估支持度變化:** `{e_sup:+.2f}%`")
    st.markdown("---")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    for col, party in zip([c1, c2], [view_party, opp]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role = "🛡️ **[執行系統]**" if is_h else "⚖️ **[監管系統]**"
            is_win = (game.ruling_party.name == party.name)
            crown = "👑" if is_win else ""
            
            if is_election_year or god_mode: disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is
