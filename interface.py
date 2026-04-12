# ==========================================
# interface.py
# 負責動態全域設定、狀態列戰報、圖表與即時公式面板
# ==========================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import content

def render_global_settings(cfg):
    st.sidebar.title("⚙️ 全域變數控制台")
    with st.sidebar.expander("📝 動態調整遊戲參數 (即時連動)", expanded=False):
        for key, default_val in content.DEFAULT_CONFIG.items():
            label = content.CONFIG_TRANSLATIONS.get(key, key)
            if isinstance(default_val, float):
                cfg[key] = st.number_input(label, value=float(cfg[key]), step=0.1, format="%.2f", key=f"cfg_{key}")
            elif isinstance(default_val, int):
                cfg[key] = st.number_input(label, value=int(cfg[key]), step=1, key=f"cfg_{key}")
            elif isinstance(default_val, str):
                cfg[key] = st.text_input(label, value=str(cfg[key]), key=f"cfg_{key}")

def render_status_bar(game, cfg):
    """繪製包含深度戰報的主畫面狀態列"""
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    
    # 總體經濟與戰報
    with c1:
        st.subheader("🌐 國家總體現況")
        st.markdown(f"**公民識讀指數:** `{content.get_civic_index_text(game.sanity)}`")
        
        rep = game.last_year_report
        if rep:
            gdp_change = ((game.gdp - rep['old_gdp']) / rep['old_gdp']) * 100
            st.markdown(f"**GDP (總體經濟):** `{game.gdp:.1f}`  *(年變動率: {gdp_change:+.2f}%)*")
            st.caption(f"↳ 去年議定目標: 成長 {rep['target_gdp_growth']}%")
            
            # GDP 判讀
            if rep['r_perf'] >= 0: st.success("✅ GDP 成功達標，帶動整體預算上升。")
            else:
                st.error("📉 GDP 未達標！")
                if rep['r_blame_saved'] < 0:
                    st.caption(f"🗣️ **甩鍋效應:** R 黨發動宣傳戰，成功將 {abs(rep['r_blame_saved']):.1f} 點民怨轉嫁給 H 黨！(選民分不清是誰的責任)")
        else:
            st.markdown(f"**GDP (總體經濟):** `{game.gdp:.1f}`")

    # H Fund 與戰報
    with c2:
        st.subheader("💰 行政系統資源")
        current_h_ratio = (game.h_fund / game.total_budget) * 100 if game.total_budget > 0 else 50
        st.markdown(f"**目前總預算池:** `{game.total_budget:.0f}`")
        st.markdown(f"**本期 H 獎勵基金:** `{game.h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*")
        
        if rep:
            h_party_name = rep['h_party_name']
            st.caption(f"↳ 去年 H 黨 ({h_party_name}) 績效結算，原議定目標: {rep['target_h_fund']:.0f}")
            
            h_perf = rep['h_perf']
            if h_perf >= 0: st.success(f"✅ {h_party_name} 績效達標，穩固執政資源。")
            else:
                if h_perf >= -10: st.warning(f"⚠️ {h_party_name} 績效勉強及格 (落差 {h_perf:.1f}%)")
                else: st.error(f"🚨 {h_party_name} 施政嚴重落後 (落差 {h_perf:.1f}%)")
                
                if rep['h_blame_saved'] < 0:
                    st.caption(f"🛡️ **卸責效應:** {h_party_name} 動用網軍護航，將 {abs(rep['h_blame_saved']):.1f} 點失分硬是推給了 R 黨的杯葛！")

    # 智庫年度總結
    with c3:
        st.subheader("🕵️ 智庫年度檢討分析")
        if rep:
            rd = rep['real_decay']
            fc = rep['view_party_forecast']
            diff = abs(fc - rd)
            
            st.write(f"真實衰退(景氣): `{rd:.2f}` | 我方預估: `{fc:.2f}`")
            
            # 分析落差原因
            reasons = []
            if diff > 0.15: reasons.append("❌ **預估嚴重失準**：智庫未能察覺全球經濟風暴。")
            if rep['caught_corruption']: reasons.append("🚨 **貪腐爆雷**：H 黨貪污遭查獲，民心盡失，重創績效。")
            if rep['h_perf'] < -20 and not rep['caught_corruption']: reasons.append("📉 **施政極度無能**：即使未被抓貪，H 黨的建設轉換率低迷，導致資金浪費。")
            
            if not reasons: st.success("✅ 去年政局發展基本符合智庫沙盤推演，社會穩定。")
            else:
                for r in reasons: st.markdown(r)
            
            st.info("💡 **下期建議:** " + ("應加強智庫準確度與調查局預算。" if diff > 0.15 else "對手宣傳力道增強，建議增加政治防禦(甩鍋/公關)預算。"))
        else:
            st.info("新任期開始，尚無檢討資料。")
    st.markdown("---")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    """繪製帶有 H/R Role 標示的政黨卡片"""
    c1, c2 = st.columns(2)
    for col, party in zip([c1, c2], [game.party_A, game.party_B]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role_badge = "🛡️ **[行政(H)]**" if is_h else "🔍 **[監督(R)]**"
            crown = "👑" if game.ruling_party.name == party.name else ""
            
            blur = 1.0 - (view_party.predict_ability / cfg['MAX_ABILITY']) if not god_mode else 0.0
            
            disp_sup = f"{party.support:.1f}%" if is_election_year or god_mode else "??? (需作民調)"
            
            import random
            rng_status = random.Random(f"status_{game.year}_{party.name}_{view_party.name}")
            fog_w = rng_status.uniform(max(0, party.wealth * (1 - blur)), party.wealth * (1 + blur))
            disp_w = f"{party.wealth:.0f}" if (party == view_party or god_mode) else f"估算約 {fog_w:.0f}"

            if party.name == view_party.name:
                st.success(f"### 👁️ {party.name} {crown} {role_badge}\n**黨產:** {disp_w} | **支持度:** {disp_sup}")
            else:
                st.info(f"### {party.name} {crown} {role_badge}\n**黨產:** {disp_w} | **支持度:** {disp_sup}")
    st.markdown("---")

def render_real_time_formulas(req_funds, h_ratio, r_pays, h_pays, r_val, t_h, t_gdp, curr_h, curr_gdp):
    """主頁最下方的動態公式收合面板 (Point 3)"""
    with st.expander("🧮 即時運算公式與數值追蹤 (研發者除錯用面板)", expanded=False):
        st.markdown("所有公式皆依據目前草擬參數即時連動計算：")
        
        strict_mult = r_val ** 2
        
        st.markdown(f"""
        **1. 嚴格度撞牆乘數 (Exponential Strictness):** $$ \text{{Strict}} = r^2 = {r_val}^2 = {strict_mult:.2f} $$
        *(R值設越高，H黨需要的建設總資金會以拋物線飆升)*
        
        **2. 總資金池分配 (Required Funds):** $$ \text{{ReqFunds}} = {req_funds} \quad (\text{{H-Ratio}}: {h_ratio:.2f}) $$
        $$ \text{{R出資}} = {r_pays} \quad | \quad \text{{H出資}} = {h_pays} $$
        """)

def add_event_vlines(fig, history_df):
    for _, row in history_df.iterrows():
        y = row['Year']
        if row['Is_Swap']: fig.add_vline(x=y, line_dash="dot", line_color="red", annotation_text="Swap!", annotation_position="top left")
        if row['Is_Election']: fig.add_vline(x=y, line_dash="dash", line_color="green", annotation_text="選舉", annotation_position="bottom right")

def render_endgame_charts(history_data, cfg):
    st.balloons()
    st.title("🏁 遊戲結束！共生內閣軌跡總結算")
    df = pd.DataFrame(history_data)

    st.subheader("📊 1. 總體經濟與公民識讀指數走勢")
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['GDP'], name="總 GDP", line=dict(color='blue', width=3)), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity']*100, name="公民識讀 (0-100)", line=dict(color='purple', width=3)), secondary_y=True)
    fig1.update_yaxes(title_text="GDP (資金)", secondary_y=False)
    fig1.update_yaxes(title_text="識讀指數", secondary_y=True, range=[0, 100])
    add_event_vlines(fig1, df)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader(f"📊 2. 雙方民意支持度與黨產角力")
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['A_Wealth'], name=f"{cfg['PARTY_A_NAME']} 存款", line=dict(color='cyan', dash='dash')), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['B_Wealth'], name=f"{cfg['PARTY_B_NAME']} 存款", line=dict(color='orange', dash='dash')), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['A_Support'], name=f"{cfg['PARTY_A_NAME']} 民意支持度", line=dict(color='green', width=4)), secondary_y=True)
    fig2.update_yaxes(title_text="財富總額", secondary_y=False)
    fig2.update_yaxes(title_text="支持度 (%)", secondary_y=True, range=[0, 100])
    add_event_vlines(fig2, df)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📊 3. 兩黨硬實力成長軌跡")
    fig3 = go.Figure()
    abilities = [('Build', '建設'), ('Inv', '調查'), ('Edu', '教育'), ('Prop', '宣傳'), ('Blame', '甩鍋')]
    colors = ['#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']
    for i, (key, label) in enumerate(abilities):
        fig3.add_trace(go.Scatter(x=df['Year'], y=df[f'A_{key}'], name=f"A黨-{label}", line=dict(color=colors[i])))
        fig3.add_trace(go.Scatter(x=df['Year'], y=df[f'B_{key}'], name=f"B黨-{label}", line=dict(color=colors[i], dash='dot')))
    fig3.update_layout(yaxis_title="能力等級")
    add_event_vlines(fig3, df)
    st.plotly_chart(fig3, use_container_width=True)
