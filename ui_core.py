# ==========================================
# ui_core.py
# ==========================================
import streamlit as st
import config
import formulas

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_debug_ui(game, cfg):
    with st.sidebar.expander("🛠️ 底層引擎與數學監控 (Debug UI)", expanded=False):
        st.markdown("### 經濟運作公式")
        st.latex(r"T = GDP \times 20\%")
        st.write(f"下年度可用總預算 (T): {game.budget_t:.0f}")
        st.write(f"待發放尾款 (H/R/殘值): {game.pending_payouts['H']:.0f} / {game.pending_payouts['R']:.0f} / {game.pending_payouts['R_residual']:.0f}")

def render_global_settings(cfg, game):
    st.sidebar.title("🎛️ 控制台")
    render_debug_ui(game, cfg)
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
        st.markdown(f"**今年總預算池 (T):** `{game.budget_t:.0f}`")
        st.markdown(f"**H-Index 待發獎勵:** `{game.pending_payouts['H']:.0f}`")
        st.markdown(f"**監管沒收與殘值:** `{(game.pending_payouts['R'] + game.pending_payouts['R_residual']):.0f}`")

    with c3:
        fc = view_party.current_forecast
        st.markdown(f"### 🕵️ 智庫準確度估算")
        st.write(f"經濟預估: {config.get_economic_forecast_text(fc)}(估計: -{fc:.2f})")
        if rep:
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            st.write(f"(去年檢討: 誤差值 {diff:.2f} / 實真 -{rep['real_decay']:.2f})")
        else:
            st.write("\n(尚無去年歷史資料以供檢討)")

    with c4:
        st.markdown("### 📊 財報")
        st.write(f"可用淨資產: {int(view_party.wealth)}")
        if rep:
            is_h = view_party.name == rep['h_party_name']
            real_inc = rep['h_inc'] if is_h else rep['r_inc']
            st.write(f"去年淨收益總結: **{real_inc:.0f}**")
    st.markdown("---")

def render_sidebar_intel_audit(game, view_party, cfg):
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    st.markdown("---")
    st.title("🕵️ 情報處 - 對手機構指標")
    
    blur = max(0.0, 1.0 - (view_party.investigate_ability / max(0.1, opp.stealth_ability)))
    acc = int((1.0 - blur)*100) if not st.session_state.get('god_mode') else 100
    st.progress(acc/100.0, text=f"準確度: {acc}%")
    
    if opp.last_acts:
        st.write("📝 **對手去年各項花費估算:**")
        st.write(f"- 媒體與造勢: {opp.last_acts.get('media', 0) + opp.last_acts.get('camp', 0):.0f}")
        st.write(f"- 煽動與教育: {opp.last_acts.get('incite', 0) + abs(opp.last_acts.get('edu_amt', 0)):.0f}")
        st.write(f"- 司法與其他: {opp.last_acts.get('judicial', 0):.0f}")
    else:
        st.write("尚無對手行動數據。")

    st.markdown("---")
    st.title("📈 審計處 - 自身機構指標及花費")
    if view_party.last_acts:
        st.write("📝 **自身去年各項花費:**")
        st.write(f"- 媒體操控: {view_party.last_acts.get('media', 0):.0f} | 舉辦競選: {view_party.last_acts.get('camp', 0):.0f}")
        st.write(f"- 煽動情緒: {view_party.last_acts.get('incite', 0):.0f} | 教育方針: {abs(view_party.last_acts.get('edu_amt', 0)):.0f}")
        st.write(f"- 司法審查: {view_party.last_acts.get('judicial', 0):.0f}")
        st.write(f"- 部門升級總投: {view_party.last_acts.get('inv_pre',0)+view_party.last_acts.get('inv_med',0)+view_party.last_acts.get('inv_bld',0)+view_party.last_acts.get('inv_inv',0)+view_party.last_acts.get('inv_stl',0):.0f}")
    else:
        st.write("尚無去年花費紀錄。")

def render_message_board(game):
    if st.session_state.get('news_flash'):
        st.warning(st.session_state.news_flash)
        st.session_state.news_flash = None

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
                if party.latest_poll is not None: disp_sup = f"{party.latest_poll:.1f}%(最新民調)"
                else: disp_sup = "??? (需作民調)"
            
            st.markdown(f"### 📊 支持度: {disp_sup}")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write(f"**公告衰退:** {plan['claimed_decay']:.2f} | **目標 GDP 成長:** {plan['target_gdp_growth']}%")
        r_pct = (plan['r_pays'] / max(1, plan['c_funds'])) * 100
        h_pct = (plan['h_pays'] / max(1, plan['c_funds'])) * 100
        st.write(f"**監管出資:** {plan['r_pays']} ({r_pct:.1f}%) / **總額:** {plan['c_funds']} / **執行出資:** {plan['h_pays']} ({h_pct:.1f}%)")
        st.write(f"**標案實質成本 (D):** {plan['d_cost']}")
        
    with c2:
        new_gdp, h_est, r_est, h_roi, r_roi, sup_shift = formulas.calc_preview(
            cfg, game.gdp, game.budget_t, plan['c_funds'], view_party.current_forecast, game.h_role_party.build_ability
        )
        my_is_h = (view_party.name == game.h_role_party.name)
        my_net, my_roi_disp = (h_est - plan['h_pays'], h_roi) if my_is_h else (r_est - plan['r_pays'], r_roi)
        opp_net, opp_roi_disp = (r_est - plan['r_pays'], r_roi) if my_is_h else (h_est - plan['h_pays'], h_roi)
        
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
