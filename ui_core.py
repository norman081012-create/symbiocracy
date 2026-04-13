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

def render_dashboard(game, view_party, cfg):
    rep = game.last_year_report
    st.markdown("---")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("### 🌐 國家總體現況")
        san_chg = (game.sanity - rep['old_san']) if rep else 0
        st.markdown(f"**資訊辨識:** `{config.get_civic_index_text(game.sanity)}` *(變動: {san_chg:+.1f})*")
        emo_chg = game.emotion - rep['old_emo'] if rep else 0
        st.markdown(f"**選民情緒:** `{config.get_emotion_text(game.emotion)}` *(變動: {emo_chg:+.1f})*")
        gdp_chg = game.gdp - rep['old_gdp'] if rep else 0
        st.markdown(f"**當前 GDP:** `{game.gdp:.1f}` *(變動: {gdp_chg:+.0f})*")

    with c2:
        st.markdown("### 💰 系統資金與待付款")
        st.markdown(f"**下年度可用總預算 (T):** `{game.budget_t:.0f}`")
        st.markdown(f"**H-Index 待發獎勵:** `{game.pending_payouts['H']:.0f}`")
        st.markdown(f"**監管沒收與殘值待發:** `{(game.pending_payouts['R'] + game.pending_payouts['R_residual']):.0f}`")

    with c3:
        fc = view_party.current_forecast
        acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
        st.markdown(f"### 🕵️ 智庫 準確度: {acc}%")
        st.write(f"經濟預估: {config.get_economic_forecast_text(fc)}(預估衰退值: -{fc:.2f})")
        if rep:
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            eval_txt = config.get_thinktank_eval(view_party.predict_ability, diff)
            st.write(f"\n({cfg['CALENDAR_NAME']} {game.year-1} 年度內部檢討報告: \n")
            st.write(f"{eval_txt}\n")
            st.write(f"判讀誤差值: {diff:.2f} / 實真: -{rep['real_decay']:.2f} / 估值: -{rep['view_party_forecast']:.2f})")
        else:
            st.write("\n(尚無去年歷史資料以供檢討)")

    with c4:
        st.markdown("### 📊 財報")
        total_maint = sum([formulas.get_maintenance_fee(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
        st.write(f"可用淨資產: {int(view_party.wealth)} (已扣維護: {int(total_maint)})")
            
        if rep:
            my_is_h = view_party.name == rep['h_party_name']
            real_inc = rep['h_inc'] if my_is_h else rep['r_inc']
            pol_cost = view_party.last_acts.get('policy', 0)
            
            st.write(f"去年淨利入帳: {real_inc:.0f}")
            st.write(f"去年施政與投資總額: {pol_cost:.0f}")
    st.markdown("---")

def render_message_board(game):
    if st.session_state.get('news_flash'):
        st.warning(st.session_state.news_flash)
        st.session_state.news_flash = None
        
    if game.phase == 1:
        if game.year == 1: st.info("📢 **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商。")
        elif game.last_year_report: st.info(f"📢 **【年度通報】** 新的一年開始了，請盡快展開預算與目標協商。")
    elif game.phase == 2:
        st.info("📢 **【年度通報】** 法案已通過，請分配黨產資金進行內部升級、競選造勢與媒體攻防。")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    st.header("👤 玩家頁面")
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    
    a_bg = f"{cfg['PARTY_A_COLOR']}40" if game.proposing_party.name == game.party_A.name else f"{cfg['PARTY_A_COLOR']}10"
    b_bg = f"{cfg['PARTY_B_COLOR']}40" if game.proposing_party.name == game.party_B.name else f"{cfg['PARTY_B_COLOR']}10"
    
    st.markdown(f"""
    <style>
    div[data-testid="column"]:nth-child(1) {{ background-color: {a_bg}; padding: 15px; border-radius: 10px; border-left: 5px solid {cfg['PARTY_A_COLOR']}; }}
    div[data-testid="column"]:nth-child(2) {{ background-color: {b_bg}; padding: 15px; border-radius: 10px; border-left: 5px solid {cfg['PARTY_B_COLOR']}; }}
    </style>
    """, unsafe_allow_html=True)

    for col, party in zip([c1, c2], [view_party, opp]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role_badge = "🛡️ [執行系統]" if is_h else "⚖️ [監管系統]"
            is_winner = (game.ruling_party.name == party.name)
            crown_str = cfg.get('CROWN_WINNER', '👑 當權') if is_winner else cfg.get('CROWN_LOSER', '🎯 候選')
            logo = config.get_party_logo(party.name)
            
            eye = "👁️ " if party.name == view_party.name else ""
            st.markdown(f"## {eye}{logo} {party.name} {crown_str}")
            st.markdown(f"#### {role_badge}")

            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
            else:
                if party.latest_poll is not None:
                    best_type = None
                    for t in ['大型', '中型', '小型']:
                        if len(party.poll_history[t]) > 0:
                            best_type = t; break
                    if best_type:
                        avg = sum(party.poll_history[best_type]) / len(party.poll_history[best_type])
                        count = len(party.poll_history[best_type])
                        disp_sup = f"{party.latest_poll:.1f}%(最新民調) ({count}次{best_type}平均: {avg:.1f}%)"
                    else:
                        disp_sup = f"{party.latest_poll:.1f}%(最新民調)"
                else:
                    disp_sup = "??? (需作民調)"
            
            st.markdown(f"### 📊 支持度: {disp_sup}")
            
            if party.name == view_party.name and not is_election_year:
                b1, b2, b3 = st.columns(3)
                if b1.button("小民調 ($5)", key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5); st.rerun()
                if b2.button("中民調 ($10)", key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10); st.rerun()
                if b3.button("大民調 ($20)", key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20); st.rerun()

def render_sidebar_intel_audit(game, view_party, cfg):
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    st.markdown("---")
    st.title("🕵️ 情報處 - 對手機構指標")
    blur = max(0.0, 1.0 - (view_party.investigate_ability / max(0.1, opp.stealth_ability))) if not st.session_state.get('god_mode') else 0.0
    acc = int((1.0 - blur)*100)
    st.progress(1.0 - blur, text=f"準確度: {acc}%")
    rng = random.Random(f"intel_{opp.name}_{game.year}")
    
    st.write(f"智庫: {opp.predict_ability*(1+rng.uniform(-blur, blur)):.1f} | 情報處: {opp.investigate_ability*(1+rng.uniform(-blur, blur)):.1f}")
    st.write(f"黨媒: {opp.media_ability*(1+rng.uniform(-blur, blur)):.1f} | 反情報處: {opp.stealth_ability*(1+rng.uniform(-blur, blur)):.1f}")
    st.write(f"工程處: {opp.build_ability*(1+rng.uniform(-blur, blur)):.1f}")
    
    if opp.last_acts:
        est_pol = opp.last_acts.get('policy', 0) * (1+rng.uniform(-blur, blur))
        st.write(f"📝 **對手去年施政花費估算:** {est_pol:.0f}")

    st.markdown("---")
    st.title("📈 審計處 - 自身機構與花費")
    if view_party.last_acts:
        st.write("📝 **自身去年各項花費:**")
        st.write(f"- 媒體操控: {view_party.last_acts.get('media', 0):.0f} | 舉辦競選: {view_party.last_acts.get('camp', 0):.0f}")
        st.write(f"- 煽動情緒: {view_party.last_acts.get('incite', 0):.0f} | 教育方針: {abs(view_party.last_acts.get('edu_amt', 0)):.0f}")
        st.write(f"- 司法審查: {view_party.last_acts.get('judicial', 0):.0f}")
    else:
        st.write("尚無去年花費紀錄。")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write(f"**公告衰退:** {plan['claimed_decay']:.2f}")
        st.write(f"**投標總額 (C):** {plan['c_funds']}")
        st.write(f"**實質成本 (D):** {plan['d_cost']}")
        
    with c2:
        new_gdp, h_est, r_est, h_roi, r_roi, sup_shift = formulas.calc_preview(
            cfg, game.gdp, game.budget_t, plan['c_funds'], view_party.current_forecast, game.h_role_party.build_ability
        )
        my_is_h = (view_party.name == game.h_role_party.name)
        my_net, my_roi_disp = (h_est, h_roi) if my_is_h else (r_est, r_roi)
        opp_net, opp_roi_disp = (r_est, r_roi) if my_is_h else (h_est, h_roi)
        
        diff = abs(plan['claimed_decay'] - view_party.current_forecast)
        risk_txt = "🔴 風險極高" if diff > 0.3 else "🟡 風險中等" if diff > 0.1 else "🟢 風險極低"

        st.markdown(f"**📊 智庫評估報告 (依自己預測: -{view_party.current_forecast:.2f})**")
        st.markdown(f"1. 我方預估收益: {my_net:.0f} (ROI: {my_roi_disp:+.1f}%)")
        st.markdown(f"2. 對方預估收益: {opp_net:.0f} (ROI: {opp_roi_disp:+.1f}%)")
        st.markdown(f"3. 支持度預估: {sup_shift:+.2f}%")
        st.markdown(f"4. 預期 GDP: {game.gdp:.0f} ➔ {new_gdp:.0f} ({((new_gdp-game.gdp)/max(1.0,game.gdp))*100:+.2f}%)")
        st.markdown(f"5. 衰退值判讀: {risk_txt} (公告差異: {diff:.2f})")

def ability_investment_ui(label, key, current_val, pool_val, wealth, is_h, cfg):
    target_pct = st.slider(f"{label} 目標能力 (當前: {current_val:.1f})", 0.0, 100.0, float(current_val), 5.0, key=f"tgt_{key}")
    invest_amt = st.number_input(f"投入資金 (可用: {wealth:.0f})", 0.0, float(wealth), 0.0, step=10.0, key=f"inv_{key}")
    
    cost_total, years = formulas.get_upgrade_cost_and_time(current_val, target_pct, cfg)
    maint = formulas.get_maintenance_fee(current_val, cfg)
    buff_txt = " *(工程處 1.2倍 Buff 生效中)*" if is_h else ""
    
    if target_pct > current_val:
        st.caption(f"📈 升級總需: ${int(cost_total)} | 目前已投: ${int(pool_val)} | 只要錢投到了就達標{buff_txt} | 維護費: ${int(maint)}")
    elif invest_amt == 0:
        st.caption(f"穩定維持或自然下降 | 維護費: ${int(maint)}")
    
    return invest_amt, target_pct

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
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity'], name="資訊辨識 (0-100)", line=dict(color='purple', width=3)), secondary_y=True)
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
