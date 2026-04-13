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
    game.party_A.name = cfg['PARTY_A_NAME']
    game.party_B.name = cfg['PARTY_B_NAME']

def render_global_settings(cfg, game):
    st.sidebar.title("🎛️ 控制台")
    with st.sidebar.expander("📝 參數調整(即時)", expanded=False):
        for key, default_val in config.DEFAULT_CONFIG.items():
            label = config.CONFIG_TRANSLATIONS.get(key, key)
            if 'COLOR' in key: 
                cfg[key] = st.color_picker(label, value=cfg[key], key=f"cfg_{key}")
            elif isinstance(default_val, float): 
                cfg[key] = st.number_input(label, value=float(cfg[key]), step=0.1, format="%.2f", key=f"cfg_{key}")
            elif isinstance(default_val, int): 
                cfg[key] = st.number_input(label, value=int(cfg[key]), step=1, key=f"cfg_{key}")
            elif isinstance(default_val, str): 
                cfg[key] = st.text_input(label, value=str(cfg[key]), key=f"cfg_{key}")
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
            st.markdown(f"**當前 GDP:** `{disp_gdp:.1f}` *(變動: {disp_gdp - rep['old_gdp'] if rep else 0:+.0f})*")

    with c2:
        st.markdown("### 💰 執行系統資源")
        if game.year == 1 and not is_preview: 
            st.info("首年重整中，尚未配發獎勵。")
        else:
            current_h_ratio = (disp_h_fund / disp_budg) * 100 if disp_budg > 0 else 50
            st.markdown(f"**總預算池:** `{disp_budg:.0f}` *(變動: {disp_budg - rep['old_budg'] if rep else 0:+.0f})*")
            st.markdown(f"**獎勵基金:** `{disp_h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*")

    with c3:
        st.markdown("### 🕵️ 智庫")
        fc = view_party.current_forecast
        acc = min(100, int((view_party.depts['predict'].eff / cfg['MAX_EFFICIENCY']) * 100))
        st.info(f"經濟預估: {config.get_economic_forecast_text(fc)}\n\n(預估衰退值: -{fc:.2f})\n\n準確度: {acc}%")
        if rep:
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            # 將 0-100 的效率轉回 0-10 供評價文字判斷
            eval_txt = config.get_thinktank_eval(view_party.depts['predict'].eff / 10.0, diff)
            st.markdown(f"**判讀結果:** {eval_txt}")
            st.markdown(f"**去年真實VS預估衰退:** 真: -{rep['real_decay']:.2f} / 估: -{rep['view_party_forecast']:.2f}")

    with c4:
        if game.phase == 1:
            st.markdown("### 📊 財報")
            total_maint = sum([formulas.get_ability_maintenance(dept, cfg) for dept in view_party.depts.values()])
            st.write(f"可用淨資產: {int(view_party.wealth + total_maint)} - 維護成本: {int(total_maint)} = **{int(view_party.wealth)}**")
            
            if rep:
                my_is_h = view_party.name == rep['h_party_name']
                real_inc = rep['h_inc'] if my_is_h else rep['r_inc']
                est_inc = rep['est_h_inc'] if my_is_h else rep['est_r_inc']
                pol_cost = view_party.last_acts.get('policy', 0)
                
                st.write(f"淨利: 真:{real_inc:.0f} (去年估:{est_inc:.0f})")
                st.write(f"去年政治成本: {pol_cost:.0f} 維護成本: {total_maint:.0f}")
                final_profit = real_inc - pol_cost - total_maint
                st.write(f"{cfg['CALENDAR_NAME']} {game.year-1} 年度收益: {real_inc:.0f} - {pol_cost:.0f} - {total_maint:.0f} = **{final_profit:.0f}**")
            else: 
                st.write("尚無去年財報資料。")
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
        if game.year == 1: 
            st.info("📢 **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商。")
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
            crown = "👑 當權派" if is_winner else "🎯 在野派"
            logo = config.get_party_logo(party.name)
            
            eye = "👁️ " if party.name == view_party.name else ""
            st.markdown(f"## {eye}{logo} {party.name} {crown}")
            st.markdown(f"#### {role_badge}")

            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
            else:
                if party.latest_poll is not None:
                    best_type = None
                    for t in ['大型', '中型', '小型']:
                        if len(party.poll_history[t]) > 0:
                            best_type = t
                            break
                    if best_type:
                        avg = sum(party.poll_history[best_type]) / len(party.poll_history[best_type])
                        count = len(party.poll_history[best_type])
                        disp_sup = f"{party.latest_poll:.1f}%(最新民調) ({count}次{best_type}民調平均: {avg:.1f}%)"
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
    st.title("🕵️ 情報處")
    
    blur = max(0.0, 1.0 - (view_party.depts['investigate'].eff / max(0.1, opp.depts['stealth'].eff))) if not st.session_state.get('god_mode') else 0.0
    acc = int((1.0 - blur)*100)
    st.progress(1.0 - blur, text=f"情報準確度: {acc}%")
    rng = random.Random(f"intel_{opp.name}_{game.year}")
    
    with st.expander("對手各部門效率", expanded=True):
        st.write(f"建設效率: {opp.depts['build'].eff*(1+rng.uniform(-blur, blur)):.1f}%")
        st.write(f"調查效率: {opp.depts['investigate'].eff*(1+rng.uniform(-blur, blur)):.1f}%")
        st.write(f"教育效率: {opp.depts['edu'].eff*(1+rng.uniform(-blur, blur)):.1f}%")
        st.write(f"媒體效率: {opp.depts['media'].eff*(1+rng.uniform(-blur, blur)):.1f}%")
        st.write(f"隱密效率: {opp.depts['stealth'].eff*(1+rng.uniform(-blur, blur)):.1f}%")
    with st.expander("對手去年政治花費"):
        st.write(f"政策投入總額: {opp.last_acts.get('policy',0)*(1+rng.uniform(-blur, blur)):.0f}")

    st.markdown("---")
    st.title("📈 審計處")
    total_maint = sum([formulas.get_ability_maintenance(dept, cfg) for dept in view_party.depts.values()])
    with st.expander("自身各部門效率及維護費", expanded=True):
        st.write(f"建設:{view_party.depts['build'].eff:.1f}% | 調查:{view_party.depts['investigate'].eff:.1f}%")
        st.write(f"教育:{view_party.depts['edu'].eff:.1f}% | 媒體:{view_party.depts['media'].eff:.1f}%")
        st.write(f"預測:{view_party.depts['predict'].eff:.1f}% | 隱密:{view_party.depts['stealth'].eff:.1f}%")
        st.write(f"**明年維護費估算:** -${total_maint:.0f}")
    with st.expander("自身去年花費"):
        st.write(f"政治花費: ${view_party.last_acts.get('policy',0):.0f}")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    st.write(f"公告衰退: {plan['claimed_decay']:.2f} | 目標 GDP 成長: {plan['target_gdp_growth']}%")
    st.write(f"總額: {plan['total_funds']} (監管出資: {plan['r_pays']} | 執行出資: {plan['h_pays']})")

def add_event_vlines(fig, history_df):
    for _, row in history_df.iterrows():
        y = row['Year']
        if row['Is_Swap']: 
            fig.add_vline(x=y, line_dash="dot", line_color="red", annotation_text="倒閣!", annotation_position="top left")
        if row['Is_Election']: 
            fig.add_vline(x=y, line_dash="dash", line_color="green", annotation_text="選舉", annotation_position="bottom right")

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

def render_debug_panel(game, cfg):
    with st.expander("⚙️ 遊戲底層引擎與數學監控 (Debug UI)", expanded=False):
        st.markdown("### 內部數值")
        st.code(f"""
[環境物理]
真實衰退率 = {game.current_real_decay:.3f}
GDP = {game.gdp:.1f}
總預算 = {game.total_budget:.1f}
H系統獎勵池 = {game.h_fund:.1f}

[社會心理]
資訊辨識 (Sanity) = {game.sanity:.3f}
選民情緒 (Emotion) = {game.emotion:.1f}
民生權重 = {cfg['LIVELIHOOD_WEIGHT']}
        """)
        st.markdown("### 運作公式")
        st.markdown("""
        - **Sanity 變化** = (正面教育資金 - 愚化資金) * (教育效率%) * 0.002
        - **Emotion 變化** = -(GDP成長率 * 民生權重 * (1 - Sanity)) + (煽動資金 * 媒體效率% * 0.5)
        - **升級花費** = (目標效率 - 當前效率) * UPGRADE_COST_PER_PCT
        - **降級機制** = 每年自動衰退設定之%，維護費即刻降低
        """)
