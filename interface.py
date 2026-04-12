# ==========================================
# interface.py
# 負責 UI 渲染、動態戰報、公式除錯面板
# ==========================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import content

def render_global_settings(cfg):
    st.sidebar.title("⚙️ 全域變數控制台")
    with st.sidebar.expander("📝 動態調整遊戲參數", expanded=False):
        for key, default_val in content.DEFAULT_CONFIG.items():
            label = content.CONFIG_TRANSLATIONS.get(key, key)
            if isinstance(default_val, float): cfg[key] = st.number_input(label, value=float(cfg[key]), step=0.1, format="%.2f", key=f"cfg_{key}")
            elif isinstance(default_val, int): cfg[key] = st.number_input(label, value=int(cfg[key]), step=1, key=f"cfg_{key}")
            elif isinstance(default_val, str): cfg[key] = st.text_input(label, value=str(cfg[key]), key=f"cfg_{key}")

def render_think_tank_toast(view_party, acc_percent, fc_val):
    st.info(f"🕵️ **智庫機密通報 [{view_party.name} 視角]** | 經濟預估: {content.get_economic_forecast_text(fc_val)} (衰退參數: -{fc_val:.2f}) | 報告準確度: {acc_percent}%")

def render_status_bar(game, cfg):
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("🌐 國家總體現況")
        st.markdown(f"**公民識讀指數:** `{content.get_civic_index_text(game.sanity)}`")
        st.markdown(f"**選民情緒參數:** `{content.get_emotion_text(game.emotion)}`")
        
        rep = game.last_year_report
        if rep:
            gdp_change = ((game.gdp - rep['old_gdp']) / rep['old_gdp']) * 100
            st.markdown(f"**GDP:** `{game.gdp:.1f}` *(年變動: {gdp_change:+.2f}%)*")
            st.caption(f"↳ 去年目標: 成長 {rep['target_gdp_growth']}%")
            if rep['r_perf'] >= 0: st.success("✅ GDP 達標，帶動預算上升。")
            else: st.error("📉 GDP 未達標！")
        else:
            st.markdown(f"**GDP:** `{game.gdp:.1f}`")

    with c2:
        st.subheader("💰 執行系統資源")
        current_h_ratio = (game.h_fund / game.total_budget) * 100 if game.total_budget > 0 else 50
        st.markdown(f"**總預算池:** `{game.total_budget:.0f}`")
        st.markdown(f"**執行獎勵基金:** `{game.h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*")
        
        if rep:
            h_party_name = rep['h_party_name']
            st.caption(f"↳ 去年 {h_party_name} 績效結算，目標: {rep['target_h_fund']:.0f}")
            h_perf = rep['h_perf']
            if h_perf >= 0: st.success(f"✅ {h_party_name} 績效達標。")
            else:
                if h_perf >= -10: st.warning(f"⚠️ {h_party_name} 勉強及格 (落差 {h_perf:.1f}%)")
                else: st.error(f"🚨 {h_party_name} 嚴重落後 (落差 {h_perf:.1f}%)")
                if rep['h_blame_saved'] < 0:
                    st.caption(f"🗣️ **媒體效應:** {h_party_name} 成功將 {abs(rep['h_blame_saved']):.1f} 點失分硬推給對手！選民分不清責任歸屬。")

    with c3:
        st.subheader("🕵️ 智庫年度檢討分析")
        if rep:
            rd = rep['real_decay']; fc = rep['view_party_forecast']
            st.write(f"真實衰退: `{rd:.2f}` | 我方原估: `{fc:.2f}`")
            if abs(fc - rd) > 0.15: st.error("❌ 預估嚴重失準：智庫未能察覺經濟異常。建議提升調查預測。")
            if rep['caught_corruption']: st.error("🚨 貪腐爆雷：執行方貪污遭逮，民心重挫。")
            elif not rep['caught_corruption'] and rep['h_perf'] < -15: st.warning("📉 執行效率極度低迷，資金轉換率不佳。")
            else: st.success("✅ 發展基本符合預期。")
        else:
            st.info("新任期開始，尚無檢討資料。")
    st.markdown("---")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    c1, c2 = st.columns(2)
    for col, party in zip([c1, c2], [game.party_A, game.party_B]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role_badge = "🛡️ **[執行者]**" if is_h else "⚖️ **[調節者]**"
            crown = "👑" if game.ruling_party.name == party.name else ""
            blur = 1.0 - (view_party.predict_ability / cfg['MAX_ABILITY']) if not god_mode else 0.0
            disp_sup = f"{party.support:.1f}%" if is_election_year or god_mode else "??? (需作民調)"
            
            import random
            rng_status = random.Random(f"status_{game.year}_{party.name}_{view_party.name}")
            fog_w = rng_status.uniform(max(0, party.wealth * (1 - blur)), party.wealth * (1 + blur))
            disp_w = f"{party.wealth:.0f}" if (party == view_party or god_mode) else f"估算約 {fog_w:.0f}"

            if party.name == view_party.name: st.success(f"### 👁️ {party.name} {crown} {role_badge}\n**黨產:** {disp_w} | **支持度:** {disp_sup}")
            else: st.info(f"### {party.name} {crown} {role_badge}\n**黨產:** {disp_w} | **支持度:** {disp_sup}")

def render_real_time_formulas(req_funds, h_ratio, r_pays, h_pays, r_val, t_h, t_gdp, act_h, act_gdp, net_inc, opp_net_inc, my_sup, opp_sup, is_h):
    with st.expander("🧮 運算公式與數值追蹤面板 (動態解構)", expanded=False):
        st.markdown(f"""
        **1. 資金總池推算 (Required Funds)**: 
        總需資金 = {req_funds} (H端分配率: {h_ratio:.2f}) | 投資方: (調節者出 {r_pays} / 執行者出 {h_pays})
        
        **2. 淨利推算 (Net Income)**: 
        我方淨利 = {net_inc:.0f} | 對手淨利 = {opp_net_inc:.0f}
        
        **3. 民調變動推算 (Support Shift)**:
        我方預計民調變更 = {my_sup:+.2f}% | 對手預計民調變更 = {opp_sup:+.2f}%
        """)
