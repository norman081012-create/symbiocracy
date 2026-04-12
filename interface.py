# ==========================================
# interface.py
# 負責 UI 渲染、動態戰報、標準化組件
# ==========================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import content
import formulas

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_global_settings(cfg, game):
    st.sidebar.title("⚙️ 全域變數控制台")
    with st.sidebar.expander("📝 動態調整遊戲參數", expanded=False):
        for key, default_val in content.DEFAULT_CONFIG.items():
            label = content.CONFIG_TRANSLATIONS.get(key, key)
            if isinstance(default_val, float): cfg[key] = st.number_input(label, value=float(cfg[key]), step=0.1, format="%.2f", key=f"cfg_{key}")
            elif isinstance(default_val, int): cfg[key] = st.number_input(label, value=int(cfg[key]), step=1, key=f"cfg_{key}")
            elif isinstance(default_val, str): cfg[key] = st.text_input(label, value=str(cfg[key]), key=f"cfg_{key}")
    sync_party_names(game, cfg)

def render_dashboard(game, view_party, cfg, is_preview=False, preview_data=None):
    """整合五大元素的置頂儀表板"""
    st.markdown("---")
    
    # 動態判定要顯示當前值還是預覽值
    disp_gdp = preview_data['gdp'] if is_preview else game.gdp
    disp_san = preview_data['san'] if is_preview else game.sanity
    disp_emo = preview_data['emo'] if is_preview else game.emotion
    disp_h_fund = preview_data['h_fund'] if is_preview else game.h_fund
    disp_budg = preview_data['budg'] if is_preview else game.total_budget
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("### 🌐 國家總體現況")
        st.markdown(f"**公民識讀:** `{content.get_civic_index_text(disp_san)}`")
        st.markdown(f"**選民情緒:** `{content.get_emotion_text(disp_emo)}`")
        
        if is_preview:
            gdp_chg = ((disp_gdp - game.gdp) / max(1.0, game.gdp)) * 100
            st.markdown(f"**預估 GDP:** `{disp_gdp:.0f}` *(變動: {gdp_chg:+.2f}%)*")
        else:
            st.markdown(f"**當前 GDP:** `{disp_gdp:.1f}`")

    with c2:
        st.markdown("### 💰 執行系統資源")
        if game.year == 1 and not is_preview:
            st.info("首年重整中，尚未配發獎勵。")
        else:
            current_h_ratio = (disp_h_fund / disp_budg) * 100 if disp_budg > 0 else 50
            st.markdown(f"**總預算池:** `{disp_budg:.0f}`")
            st.markdown(f"**執行獎勵基金:** `{disp_h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*")

    with c3:
        st.markdown("### 🕵️ 智庫機密通報")
        fc = view_party.current_forecast
        acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
        st.info(f"經濟預估: **{content.get_economic_forecast_text(fc)}**\n\n*(預估衰退值: -{fc:.2f})*\n\n準確度: {acc}%")

    with c4:
        st.markdown("### 📈 智庫檢討")
        rep = game.last_year_report
        if rep:
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            eval_txt = content.get_thinktank_eval(view_party.predict_ability, diff)
            st.write(f"**評語:** {eval_txt}")
            with st.expander("顯示去年預估檢討", expanded=False):
                st.write(f"真實衰退: `{rep['real_decay']:.2f}` | 我方預估: `{rep['view_party_forecast']:.2f}`")
        else:
            st.info("尚無檢討資料。")
    st.markdown("---")

def render_message_board(game):
    """獨立的訊息中樞欄位"""
    rep = game.last_year_report
    if game.year == 1:
        st.info("🏛️ **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商，確立今年的施政方向。")
    elif st.session_state.get('news_flash'):
        st.warning(st.session_state.news_flash)
        st.session_state.news_flash = None
    elif rep:
        gdp_diff = ((game.gdp - rep['old_gdp']) / max(1.0, rep['old_gdp'])) * 100
        gdp_str = f"成長 {gdp_diff:.1f}%" if gdp_diff >= 0 else f"衰退 {abs(gdp_diff):.1f}%"
        h_str = "達標" if rep['h_perf'] >= 0 else f"落後 {abs(rep['h_perf']):.1f}%"
        st.info(f"🏛️ **【年度通報】** 回顧去年，GDP {gdp_str}，執行系統目標 {h_str}。基於此現況，請擬定今年的預算草案。")
    
    if rep:
        with st.expander("📊 去年財報與實績對比", expanded=True):
            c1, c2, c3 = st.columns(3)
            my_is_h = game.proposing_party.name == rep['h_party_name']
            r_inc, e_inc = (rep['h_inc'], rep['est_h_inc']) if my_is_h else (rep['r_inc'], rep['est_r_inc'])
            r_sup, e_sup = (rep['h_sup_shift'], rep['est_h_sup_shift']) if my_is_h else (rep['r_sup_shift'], rep['est_r_sup_shift'])
            c1.write(f"**真實衰退:** `{rep['real_decay']:.2f}`\n\n**我方原估:** `{rep['view_party_forecast']:.2f}`")
            c2.write(f"**去年實質淨利:** `${r_inc:.0f}`\n\n**去年原估淨利:** `${e_inc:.0f}`")
            c3.write(f"**去年實質支持度變化:** `{r_sup:+.2f}%`\n\n**去年原估支持度變化:** `{e_sup:+.2f}%`")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    for col, party in zip([c1, c2], [view_party, opp]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role_badge = "🛡️ **[執行系統]**" if is_h else "⚖️ **[監管系統]**"
            is_winner = (game.ruling_party.name == party.name)
            crown = "👑" if is_winner else ""
            
            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
            else:
                if party.current_poll_result is not None: disp_sup = f"📊 預估: {party.current_poll_result:.1f}%"
                else: disp_sup = "??? (需作民調)"
            
            blur = 1.0 - (view_party.predict_ability / cfg['MAX_ABILITY']) if not god_mode else 0.0
            import random
            rng_status = random.Random(f"status_{game.year}_{party.name}_{view_party.name}")
            fog_w = rng_status.uniform(max(0, party.wealth * (1 - blur)), party.wealth * (1 + blur))
            disp_w = f"{party.wealth:.0f}" if (party.name == view_party.name or god_mode) else f"估算約 {fog_w:.0f}"

            if party.name == view_party.name: 
                st.success(f"### 👁️ {party.name} {crown} {role_badge}\n**黨產:** {disp_w} | **支持度:** {disp_sup}")
                if not is_election_year:
                    b1, b2, b3 = st.columns(3)
                    if b1.button("小型民調 ($5)", key=f"p1_{party.name}"): formulas.execute_poll(game, view_party, 5); st.rerun()
                    if b2.button("中型民調 ($10)", key=f"p2_{party.name}"): formulas.execute_poll(game, view_party, 10); st.rerun()
                    if b3.button("大型民調 ($20)", key=f"p3_{party.name}"): formulas.execute_poll(game, view_party, 20); st.rerun()
            else: 
                st.info(f"### {party.name} {crown} {role_badge}\n**黨產:** {disp_w} | **支持度:** {disp_sup}")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    st.write(f"**公告衰退:** `{plan['claimed_decay']:.2f}` | **目標 GDP 成長:** `{plan['target_gdp_growth']}%`")
    st.write(f"**標案利潤(嚴格度):** `{plan['r_value']:.2f}` | **標案達標付款:** `{plan['target_h_fund']}`")
    st.write(f"**總標案需求:** `{plan['total_funds']}` | **監管系統出資:** `{plan['r_pays']}`")
    
    st.markdown("---")
    st.markdown("📊 **👁️ 本黨智庫推演報告:**")
    p_gdp_pct, p_h_g, p_h_n, p_r_g, p_r_n, p_h_sup, p_r_sup, p_est_gdp, p_est_h_fund, p_h_roi, p_r_roi = formulas.calculate_preview(
        cfg, game, plan['total_funds'], plan['h_ratio'], plan['r_value'], 
        view_party.current_forecast, game.h_role_party.build_ability, plan['r_pays'], plan['h_pays']
    )
    
    my_is_h = (view_party.name == game.h_role_party.name)
    my_net, my_sup, my_roi = (p_h_n, p_h_sup, p_h_roi) if my_is_h else (p_r_n, p_r_sup, p_r_roi)
    opp_net, opp_sup, opp_roi = (p_r_n, p_r_sup, p_r_roi) if my_is_h else (p_h_n, p_h_sup, p_h_roi)
    
    st.info(f"📈 **預期 GDP:** `{game.gdp:.0f} ➔ {p_est_gdp:.0f}` ({p_gdp_pct:+.2f}%)")
    st.success(f"🟢 **我方預期收益:** `{my_net:.0f}` (ROI: {my_roi:.1f}%) | **支持度變化:** `{my_sup:+.2f}%`")
    st.error(f"🔴 **對手預期收益:** `{opp_net:.0f}` (ROI: {opp_roi:.1f}%) | **支持度變化:** `{opp_sup:+.2f}%`")

def ability_slider(label, key, current_val, wealth, cfg):
    maint = max(0, (current_val - 3.0) * cfg['MAINTENANCE_RATE'])
    default_val = min(int(maint), int(wealth))
    invest = st.slider(f"{label} (當前: {current_val*10:.0f}%)", 0, int(wealth), default_val, key=key)
    
    if invest < maint:
        drop = (maint - invest) * 0.02
        st.caption(f"📉 投入不足維護費 (${int(maint)})，預計降至: {max(30.0, (current_val - drop)*10):.1f}%")
    else:
        gain = formulas.calc_log_gain(invest - maint)
        st.caption(f"📈 已達維護費 (${int(maint)})，預計升至: {min(100.0, (current_val + gain)*10):.1f}%")
    return invest

def add_event_vlines(fig, history_df):
    for _, row in history_df.iterrows():
        y = row['Year']
        if row['Is_Swap']: fig.add_vline(x=y, line_dash="dot", line_color="red", annotation_text="倒閣!", annotation_position="top left")
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

    st.subheader("📊 3. 兩黨硬實力成長軌跡 (0~100%)")
    fig3 = go.Figure()
    abilities = [('Build', '建設'), ('Inv', '調查'), ('Edu', '教育'), ('Media', '媒體操控')]
    colors = ['#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
    for i, (key, label) in enumerate(abilities):
        fig3.add_trace(go.Scatter(x=df['Year'], y=df[f'A_{key}']*10, name=f"A黨-{label}", line=dict(color=colors[i])))
        fig3.add_trace(go.Scatter(x=df['Year'], y=df[f'B_{key}']*10, name=f"B黨-{label}", line=dict(color=colors[i], dash='dot')))
    fig3.update_layout(yaxis_title="能力等級 (%)", yaxis=dict(range=[0, 100]))
    add_event_vlines(fig3, df)
    st.plotly_chart(fig3, use_container_width=True)
