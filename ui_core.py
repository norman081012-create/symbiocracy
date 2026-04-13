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
import random

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_global_settings(cfg, game):
    st.sidebar.title("🎛️ 控制台")
    with st.sidebar.expander("📝 參數調整(即時)", expanded=False):
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
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("### 🌐 國家總體現況")
        san_chg = (disp_san - rep['old_san']) * 100 if rep else 0
        st.markdown(f"**資訊辨識:** `{config.get_civic_index_text(disp_san)}` *(變動: {san_chg:+.1f})*")
        emo_chg = disp_emo - rep['old_emo'] if rep else 0
        st.markdown(f"**選民情緒:** `{config.get_emotion_text(disp_emo)}` *(變動: {emo_chg:+.1f})*")
        if is_preview:
            st.markdown(f"**預估 GDP:** `{disp_gdp:.0f}` *(變動: {disp_gdp - game.gdp:+.0f})*")
        else:
            t_gdp = st.session_state.turn_data.get('target_gdp', 0) if game.year > 1 else 0
            st.markdown(f"**當前 GDP:** `{disp_gdp:.1f}` *(變動: {disp_gdp - rep['old_gdp'] if rep else 0:+.0f})*")

    with c2:
        st.markdown("### 💰 執行系統資源")
        if game.year == 1 and not is_preview: st.info("首年重整中，尚未配發獎勵。")
        else:
            current_h_ratio = (disp_h_fund / disp_budg) * 100 if disp_budg > 0 else 50
            st.markdown(f"**總預算池:** `{disp_budg:.0f}` *(變動: {disp_budg - rep['old_budg'] if rep else 0:+.0f})*")
            t_h = st.session_state.turn_data.get('target_h_fund', 0) if game.year > 1 else 0
            st.markdown(f"**獎勵基金:** `{disp_h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*")

    with c3:
        if game.phase == 1:
            st.markdown("### 🕵️ 智庫")
            fc = view_party.current_forecast
            acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
            st.info(f"經濟預估: **{config.get_economic_forecast_text(fc)}**\n\n*(預估衰退值: -{fc:.2f})*\n\n準確度: {acc}%")
        else:
            st.markdown("### 🕵️ 智庫")
            fc = view_party.current_forecast
            acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
            st.info(f"經濟預估: **{config.get_economic_forecast_text(fc)}**\n\n*(預估衰退值: -{fc:.2f})*\n\n準確度: {acc}%")

    with c4:
        if game.phase == 1:
            st.markdown("### 📊 財報")
            total_maint = sum([formulas.get_ability_maintenance(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.edu_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
            st.write(f"**可用淨資產:** {int(view_party.wealth + total_maint)} - 維護成本 = **{int(view_party.wealth)}**")
            if rep:
                my_is_h = view_party.name == rep['h_party_name']
                real_inc = rep['h_inc'] if my_is_h else rep['r_inc']
                est_inc = rep['est_h_inc'] if my_is_h else rep['est_r_inc']
                st.write(f"**淨利:** 真:{real_inc:.0f} (去年估:{est_inc:.0f})")
                st.write(f"**去年政治成本:** {view_party.last_acts.get('policy',0):.0f}")
                st.write(f"**維護成本:** {total_maint:.0f}")
            else: st.write("尚無去年財報資料。")
        else:
            st.markdown("### 📊 智庫/情報預測")
            if is_preview:
                my_is_h = view_party.name == game.h_role_party.name
                my_net = preview_data['h_inc'] if my_is_h else preview_data['r_inc']
                opp_net = preview_data['r_inc'] if my_is_h else preview_data['h_inc']
                my_roi = preview_data['h_roi'] if my_is_h else preview_data['r_roi']
                st.success(f"🟢 **我方預估收益:** {my_net:.0f} (ROI: {my_roi:.1f}%)\n\n支持度變化: {preview_data['my_sup_shift']:+.2f}%")
                st.error(f"🔴 **對手預估收益:** {opp_net:.0f}\n\n支持度變化: {preview_data['opp_sup_shift']:+.2f}%")
    st.markdown("---")

def render_message_board(game):
    if st.session_state.get('news_flash'):
        st.warning(st.session_state.news_flash)
        st.session_state.news_flash = None
        
    if game.phase == 1:
        if game.year == 1: st.info("📢 **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商。")
        elif game.last_year_report:
            st.info(f"📢 **【年度通報】** 新的一年開始了，請盡快展開預算與目標協商。")
    elif game.phase == 2:
        st.info("📢 **【年度通報】** 法案已通過，請分配黨產資金進行內部升級、競選造勢與媒體攻防。")

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
            crown = "👑 當權派" if is_winner else ""
            logo = config.get_party_logo(party.name)
            
            eye = "👁️ " if party.name == view_party.name else ""
            st.markdown(f"## {eye}{logo} {party.name} {crown}")
            st.markdown(f"#### {role_badge}")

            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
            else:
                disp_sup = f"{party.current_poll_result:.1f}%" if party.current_poll_result is not None else "??? (需作民調)"
            
            st.markdown(f"### 📊 支持度: {disp_sup}")
            
            if party.name == view_party.name and not is_election_year:
                b1, b2, b3 = st.columns(3)
                if b1.button("小民調 ($5)", key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5); st.rerun()
                if b2.button("中民調 ($10)", key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10); st.rerun()
                if b3.button("大民調 ($20)", key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20); st.rerun()

def render_sidebar_intel_audit(game, view_party, cfg):
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    st.markdown("---")
    st.title("🕵️ 情報局")
    blur = max(0.0, 1.0 - (view_party.investigate_ability / max(0.1, opp.stealth_ability))) if not st.session_state.get('god_mode') else 0.0
    acc = int((1.0 - blur)*100)
    st.progress(1.0 - blur, text=f"準確度: {acc}%")
    rng = random.Random(f"intel_{opp.name}_{game.year}")
    
    with st.expander("對手各項能力", expanded=True):
        st.write(f"建設能力: {opp.build_ability*(1+rng.uniform(-blur, blur)):.1f}")
        st.write(f"調查能力: {opp.investigate_ability*(1+rng.uniform(-blur, blur)):.1f}")
        st.write(f"教育能力: {opp.edu_ability*(1+rng.uniform(-blur, blur)):.1f}")
        st.write(f"媒體操控: {opp.media_ability*(1+rng.uniform(-blur, blur)):.1f}")
        st.write(f"隱密能力: {opp.stealth_ability*(1+rng.uniform(-blur, blur)):.1f}")
    with st.expander("對手去年各項花費"):
        st.write(f"政策投入: {opp.last_acts.get('policy',0)*(1+rng.uniform(-blur, blur)):.0f}")

    st.markdown("---")
    st.title("📈 審計局")
    total_maint = sum([formulas.get_ability_maintenance(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.edu_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
    with st.expander("自身各項能力及維護費", expanded=True):
        st.write(f"建設:{view_party.build_ability:.1f} | 調查:{view_party.investigate_ability:.1f}")
        st.write(f"教育:{view_party.edu_ability:.1f} | 媒體:{view_party.media_ability:.1f}")
        st.write(f"預測:{view_party.predict_ability:.1f} | 隱密:{view_party.stealth_ability:.1f}")
        st.write(f"**明年維護費估算:** -${total_maint:.0f}")
    with st.expander("自身去年各項花費"):
        st.write(f"政治花費: ${view_party.last_acts.get('policy',0):.0f}")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    st.write(f"公告衰退: {plan['claimed_decay']:.2f} | 目標 GDP 成長: {plan['target_gdp_growth']}%")
    st.write(f"總額: {plan['total_funds']} (監管出資: {plan['r_pays']} | 執行出資: {plan['h_pays']})")

def ability_slider(label, key, current_val, wealth, cfg):
    t_val = st.slider(f"{label} (當前: {current_val:.1f})", 3.0, 10.0, float(current_val), 0.1, key=key)
    cost = formulas.calculate_upgrade_cost(current_val, t_val)
    maint = formulas.get_ability_maintenance(t_val, cfg)
    
    if t_val > current_val:
        st.caption(f"📈 升級花費: ${int(cost)} | 明年維護 ${int(maint)}")
    elif t_val < current_val:
        st.caption(f"📉 免費降級 | 明年維護降至 ${int(maint)}")
    else:
        st.caption(f"穩定維持 | 明年維護 ${int(maint)}")
    return t_val, cost

def add_event_vlines(fig, history_df):
    for _, row in history_df.iterrows():
        y = row['Year']
        if row['Is_Swap']: fig.add_vline(x=y, line_dash="dot", line_color="red", annotation_text="倒閣!", annotation_position="top left")
        if row['Is_Election']: fig.add_vline(x=y, line_dash="dash", line_color="green", annotation_text="選舉", annotation_position="bottom right")

def render_endgame_charts(history_data, cfg):
    st.balloons()
    st.title("🏁 遊戲結束！共生內閣軌跡總結算")
    df = pd.DataFrame(history_data)

    st.subheader("📊 1. 總體經濟與資訊辨識指數走勢")
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['GDP'], name="總 GDP", line=dict(color='blue', width=3)), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity']*100, name="資訊辨識 (0-100)", line=dict(color='purple', width=3)), secondary_y=True)
    fig1.update_yaxes(title_text="GDP (資金)", secondary_y=False)
    fig1.update_yaxes(title_text="辨識指數", secondary_y=True, range=[0, 100])
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
