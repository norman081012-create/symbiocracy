# ui_core.py
import streamlit as st
import config
import formulas
import engine

def render_debug_ui(game, cfg):
    with st.sidebar.expander("🛠️ 底層引擎與數學監控 (Debug UI)", expanded=False):
        st.markdown("### 經濟運作公式")
        st.latex(r"T = GDP \times 20\%")
        st.latex(r"Residual = T - A_b - A_r - C_{funds}")
        st.latex(r"L_{gdp} = GDP \times (R_{decay} \times 0.072 / 0.5)")
        st.latex(r"C_{net} = Gross - (L_{gdp} \times 5.0)")
        st.latex(r"H_{idx} = C_{net} / C_{funds}")
        
        st.markdown("### 當前全域變數")
        st.write(f"下年度可用總預算 (T): {game.budget_t:.0f}")
        st.write(f"待發放尾款 (H/R/殘值): {game.pending_payouts['H']:.0f} / {game.pending_payouts['R']:.0f} / {game.pending_payouts['R_residual']:.0f}")

def render_global_settings(cfg, game):
    st.sidebar.title("🎛️ 控制台")
    render_debug_ui(game, cfg)
    # ... 原有設定邏輯 ...
    sync_party_names(game, cfg)

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    st.header("👤 玩家頁面")
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    
    # 高亮當前操作者的顏色
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

            # 確保選舉年永遠顯示真實支持度
            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
            else:
                if party.latest_poll is not None:
                    disp_sup = f"{party.latest_poll:.1f}%(最新民調)"
                else:
                    disp_sup = "??? (需作民調)"
            
            st.markdown(f"### 📊 支持度: {disp_sup}")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write(f"**公告衰退:** {plan['claimed_decay']:.2f}")
        st.write(f"**投標資金 (C):** {plan['c_funds']}")
        st.write(f"**標案實質成本 (D):** {plan['d_cost']}")
        
    with c2:
        new_gdp, h_est, r_est, h_roi, r_roi, sup_shift = formulas.calc_preview(
            cfg, game.gdp, game.budget_t, plan['c_funds'], view_party.current_forecast, game.h_role_party.build_ability
        )
        
        my_is_h = (view_party.name == game.h_role_party.name)
        my_net, my_roi_disp = (h_est, h_roi) if my_is_h else (r_est, r_roi)
        opp_net, opp_roi_disp = (r_est, r_roi) if my_is_h else (h_est, h_roi)
        
        diff = abs(plan['claimed_decay'] - view_party.current_forecast)
        if diff > 0.3: risk_txt = "🔴 風險極高 (數據嚴重偏離預估)"
        elif diff > 0.1: risk_txt = "🟡 風險中等 (數據略有出入)"
        else: risk_txt = "🟢 風險極低 (基準比對)"

        # 鎖死要求的智庫格式
        st.markdown(f"**📊 智庫評估報告 (依自己預測: -{view_party.current_forecast:.2f})**")
        st.markdown(f"1. 我方預估收益: {my_net:.0f} (ROI: {my_roi_disp:+.1f}%)")
        st.markdown(f"2. 對方預估收益: {opp_net:.0f} (ROI: {opp_roi_disp:+.1f}%)")
        st.markdown(f"3. 支持度預估: {sup_shift:+.2f}%")
        st.markdown(f"4. 預期 GDP: {game.gdp:.0f} ➔ {new_gdp:.0f} ({((new_gdp-game.gdp)/max(1.0,game.gdp))*100:+.2f}%)")
        st.markdown(f"5. 衰退值判讀: {risk_txt} (公告值與估值差異: {diff:.2f})")

def ability_investment_ui(label, key, current_val, invested, wealth, cfg):
    """新的投資池介面"""
    target_pct = st.slider(f"{label} 目標能力 (當前: {current_val:.1f})", 0.0, 100.0, float(current_val), 5.0, key=f"tgt_{key}")
    invest_amt = st.number_input(f"投入資金 (可用: {wealth:.0f})", 0.0, float(wealth), 0.0, step=10.0, key=f"inv_{key}")
    
    cost, years = formulas.get_upgrade_cost_and_time(current_val, target_pct, cfg)
    maint = formulas.get_maintenance_fee(current_val, cfg)
    
    if target_pct > current_val:
        st.caption(f"📈 升級總需: ${int(cost)} | 目前已投: ${int(invested)} | 以此速約 {years} 年完成 | 維護費: ${int(maint)}")
    elif invest_amt == 0:
        st.caption(f"📉 未投入維護，能力將自然下降 | 維護費免除")
    
    return invest_amt, target_pct
