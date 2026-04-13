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
import i18n

t = i18n.t

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_global_settings(cfg, game):
    st.sidebar.title(t("🎛️ 控制台", "🎛️ Control Panel"))
    
    # 切換語言按鈕
    lang = st.session_state.get('lang', 'EN')
    btn_text = "🌐 切換至中文" if lang == 'EN' else "🌐 Switch to English"
    if st.sidebar.button(btn_text, use_container_width=True):
        st.session_state.lang = 'ZH' if lang == 'EN' else 'EN'
        st.rerun()

    with st.sidebar.expander(t("📝 參數調整(即時)", "📝 Parameter Settings"), expanded=False):
        trans = config.get_config_translations()
        for key, default_val in config.DEFAULT_CONFIG.items():
            label = trans.get(key, key)
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
        st.markdown(t("### 🌐 國家總體現況", "### 🌐 National Status"))
        san_chg = (disp_san - rep['old_san']) if rep else 0
        st.markdown(t(f"**資訊辨識:** `{config.get_civic_index_text(disp_san)}` *(變動: {san_chg:+.1f})*", f"**Civic Literacy:** `{config.get_civic_index_text(disp_san)}` *(Change: {san_chg:+.1f})*"))
        emo_chg = disp_emo - rep['old_emo'] if rep else 0
        st.markdown(t(f"**選民情緒:** `{config.get_emotion_text(disp_emo)}` *(變動: {emo_chg:+.1f})*", f"**Voter Emotion:** `{config.get_emotion_text(disp_emo)}` *(Change: {emo_chg:+.1f})*"))
        if is_preview:
            st.markdown(t(f"**預估 GDP:** `{disp_gdp:.0f}` *(變動: {disp_gdp - game.gdp:+.0f})*", f"**Est. GDP:** `{disp_gdp:.0f}` *(Change: {disp_gdp - game.gdp:+.0f})*"))
        else:
            t_gdp = st.session_state.turn_data.get('target_gdp', 0) if game.year > 1 else 0
            st.markdown(t(f"**當前 GDP:** `{disp_gdp:.1f}` *(變動: {disp_gdp - rep['old_gdp'] if rep else 0:+.0f})*", f"**Current GDP:** `{disp_gdp:.1f}` *(Change: {disp_gdp - rep['old_gdp'] if rep else 0:+.0f})*"))

    with c2:
        st.markdown(t("### 💰 執行系統資源", "### 💰 Executive Resources"))
        if game.year == 1 and not is_preview: st.info(t("首年重整中，尚未配發獎勵。", "Year 1: Reorganizing, no funds distributed yet."))
        else:
            current_h_ratio = (disp_h_fund / disp_budg) * 100 if disp_budg > 0 else 50
            st.markdown(t(f"**總預算池:** `{disp_budg:.0f}` *(變動: {disp_budg - rep['old_budg'] if rep else 0:+.0f})*", f"**Total Budget:** `{disp_budg:.0f}` *(Change: {disp_budg - rep['old_budg'] if rep else 0:+.0f})*"))
            t_h = st.session_state.turn_data.get('target_h_fund', 0) if game.year > 1 else 0
            st.markdown(t(f"**獎勵基金:** `{disp_h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*", f"**Reward Fund:** `{disp_h_fund:.0f}` *(Share: {current_h_ratio:.1f}%)*"))

    with c3:
        fc = view_party.current_forecast
        acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
        st.markdown(t(f"### 🕵️ 智庫 準確度: {acc}%", f"### 🕵️ Think Tank Acc: {acc}%"))
        st.write(t(f"經濟預估: {config.get_economic_forecast_text(fc)}(預估衰退值: -{fc:.2f})", f"Forecast: {config.get_economic_forecast_text(fc)} (Est. Decay: -{fc:.2f})"))
        if rep:
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            eval_txt = config.get_thinktank_eval(view_party.predict_ability, diff)
            st.write(t(f"\n({cfg['CALENDAR_NAME']} {game.year-1} 年度內部檢討報告: \n", f"\n({cfg['CALENDAR_NAME']} Year {game.year-1} Review: \n"))
            st.write(f"{eval_txt}\n")
            st.write(t(f"判讀誤差值: {diff:.2f} / 實真: -{rep['real_decay']:.2f} / 估值: -{rep['view_party_forecast']:.2f})", f"Error: {diff:.2f} / Real: -{rep['real_decay']:.2f} / Est: -{rep['view_party_forecast']:.2f})"))
        else:
            st.write(t("\n(尚無去年歷史資料以供檢討)", "\n(No historical data for review)"))

    with c4:
        if game.phase == 1:
            st.markdown(t("### 📊 財報", "### 📊 Finances"))
            total_maint = sum([formulas.get_ability_maintenance(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
            
            if game.year == 1:
                st.write(t(f"可用淨資產: {int(view_party.wealth)} ({int(view_party.wealth)} - 0)", f"Net Assets: {int(view_party.wealth)} ({int(view_party.wealth)} - 0)"))
            else:
                st.write(t(f"可用淨資產: {int(view_party.wealth)} ({int(view_party.wealth + total_maint)} - {int(total_maint)})", f"Net Assets: {int(view_party.wealth)} ({int(view_party.wealth + total_maint)} - {int(total_maint)})"))
                
            if rep:
                my_is_h = view_party.name == rep['h_party_name']
                real_inc = rep['h_inc'] if my_is_h else rep['r_inc']
                est_inc = rep['est_h_inc'] if my_is_h else rep['est_r_inc']
                pol_cost = view_party.last_acts.get('policy', 0)
                
                st.write(t(f"淨利: 真:{real_inc:.0f} (去年估:{est_inc:.0f})", f"Net: Real:{real_inc:.0f} (Est:{est_inc:.0f})"))
                st.write(t(f"去年施政花費: {pol_cost:.0f} 維護成本: {total_maint:.0f}", f"Last Yr Policy Cost: {pol_cost:.0f} Maint: {total_maint:.0f}"))
                final_profit = real_inc - pol_cost - total_maint
                st.write(t(f"收益總結: {real_inc:.0f} - {pol_cost:.0f} - {total_maint:.0f} = **{final_profit:.0f}**", f"Profit Summary: {real_inc:.0f} - {pol_cost:.0f} - {total_maint:.0f} = **{final_profit:.0f}**"))
        else:
            if is_preview:
                my_is_h = view_party.name == game.h_role_party.name
                my_net = preview_data['h_inc'] if my_is_h else preview_data['r_inc']
                opp_net = preview_data['r_inc'] if my_is_h else preview_data['h_inc']
                my_roi = preview_data['h_roi'] if my_is_h else preview_data['r_roi']
                opp_roi = preview_data['r_roi'] if my_is_h else preview_data['h_roi']
                
                st.markdown(t("### 📊 智庫評估報告", "### 📊 Think Tank Report"))
                st.markdown(t(f"我方預估收益: {my_net:.0f} (ROI: {my_roi:.1f}%)", f"Our Est. Profit: {my_net:.0f} (ROI: {my_roi:.1f}%)"))
                st.markdown(t(f"對方預估收益: {opp_net:.0f} (ROI: {opp_roi:.1f}%)", f"Opp Est. Profit: {opp_net:.0f} (ROI: {opp_roi:.1f}%)"))
                st.markdown(t(f"支持度預估: {preview_data['my_sup_shift']:+.2f}%", f"Est. Support: {preview_data['my_sup_shift']:+.2f}%"))
                st.markdown(t(f"📈 預期 GDP: {game.gdp:.0f} ➔ {disp_gdp:.0f} ({((disp_gdp-game.gdp)/max(1.0, game.gdp))*100:+.2f}%)", f"📈 Exp. GDP: {game.gdp:.0f} ➔ {disp_gdp:.0f} ({((disp_gdp-game.gdp)/max(1.0, game.gdp))*100:+.2f}%)"))
                st.markdown(t(f"衰退值判讀: 🟢 風險極低 (基準比對)", f"Decay Risk: 🟢 Low Risk (Baseline)"))
    st.markdown("---")

def render_message_board(game):
    if st.session_state.get('news_flash'):
        st.warning(st.session_state.news_flash)
        st.session_state.news_flash = None
        
    if game.phase == 1:
        if game.year == 1: st.info(t("📢 **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商。", "📢 **[ANNUAL UPDATE]** A new year begins. Please start budget negotiations."))
        elif game.last_year_report:
            st.info(t(f"📢 **【年度通報】** 新的一年開始了，請盡快展開預算與目標協商。", "📢 **[ANNUAL UPDATE]** A new year begins. Please start budget negotiations."))
    elif game.phase == 2:
        st.info(t("📢 **【年度通報】** 法案已通過，請分配黨產資金進行內部升級、競選造勢與媒體攻防。", "📢 **[ANNUAL UPDATE]** Bill passed. Allocate funds for upgrades, campaigns, and media."))

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    st.header(t("👤 玩家頁面", "👤 Player View"))
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
            role_badge = t("🛡️ [執行系統]", "🛡️ [H-System]") if is_h else t("⚖️ [監管系統]", "⚖️ [R-System]")
            is_winner = (game.ruling_party.name == party.name)
            crown_str = cfg.get('CROWN_WINNER', t('👑 當權', '👑 Ruling')) if is_winner else cfg.get('CROWN_LOSER', t('🎯 候選', '🎯 Candidate'))
            logo = config.get_party_logo(party.name)
            
            eye = "👁️ " if party.name == view_party.name else ""
            st.markdown(f"## {eye}{logo} {party.name} {crown_str}")
            st.markdown(f"#### {role_badge}")

            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}%" + (t(" 🏆(當選!)", " 🏆(Elected!)") if is_winner else t(" 💀(落選)", " 💀(Lost)"))
            else:
                if party.latest_poll is not None:
                    best_type = None
                    for pt in ['大型', '中型', '小型']:
                        if len(party.poll_history[pt]) > 0:
                            best_type = pt
                            break
                    if best_type:
                        avg = sum(party.poll_history[best_type]) / len(party.poll_history[best_type])
                        count = len(party.poll_history[best_type])
                        disp_sup = t(f"{party.latest_poll:.1f}%(最新民調) ({count}次{best_type}民調平均: {avg:.1f}%)", f"{party.latest_poll:.1f}%(Latest Poll) ({count} {best_type} avg: {avg:.1f}%)")
                    else:
                        disp_sup = t(f"{party.latest_poll:.1f}%(最新民調)", f"{party.latest_poll:.1f}%(Latest Poll)")
                else:
                    disp_sup = t("??? (需作民調)", "??? (Needs Poll)")
            
            st.markdown(t(f"### 📊 支持度: {disp_sup}", f"### 📊 Support: {disp_sup}"))
            
            if party.name == view_party.name and not is_election_year:
                b1, b2, b3 = st.columns(3)
                if b1.button(t("小民調 ($5)", "Small Poll ($5)"), key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5); st.rerun()
                if b2.button(t("中民調 ($10)", "Med Poll ($10)"), key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10); st.rerun()
                if b3.button(t("大民調 ($20)", "Big Poll ($20)"), key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20); st.rerun()

def render_sidebar_intel_audit(game, view_party, cfg):
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    st.markdown("---")
    st.title(t("🕵️ 情報處 - 對手機構指標", "🕵️ Intelligence - Opponent Stats"))
    blur = max(0.0, 1.0 - (view_party.investigate_ability / max(0.1, opp.stealth_ability))) if not st.session_state.get('god_mode') else 0.0
    acc = int((1.0 - blur)*100)
    st.progress(1.0 - blur, text=t(f"準確度: {acc}%", f"Accuracy: {acc}%"))
    rng = random.Random(f"intel_{opp.name}_{game.year}")
    
    st.write(t(f"智庫: {opp.predict_ability*(1+rng.uniform(-blur, blur))*10:.1f}% | 情報處: {opp.investigate_ability*(1+rng.uniform(-blur, blur))*10:.1f}%", f"Think Tank: {opp.predict_ability*(1+rng.uniform(-blur, blur))*10:.1f}% | Intel: {opp.investigate_ability*(1+rng.uniform(-blur, blur))*10:.1f}%"))
    st.write(t(f"黨媒: {opp.media_ability*(1+rng.uniform(-blur, blur))*10:.1f}% | 反情報處: {opp.stealth_ability*(1+rng.uniform(-blur, blur))*10:.1f}%", f"Media: {opp.media_ability*(1+rng.uniform(-blur, blur))*10:.1f}% | Counter-Intel: {opp.stealth_ability*(1+rng.uniform(-blur, blur))*10:.1f}%"))
    st.write(t(f"工程處: {opp.build_ability*(1+rng.uniform(-blur, blur))*10:.1f}%", f"Engineering: {opp.build_ability*(1+rng.uniform(-blur, blur))*10:.1f}%"))

    st.markdown("---")
    st.title(t("📈 審計處 - 內部部門投資", "📈 Audit - Internal Dept. Investments"))
    total_maint = sum([formulas.get_ability_maintenance(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
    st.write(t(f"智庫: {view_party.predict_ability*10:.1f}% | 情報處: {view_party.investigate_ability*10:.1f}%", f"Think Tank: {view_party.predict_ability*10:.1f}% | Intel: {view_party.investigate_ability*10:.1f}%"))
    st.write(t(f"黨媒: {view_party.media_ability*10:.1f}% | 反情報處: {view_party.stealth_ability*10:.1f}%", f"Media: {view_party.media_ability*10:.1f}% | Counter-Intel: {view_party.stealth_ability*10:.1f}%"))
    st.write(t(f"工程處: {view_party.build_ability*10:.1f}%", f"Engineering: {view_party.build_ability*10:.1f}%"))
    st.write(t(f"**(依據當前機構投資，明年維護費估算: -${total_maint:.0f})**", f"**(Est. Next Yr Maint: -${total_maint:.0f})**"))

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write(t(f"**公告衰退:** {plan['claimed_decay']:.2f} | **目標 GDP 成長:** {plan['target_gdp_growth']}%", f"**Claimed Decay:** {plan['claimed_decay']:.2f} | **Target GDP Growth:** {plan['target_gdp_growth']}%"))
        st.write(t(f"**總額:** {plan['total_funds']} (監管出資: {plan['r_pays']} | 執行出資: {plan['h_pays']})", f"**Total:** {plan['total_funds']} (R-Pays: {plan['r_pays']} | H-Pays: {plan['h_pays']})"))
        
    with c2:
        o_gdp_pct, o_h_g, o_h_n, o_r_g, o_r_n, o_h_sup, o_r_sup, o_est_gdp, o_est_h_fund, o_h_roi, o_r_roi = formulas.calculate_preview(cfg, game, plan['total_funds'], plan['h_ratio'], plan['r_value'], view_party.current_forecast, game.h_role_party.build_ability, plan['r_pays'], plan['h_pays'])
        my_is_h = (view_party.name == game.h_role_party.name)
        my_net, my_sup, my_roi = (o_h_n, o_h_sup, o_h_roi) if my_is_h else (o_r_n, o_r_sup, o_r_roi)
        opp_net, opp_sup, opp_roi = (o_r_n, o_r_sup, o_r_roi) if my_is_h else (o_h_n, o_h_sup, o_h_roi)
        
        st.markdown(t(f"**📊 智庫評估報告 (依自己預測: -{view_party.current_forecast:.2f})**", f"**📊 Think Tank Report (Based on est: -{view_party.current_forecast:.2f})**"))
        st.markdown(t(f"我方預估收益: {my_net:.0f} (ROI: {my_roi:.1f}%)", f"Our Est Profit: {my_net:.0f} (ROI: {my_roi:.1f}%)"))
        st.markdown(t(f"對方預估收益: {opp_net:.0f} (ROI: {opp_roi:.1f}%)", f"Opp Est Profit: {opp_net:.0f} (ROI: {opp_roi:.1f}%)"))
        st.markdown(t(f"支持度預估: {my_sup:+.2f}%", f"Est. Support Shift: {my_sup:+.2f}%"))
        st.markdown(t(f"📈 預期 GDP: {game.gdp:.0f} ➔ {o_est_gdp:.0f} ({o_gdp_pct:+.2f}%)", f"📈 Exp. GDP: {game.gdp:.0f} ➔ {o_est_gdp:.0f} ({o_gdp_pct:+.2f}%)"))
        
        diff = abs(plan['claimed_decay'] - view_party.current_forecast)
        if diff > 0.3: risk_txt = t("🔴 風險極高 (數據嚴重偏離預估)", "🔴 Very High Risk")
        elif diff > 0.1: risk_txt = t("🟡 風險中等 (數據略有出入)", "🟡 Med Risk")
        else: risk_txt = t("🟢 風險極低 (基準比對)", "🟢 Low Risk")
        st.markdown(t(f"衰退值判讀: {risk_txt}", f"Decay Analysis: {risk_txt}"))

def ability_slider(label, key, current_val, wealth, cfg):
    current_pct = current_val * 10.0
    t_pct = st.slider(f"{label} ({t('當前', 'Current')}: {current_pct:.1f}%)", 0.0, 100.0, float(current_pct), 1.0, key=key)
    
    t_val = t_pct / 10.0
    
    cost = formulas.calculate_upgrade_cost(current_val, t_val)
    maint = formulas.get_ability_maintenance(t_val, cfg)
    
    if t_val > current_val:
        st.caption(t(f"📈 升級花費: ${int(cost)} | 維護費將達 ${int(maint)}", f"📈 Upgrade Cost: ${int(cost)} | Maint: ${int(maint)}"))
    elif t_val < current_val:
        st.caption(t(f"📉 免費降級 | 維護費降至 ${int(maint)}", f"📉 Free Downgrade | Maint drops to ${int(maint)}"))
    else:
        st.caption(t(f"穩定維持 | 維護費 ${int(maint)}", f"Stable | Maint: ${int(maint)}"))
    return t_val, cost

def add_event_vlines(fig, history_df):
    for _, row in history_df.iterrows():
        y = row['Year']
        if row['Is_Swap']: fig.add_vline(x=y, line_dash="dot", line_color="red", annotation_text=t("倒閣!", "Swap!"), annotation_position="top left")
        if row['Is_Election']: fig.add_vline(x=y, line_dash="dash", line_color="green", annotation_text=t("選舉", "Election"), annotation_position="bottom right")

def render_endgame_charts(history_data, cfg):
    st.balloons()
    st.title(t("🏁 遊戲結束！共生內閣軌跡總結算", "🏁 Game Over! Symbiocracy Trajectory"))
    df = pd.DataFrame(history_data)

    st.subheader(t("📊 1. 總體經濟與資訊辨識指數走勢", "📊 1. Macro Economy & Civic Literacy"))
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['GDP'], name=t("總 GDP", "Total GDP"), line=dict(color='blue', width=3)), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity'], name=t("資訊辨識 (0-100)", "Civic Literacy (0-100)"), line=dict(color='purple', width=3)), secondary_y=True)
    fig1.update_yaxes(title_text=t("GDP (資金)", "GDP (Funds)"), secondary_y=False)
    fig1.update_yaxes(title_text=t("辨識指數", "Literacy Index"), secondary_y=True, range=[0, 100])
    add_event_vlines(fig1, df)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader(t(f"📊 2. 雙方民意支持度與黨產角力", f"📊 2. Support & Wealth Rivalry"))
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['A_Wealth'], name=t(f"{cfg['PARTY_A_NAME']} 存款", f"{cfg['PARTY_A_NAME']} Savings"), line=dict(color='cyan', dash='dash')), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['B_Wealth'], name=t(f"{cfg['PARTY_B_NAME']} 存款", f"{cfg['PARTY_B_NAME']} Savings"), line=dict(color='orange', dash='dash')), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['A_Support'], name=t(f"{cfg['PARTY_A_NAME']} 民意支持度", f"{cfg['PARTY_A_NAME']} Support"), line=dict(color='green', width=4)), secondary_y=True)
    fig2.update_yaxes(title_text=t("財富總額", "Total Wealth"), secondary_y=False)
    fig2.update_yaxes(title_text=t("支持度 (%)", "Support (%)"), secondary_y=True, range=[0, 100])
    add_event_vlines(fig2, df)
    st.plotly_chart(fig2, use_container_width=True)
