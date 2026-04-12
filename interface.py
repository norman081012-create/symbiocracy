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

def render_global_settings(cfg, game):
    st.sidebar.title("⚙️ 全域變數控制台")
    with st.sidebar.expander("📝 動態調整遊戲參數", expanded=False):
        for key, default_val in content.DEFAULT_CONFIG.items():
            label = content.CONFIG_TRANSLATIONS.get(key, key)
            if isinstance(default_val, float): cfg[key] = st.number_input(label, value=float(cfg[key]), step=0.1, format="%.2f", key=f"cfg_{key}")
            elif isinstance(default_val, int): cfg[key] = st.number_input(label, value=int(cfg[key]), step=1, key=f"cfg_{key}")
            elif isinstance(default_val, str): cfg[key] = st.text_input(label, value=str(cfg[key]), key=f"cfg_{key}")
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_dashboard(game, view_party, cfg):
    st.markdown(f"**年份: {game.year} / {cfg['END_YEAR']} &nbsp;&nbsp;|&nbsp;&nbsp; {content.get_election_icon(game.year, cfg['ELECTION_CYCLE'])}**")
    
    show_last = st.toggle("顯示去年預估對比", value=False) if game.year > 1 else False
    rep = game.last_year_report
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("#### 🌐 國家總體現況")
        san_val, emo_val = game.sanity * 100, game.emotion
        s_diff = f" ({san_val - (rep['old_san']*100):+.1f})" if rep and show_last else ""
        e_diff = f" ({emo_val - rep['old_emo']:+.1f})" if rep and show_last else ""
        st.write(f"**公民識讀:** {content.get_civic_index_text(game.sanity)}{s_diff}")
        st.write(f"**選民情緒:** {content.get_emotion_text(game.emotion)}{e_diff}")
        
        g_diff = f" ({game.gdp - rep['old_gdp']:+.0f})" if rep and show_last else ""
        st.write(f"**當前 GDP:** `{game.gdp:.0f}`{g_diff}")
        if rep and show_last: st.caption(f"判定: {content.get_performance_eval(game.gdp, rep['target_gdp'])}")

    with c2:
        st.markdown("#### 💰 執行系統資源")
        b_diff = f" ({game.total_budget - rep['old_budg']:+.0f})" if rep and show_last else ""
        h_diff = f" ({game.h_fund - rep['old_h_fund']:+.0f})" if rep and show_last else ""
        st.write(f"**總預算池:** `{game.total_budget:.0f}`{b_diff}")
        st.write(f"**獎勵基金:** `{game.h_fund:.0f}`{h_diff}")
        if rep and show_last: st.caption(f"判定: {content.get_performance_eval(game.h_fund, rep['target_h_fund'])}")

    with c3:
        st.markdown("#### 🕵️ 智庫機密通報")
        fc = view_party.current_forecast
        acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
        st.info(f"經濟預估: {content.get_economic_forecast_text(fc)}\n\n*(衰退值: -{fc:.2f})*\n\n準確度: {acc}%")

    with c4:
        st.markdown("#### 📈 智庫檢討")
        if rep:
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            st.write(f"**總評:** {content.get_thinktank_eval(view_party.predict_ability, diff)}")
        else: st.info("新任期暫無資料")
    st.markdown("---")

def render_message_board(game):
    rep = game.last_year_report
    if game.year == 1:
        st.info("🏛️ **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商，確立今年的施政方向。")
    elif game.phase == 1 and rep:
        strategy = "建議策略: 監管系統應在標案利潤與嚴格度間取得平衡，避免激怒執行系統引發倒閣。" if game.proposing_party.name == game.r_role_party.name else "建議策略: 執行系統應檢視標案是否具備足夠 ROI，若利潤太薄，可考慮退回或提最後通牒。"
        st.info(f"🏛️ **【年度通報】** {strategy}")
    elif game.phase == 2:
        st.info("🏛️ **【年度通報】** 預算案已底定，各部會進入執行階段。請妥善調配政策與升級資源。")
        
    if st.session_state.get('news_flash'):
        st.warning(f"🗞️ **新聞快訊**: {st.session_state.news_flash}")
        st.session_state.news_flash = None
        
    if rep:
        with st.expander("📊 去年財報與實績對比", expanded=False):
            c1, c2, c3 = st.columns(3)
            my_is_h = game.proposing_party.name == rep['h_party_name']
            r_inc, e_inc = (rep['h_inc'], rep['est_h_inc']) if my_is_h else (rep['r_inc'], rep['est_r_inc'])
            r_sup, e_sup = (rep['h_sup_shift'], rep['est_h_sup_shift']) if my_is_h else (rep['r_sup_shift'], rep['est_r_sup_shift'])
            c1.write(f"**真實衰退:** `{rep['real_decay']:.2f}`\n\n**我方原估:** `{rep['view_party_forecast']:.2f}`")
            c2.write(f"**去年實質淨利:** `${r_inc:.0f}`\n\n**去年原估淨利:** `${e_inc:.0f}`")
            c3.write(f"**實質支持度變化:** `{r_sup:+.2f}%`\n\n**原估支持度變化:** `{e_sup:+.2f}%`")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    for col, party in zip([c1, c2], [view_party, opp]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role = "🛡️ **[執行系統]**" if is_h else "⚖️ **[監管系統]**"
            is_win = (game.ruling_party.name == party.name)
            crown = "👑" if is_win else ""
            
            if is_election_year or god_mode: disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_win else " 💀(落選)")
            else:
                if party.current_poll_result is not None: disp_sup = f"📊 預估: {party.current_poll_result:.1f}%"
                else: disp_sup = "??? (需作民調)"
            
            blur = 1.0 - (view_party.predict_ability / cfg['MAX_ABILITY']) if not god_mode else 0.0
            rng = random.Random(f"st_{game.year}_{party.name}_{view_party.name}")
            fog_w = rng.uniform(max(0, party.wealth * (1 - blur)), party.wealth * (1 + blur))
            disp_w = f"{party.wealth:.0f}" if (party.name == view_party.name or god_mode) else f"估算約 {fog_w:.0f}"

            if party.name == view_party.name: 
                st.success(f"### 👁️ {party.name} {crown} {role}\n**黨產:** {disp_w} | **支持度:** {disp_sup}")
                if not is_election_year:
                    b1, b2, b3 = st.columns(3)
                    if b1.button("小民調 ($5)", key=f"p1_{party.name}"): formulas.execute_poll(game, view_party, 5); st.rerun()
                    if b2.button("中民調 ($10)", key=f"p2_{party.name}"): formulas.execute_poll(game, view_party, 10); st.rerun()
                    if b3.button("大民調 ($20)", key=f"p3_{party.name}"): formulas.execute_poll(game, view_party, 20); st.rerun()
            else: 
                st.info(f"### {party.name} {crown} {role}\n**黨產:** {disp_w} | **支持度:** {disp_sup}")
    st.markdown("---")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    st.write(f"**公告衰退:** `{plan['claimed_decay']:.2f}` | **目標 GDP 成長:** `{plan['target_gdp_growth']}%`")
    st.write(f"**標案利潤(嚴格度):** `{plan['r_value']:.2f}` | **標案達標付款:** `{plan['target_h_fund']}`")
    st.write(f"**總標案需求:** `{plan['total_funds']}` | **監管系統出資:** `{plan['r_pays']}`")

def ability_slider(label, key, current_val, wealth, cfg):
    maint = max(0, (current_val - 3.0) * cfg['MAINTENANCE_RATE'])
    default_val = min(int(maint), int(wealth))
    invest = st.slider(f"{label} (當前: {current_val*10:.1f}%)", 0, int(wealth), default_val, key=key)
    next_val, req_maint, next_maint = formulas.get_ability_preview(current_val, invest, cfg)
    
    if invest < maint:
        st.caption(f"📉 投入不足維護費 (${int(maint)})，預計降至: {next_val*10:.1f}% | 下期預計維護費: ${int(next_maint)}")
    else:
        st.caption(f"📈 已達維護費 (${int(maint)})，預計升至: {next_val*10:.1f}% | 下期預計維護費: ${int(next_maint)}")
    return invest

def render_endgame_charts(history_data, cfg):
    st.balloons()
    st.title("🏁 遊戲結束！共生內閣軌跡總結算")
    df = pd.DataFrame(history_data)

    st.subheader("📊 1. 總體經濟與公民識讀指數走勢")
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['
