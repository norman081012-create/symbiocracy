# ==========================================
# ui_core.py
# 負責共用 UI 渲染、圖表繪製、標準化組件
# ==========================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import config
import formulas
import engine

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_global_settings(cfg, game):
    st.sidebar.title("⚙️ 全域變數控制台")
    with st.sidebar.expander("📝 動態調整遊戲參數", expanded=False):
        for key, default_val in config.DEFAULT_CONFIG.items():
            label = config.CONFIG_TRANSLATIONS.get(key, key)
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
    
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown("### 🌐 國家總體現況")
        san_chg = (disp_san - rep['old_san']) * 100 if rep else 0
        st.markdown(f"**公民識讀:** `{config.get_civic_index_text(disp_san)}` *(變動: {san_chg:+.1f})*")
        emo_chg = disp_emo - rep['old_emo'] if rep else 0
        st.markdown(f"**選民情緒:** `{config.get_emotion_text(disp_emo)}` *(變動: {emo_chg:+.1f})*")
        if is_preview:
            st.markdown(f"**預估 GDP:** `{disp_gdp:.0f}` *(變動: {disp_gdp - game.gdp:+.0f})*")
        else:
            t_gdp = st.session_state.turn_data.get('target_gdp', 0) if game.year > 1 else 0
            st.markdown(f"**當前 GDP:** `{disp_gdp:.1f}` *(變動: {disp_gdp - rep['old_gdp'] if rep else 0:+.0f})*")
            st.caption(f"目標: {t_gdp:.0f} | 表現: {config.get_target_eval_text(disp_gdp, t_gdp)}")

    with c2:
        st.markdown("### 💰 執行系統資源")
        if game.year == 1 and not is_preview: st.info("首年重整中，尚未配發獎勵。")
        else:
            current_h_ratio = (disp_h_fund / disp_budg) * 100 if disp_budg > 0 else 50
            st.markdown(f"**總預算池:** `{disp_budg:.0f}` *(變動: {disp_budg - rep['old_budg'] if rep else 0:+.0f})*")
            t_h = st.session_state.turn_data.get('target_h_fund', 0) if game.year > 1 else 0
            st.markdown(f"**獎勵基金:** `{disp_h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*")
            if not is_preview: st.caption(f"目標: {t_h:.0f} | 表現: {config.get_target_eval_text(disp_h_fund, t_h)}")

    with c3:
        st.markdown("### 🕵️ 智庫機密通報")
        fc = view_party.current_forecast
        acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
        st.info(f"經濟預估: **{config.get_economic_forecast_text(fc)}**\n\n*(預估衰退值: -{fc:.2f})*\n\n準確度: {acc}%")

    with c4:
        st.markdown("### 📊 智庫行動預測" if game.phase == 2 else "### 📊 智庫行動預測(鎖定)")
        if is_preview:
            my_is_h = view_party.name == game.h_role_party.name
            my_net = preview_data['h_inc'] if my_is_h else preview_data['r_inc']
            opp_net = preview_data['r_inc'] if my_is_h else preview_data['h_inc']
            my_roi = preview_data['h_roi'] if my_is_h else preview_data['r_roi']
            opp_roi = preview_data['r_roi'] if my_is_h else preview_data['h_roi']
            st.success(f"🟢 **我方收益:** {my_net:.0f} (ROI: {my_roi:.1f}%)\n\n支持度: {preview_data['my_sup_shift']:+.2f}%")
            st.error(f"🔴 **對手收益:** {opp_net:.0f} (ROI: {opp_roi:.1f}%)\n\n支持度: {preview_data['opp_sup_shift']:+.2f}%")
        else:
            st.write("進入 Phase 2 調整拉桿以檢視。")

    with c5:
        st.markdown("### 📁 智庫/調查局聯合報告")
        if rep:
            my_is_h = game.proposing_party.name == rep['h_party_name']
            r_inc, e_inc = (rep['h_inc'], rep['est_h_inc']) if my_is_h else (rep['r_inc'], rep['est_r_inc'])
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            st.write(f"**智庫檢討:** {config.get_thinktank_eval(view_party.predict_ability, diff)}")
            st.markdown(f"**衰退估算:** 真:{rep['real_decay']:.2f} (估:{rep['view_party_forecast']:.2f})")
            st.markdown(f"**淨利估算:** 真:{r_inc:.0f} (估:{e_inc:.0f})")
            
            poll = view_party.current_poll_result
            if poll is not None:
                sup_shift = rep['h_sup_shift'] if my_is_h else rep['r_sup_shift']
                st.markdown(f"**支持度預測:** {poll:.1f} ({sup_shift:+.1f})")
            else: st.markdown("**支持度預測:** ??? (需作民調)")
        else:
            st.info("尚無檢討資料。")
    st.markdown("---")

def render_message_board(game):
    if st.session_state.get('news_flash'):
        st.warning(st.session_state.news_flash)
        st.session_state.news_flash = None
        
    if game.phase == 1:
        if game.year == 1: st.info("🏛️ **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商。")
        elif game.last_year_report:
            rep = game.last_year_report
            gdp_diff = ((game.gdp - rep['old_gdp']) / max(1.0, rep['old_gdp'])) * 100
            gdp_str = f"成長 {gdp_diff:.1f}%" if gdp_diff >= 0 else f"衰退 {abs(gdp_diff):.1f}%"
            h_str = "達標" if rep['h_perf'] >= 0 else f"落後 {abs(rep['h_perf']):.1f}%"
            st.info(f"🏛️ **【年度通報】** 回顧去年，GDP {gdp_str}，執行系統目標 {h_str}。請擬定今年的預算草案。")
    elif game.phase == 2:
        st.info("🛠️ **【策略建議】** 法案已通過，請分配黨產資金進行內部升級、競選造勢與媒體攻防。")

def get_maint_cost(ability, cfg):
    return max(0, (ability - 3.0) * cfg['MAINTENANCE_RATE'])

def render_strategic_intelligence_center(party, cfg, is_self=True, blur=0.0):
    total_maint = sum([get_maint_cost(a, cfg) for a in [party.build_ability, party.investigate_ability, party.edu_ability, party.media_ability, party.predict_ability]])
    total_cost = party.last_acts['policy'] - party.last_acts['legal'] + total_maint
    est_income = max(1, party.wealth)
    
    if is_self:
        st.markdown("##### 📊 內部審計局 (本年營運成本預估)")
        st.write(f"**可用淨資產:** `{party.wealth:.0f}` - `{total_cost:.0f}` = **{party.wealth - total_cost:.0f}**")
        with st.expander("詳細開銷佔比(基於目前資產)"):
            st.write(f"政策投入: {party.last_acts['policy']:.0f} ({(party.last_acts['policy']/est_income)*100:.1f}%)")
            st.write(f"專案法定款: {party.last_acts['legal']:.0f} ({(party.last_acts['legal']/est_income)*100:.1f}%)")
            st.write(f"本年維護費: {total_maint:.0f} ({(total_maint/est_income)*100:.1f}%)")
    else:
        st.markdown("##### 🕵️ 國家情報局 (對手情資還原)")
        import random
        rng = random.Random(f"intel_{party.name}")
        est_wealth = rng.uniform(max(0, party.wealth * (1 - blur)), party.wealth * (1 + blur))
        est_cost = rng.uniform(max(0, total_cost * (1 - blur)), total_cost * (1 + blur))
        st.write(f"**估算資產:** `約 {est_wealth:.0f}` - `營運 {est_cost:.0f}` = **約 {est_wealth - est_cost:.0f}**")
        st.progress(1.0 - blur, text=f"情報準確度: {int((1.0 - blur)*100)}%")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    st.header("👤 玩家頁面")
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    
    st.markdown(f"""
    <style>
    div[data-testid="column"]:nth-child(1) {{ background-color: {cfg['PARTY_A_COLOR']}1A; padding: 15px; border-radius: 10px; border-left: 5px solid {cfg['PARTY_A_COLOR']}; }}
    div[data-testid="column"]:nth-child(2) {{ background-color: {cfg['PARTY_B_COLOR']}1A; padding: 15px; border-radius: 10px; border-left: 5px solid {cfg['PARTY_B_COLOR']}; }}
    </style>
    """, unsafe_allow_html=True)

    for col, party in zip([c1, c2], [view_party, opp]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role_badge = "🛡️ [執行系統]" if is_h else "⚖️ [監管系統]"
            is_winner = (game.ruling_party.name == party.name)
            crown = "👑" if is_winner else ""
            
            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
            else:
                disp_sup = f"📊 {party.current_poll_result:.1f}%" if party.current_poll_result is not None else "??? (需作民調)"
            
            blur = 1.0 - (view_party.investigate_ability / cfg['MAX_ABILITY']) if not god_mode else 0.0

            if party.name == view_party.name: 
                st.markdown(f"## 👁️ {party.name} {crown} {role_badge}")
                st.markdown(f"### 支持度: {disp_sup}")
                st.markdown("#### 🏛️ 戰略情報中心")
                render_strategic_intelligence_center(party, cfg, is_self=True)
                
                if not is_election_year:
                    b1, b2, b3 = st.columns(3)
                    st.caption("*(民調可做多次增加準確性)*")
                    if b1.button("小民調 ($5)", key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5); st.rerun()
                    if b2.button("中民調 ($10)", key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10); st.rerun()
                    if b3.button("大民調 ($20)", key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20); st.rerun()
            else: 
                st.markdown(f"## {party.name} {crown} {role_badge}")
                st.markdown(f"### 支持度: {disp_sup}")
                st.markdown("#### 🏛️ 戰略情報中心")
                render_strategic_intelligence_center(party, cfg, is_self=False, blur=blur)

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    st.markdown(f"<h3>公告衰退: {plan['claimed_decay']:.2f} | 目標 GDP 成長: {plan['target_gdp_growth']}%</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3>標案利潤: {plan['r_value']:.2f} | 標案達標付款: {plan['target_h_fund']}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3>總標案需求: {plan['total_funds']} | 監管出資: {plan['r_pays']} | 執行出資: {plan['h_pays']}</h3>", unsafe_allow_html=True)
    
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
    
    gain = formulas.calc_log_gain(invest - maint)
    next_val = max(3.0, current_val + gain) if invest >= maint else max(3.0, current_val - ((maint - invest) * 0.02))
    next_maint = max(0, (next_val - 3.0) * cfg['MAINTENANCE_RATE'])
    
    if invest < maint:
        st.caption(f"📉 投入不足維護 (${int(maint)})，降至: {next_val*10:.1f}% | 明年維護 ${int(next_maint)}")
    else:
        st.caption(f"📈 已達維護 (${int(maint)})，升至: {min(100.0, next_val*10):.1f}% | 明年維護 ${int(next_maint)}")
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
