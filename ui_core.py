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
    
    c1, c2, c3, c4 = st.columns(4)
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
        st.info(f"經濟預估: **{config.get_economic_forecast_text(fc)}**\n*(預估衰退值: -{fc:.2f})*\n準確度: {acc}%")
        
        if rep:
            st.markdown("**=== 判讀結果 ===**")
            st.markdown("**去年真實VS 預估衰退**")
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            st.write(f"結果: {config.get_thinktank_eval(view_party.predict_ability, diff)}")
            st.write(f"真: {rep['real_decay']:.2f} | 估: {rep['view_party_forecast']:.2f}")

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
    total_cost = party.last_acts['policy'] + party.last_acts['legal'] + total_maint
    
    if is_self:
        st.markdown("##### 📊 內部審計局")
        st.write(f"**可用淨資產:** `{party.wealth:.0f}` - `維護成本 {total_maint:.0f}` = **{party.wealth - total_maint:.0f}**")
        
        if party.last_income_real > 0 or party.last_pol_cost > 0 or total_maint > 0:
            net_income = party.last_income_real - party.last_pol_cost - party.last_maint_cost
            st.write(f"**淨利:** 真:{party.last_income_real:.0f} (去年估:{party.last_income_est:.0f}) | 去年政治成本: {party.last_pol_cost:.0f} | 維護成本: {party.last_maint_cost:.0f}")
            st.write(f"**{cfg['CALENDAR_NAME']}(去年)年度收益:** `{party.last_income_real:.0f} - {party.last_pol_cost:.0f} - {party.last_maint_cost:.0f} = {net_income:.0f}`")
    else:
        st.markdown("##### 🕵️ 國家情報局 (對手情資還原)")
        import random
        rng = random.Random(f"intel_{party.name}")
        est_wealth = rng.uniform(max(0, party.wealth * (1 - blur)), party.wealth * (1 + blur))
        est_cost = rng.uniform(max(0, total_cost * (1 - blur)), total_cost * (1 + blur))
        st.write(f"**估算可用資產:** `約 {est_wealth:.0f}` - `維護估算 {total_maint*(1-blur):.0f}` = **約 {est_wealth - total_maint*(1-blur):.0f}**")
        st.progress(1.0 - blur, text=f"情報準確度: {int((1.0 - blur)*100)}%")

def get_poll_str(party):
    if not party.poll_history: return "??? (需作民調)"
    latest = party.poll_history[-1]['result']
    for t in ['大', '中', '小']:
        polls = [p['result'] for p in party.poll_history if p['type'] == t]
        if polls:
            avg = sum(polls) / len(polls)
            return f"{latest:.1f}%(最新民調) ({len(polls)}次{t}型民調平均: {avg:.1f}%)"
    return f"{latest:.1f}%(最新民調)"

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
                disp_sup = f"📊 支持度: {party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
            else:
                disp_sup = f"📊 支持度: {get_poll_str(party)}"
            
            blur = 1.0 - (view_party.investigate_ability / cfg['MAX_ABILITY']) if not god_mode else 0.0

            if party.name == view_party.name: 
                st.markdown(f"## 👁️ {party.name} {crown} {role_badge}")
                st.markdown(f"### {disp_sup}")
                st.markdown("#### 🏛️ 戰略情報中心")
                render_strategic_intelligence_center(party, cfg, is_self=True)
                
                if not is_election_year:
                    st.markdown("<div style='text-align: center'>", unsafe_allow_html=True)
                    st.caption("*(民調可做多次增加準確性)*")
                    b_cols = st.columns([1, 2, 2, 2, 1])
                    if b_cols[1].button("小民調 ($5)", key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5, "小"); st.rerun()
                    if b_cols[2].button("中民調 ($10)", key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10, "中"); st.rerun()
                    if b_cols[3].button("大民調 ($20)", key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20, "大"); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            else: 
                st.markdown(f"## {party.name} {crown} {role_badge}")
                st.markdown(f"### {disp_sup}")
                st.markdown("#### 🏛️ 戰略情報中心")
                render_strategic_intelligence_center(party, cfg, is_self=False, blur=blur)

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    st.markdown(f"**公告衰退:** {plan['claimed_decay']:.2f} | **目標 GDP 成長:** {plan['target_gdp_growth']}%")
    st.markdown(f"**標案利潤:** {plan['r_value']:.2f} | **標案達標付款:** {plan['target_h_fund']}")
    
    st.markdown(f"""
    <div style="font-family: sans-serif; margin: 10px 0;">
        <span style="font-size: 1.2em;">監管出資 </span>
        <span style="font-size: 1.5em; font-weight: bold;">{plan['r_pays']}</span>
        <span style="font-size: 1.0em;"> ({(plan['r_pays']/max(1, plan['total_funds'])*100):.
