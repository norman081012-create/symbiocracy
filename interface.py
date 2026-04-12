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

def render_think_tank_toast(view_party, acc_percent, fc_val, phase):
    # Phase 2 不顯示智庫推估
    if phase == 1:
        st.info(f"🕵️ **👁️ 智庫機密通報** | 經濟預估: {content.get_economic_forecast_text(fc_val)} (衰退參數: -{fc_val:.2f}) | 報告準確度: {acc_percent}%")

def render_status_bar(game, view_party, cfg):
    st.markdown("---")
    
    show_last_year = st.toggle("顯示去年預估與檢討", value=True) if game.year > 1 else False

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("🌐 國家總體現況")
        st.markdown(f"**公民識讀指數:** `{content.get_civic_index_text(game.sanity)}`")
        st.markdown(f"**選民情緒參數:** `{content.get_emotion_text(game.emotion)}`")
        
        rep = game.last_year_report
        
        if game.phase == 1:
            if rep and show_last_year:
                gdp_change = ((game.gdp - rep['old_gdp']) / max(1.0, rep['old_gdp'])) * 100
                st.markdown(f"**GDP:** `{game.gdp:.1f}` *(年變動: {gdp_change:+.2f}%)*")
                st.caption(f"↳ 去年目標: 成長 {rep['target_gdp_growth']}%")
                if rep['r_perf'] >= 0: st.success("✅ GDP 達標。")
                else: st.error("📉 GDP 未達標！")
            else:
                st.markdown(f"**GDP:** `{game.gdp:.1f}`")
        elif game.phase == 2:
            # Phase 2 顯示動態預估
            d = st.session_state.turn_data
            rp, hp = game.r_role_party, game.h_role_party
            ha = st.session_state.get(f"{hp.name}_acts")
            
            p_est_gdp = game.gdp
            if ha:
                 corr_amt = d.get('total_funds', 0) * (ha.get('corr',0) / 100.0)
                 act_build = d.get('total_funds', 0) - corr_amt
                 gdp_bst = (act_build * hp.build_ability) / cfg['BUILD_DIFF']
                 p_est_gdp = max(0.0, game.gdp + gdp_bst - (view_party.current_forecast * 1000))
            else:
                 p_est_gdp = game.gdp - (view_party.current_forecast * 1000) # 簡化預估
            
            gdp_change_pct = ((p_est_gdp - game.gdp)/max(1.0, game.gdp))*100
            st.markdown(f"**GDP:** `{game.gdp:.1f}` *(智庫預估季末: {p_est_gdp:.0f} / {gdp_change_pct:+.2f}%)*")

    with c2:
        st.subheader("💰 執行系統資源")
        if game.year == 1:
            st.info("首年預算重整中，尚未配發行政獎勵基金。")
        else:
            current_h_ratio = (game.h_fund / game.total_budget) * 100 if game.total_budget > 0 else 50
            st.markdown(f"**總預算池:** `{game.total_budget:.0f}`")
            st.markdown(f"**執行獎勵基金:** `{game.h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*")
            
            if game.phase == 1:
                if rep and show_last_year:
                    h_party_name = rep['h_party_name']
                    st.caption(f"↳ 去年 {h_party_name} 績效結算，目標: {rep['target_h_fund']:.0f}")
                    h_perf = rep['h_perf']
                    if h_perf >= 0: st.success(f"✅ {h_party_name} 績效達標。")
                    else:
                        if h_perf >= -10: st.warning(f"⚠️ {h_party_name} 勉強及格 (落差 {h_perf:.1f}%)")
                        else: st.error(f"🚨 {h_party_name} 嚴重落後 (落差 {h_perf:.1f}%)")
            elif game.phase == 2:
                st.info("本期專案進行中...")

    with c3:
        if game.phase == 1:
             st.subheader("🕵️ 👁️ 智庫檢討與財報")
             if rep and show_last_year:
                rd = rep['real_decay']; fc = rep['view_party_forecast']
                st.write(f"**真實衰退:** `{rd:.2f}` | **我方原估:** `{fc:.2f}`")
                
                my_is_h = view_party.name == rep['h_party_name']
                my_inc = rep['h_inc'] if my_is_h else rep['r_inc']
                st.write(f"**去年實質淨利:** `${my_inc:.0f}`")

                if abs(fc - rd) > 0.15: st.error("❌ 預估嚴重失準：智庫未能察覺經濟異常。")
                if rep['caught_corruption']: st.error("🚨 貪腐爆雷：執行者貪污遭逮。")
             else:
                st.info("尚無檢討資料。")
        elif game.phase == 2:
             st.subheader("🕵️ 👁️ 智庫機密預測")
             d = st.session_state.turn_data
             rp, hp = game.r_role_party, game.h_role_party
             ra = st.session_state.get(f"{rp.name}_acts")
             ha = st.session_state.get(f"{hp.name}_acts")
             
             if ra and ha:
                  shift = formulas.calc_support_shift(cfg, hp, rp, game.h_fund, game.gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha.get('media',0), ra.get('media',0))
                  my_sup_shift = shift['actual_shift'] if view_party.name == hp.name else -shift['actual_shift']
                  st.info(f"依據當前投入資源推演，預計支持度變化: **{my_sup_shift:+.2f}%**")
             else:
                  st.info("請輸入資源配比以獲取支持度預測。")

    st.markdown("---")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    for col, party in zip([c1, c2], [view_party, opp]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role_badge = "🛡️ **[執行者]**" if is_h else "⚖️ **[調節者]**"
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
    st.write(f"**嚴格度:** `{plan['r_value']:.2f}` | **目標執行獎勵:** `{plan['target_h_fund']}`")
    st.write(f"**總資金需求:** `{plan['total_funds']}` | **調節者出資:** `{plan['r_pays']}`")
    
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
    invest = st.number_input(f"{label} (當前: {current_val*10:.0f}%)", 0, int(wealth), default_val, key=key)
    
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
