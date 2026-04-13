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
        san_chg = (disp_san - rep['old_san']) if rep else 0
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
        if game.phase == 1:
            st.markdown("### 📊 財報")
            total_maint = sum([formulas.get_ability_maintenance(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
            
            if game.year == 1:
                st.write(f"可用淨資產: {int(view_party.wealth)} ({int(view_party.wealth)} - 0)")
            else:
                st.write(f"可用淨資產: {int(view_party.wealth)} ({int(view_party.wealth + total_maint)} - {int(total_maint)})")
                
            if rep:
                my_is_h = view_party.name == rep['h_party_name']
                real_inc = rep['h_inc'] if my_is_h else rep['r_inc']
                est_inc = rep['est_h_inc'] if my_is_h else rep['est_r_inc']
                pol_cost = view_party.last_acts.get('policy', 0)
                
                st.write(f"淨利: 真:{real_inc:.0f} (去年估:{est_inc:.0f})")
                st.write(f"去年施政花費: {pol_cost:.0f} 維護成本: {total_maint:.0f}")
                final_profit = real_inc - pol_cost - total_maint
                st.write(f"收益總結: {real_inc:.0f} - {pol_cost:.0f} - {total_maint:.0f} = **{final_profit:.0f}**")
        else:
            if is_preview:
                my_is_h = view_party.name == game.h_role_party.name
                my_net = preview_data['h_inc'] if my_is_h else preview_data['r_inc']
                opp_net = preview_data['r_inc'] if my_is_h else preview_data['h_inc']
                my_roi = preview_data['h_roi'] if my_is_h else preview_data['r_roi']
                opp_roi = preview_data['r_roi'] if my_is_h else preview_data['h_roi']
                
                st.markdown("### 📊 智庫評估報告")
                st.markdown(f"我方預估收益: {my_net:.0f} (ROI: {my_roi:.1f}%)")
                st.markdown(f"對方預估收益: {opp_net:.0f} (ROI: {opp_roi:.1f}%)")
                st.markdown(f"支持度預估: {preview_data['my_sup_shift']:+.2f}%")
                st.markdown(f"📈 預期 GDP: {game.gdp:.0f} ➔ {disp_gdp:.0f} ({((disp_gdp-game.gdp)/max(1.0, game.gdp))*100:+.2f}%)")
                st.markdown(f"衰退值判讀: 🟢 風險極低 (基準比對)")
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
            crown = "👑 當權派" if is_winner else "🎯 在野派"
            logo = config.get_party_logo(party.name)
            
            eye = "👁️ " if party.name == view_party.name else ""
            st.markdown(f"## {eye}{logo} {party.name} {crown}")
            st.markdown(f"#### {role_badge}")

            # 只要是選舉年，直接顯示支持度並取消隱藏
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
            
            # 選舉年隱藏作民調的功能
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
    
    st.write(f"智庫: {opp.predict_ability*(1+rng.uniform(-blur, blur))*10:.1f}% | 情報處: {opp.investigate_ability*(1+rng.uniform(-blur, blur))*10:.1f}%")
    st.write(f"黨媒: {opp.media_ability*(1+rng.uniform(-blur, blur))*10:.1f}% | 反情報處: {opp.stealth_ability*(1+rng.uniform(-blur, blur))*10:.1f}%")
    st.write(f"工程處: {opp.build_ability*(1+rng.uniform(-blur, blur))*10:.1f}%")

    st.markdown("---")
    st.title("📈 審計處 - 內部部門投資")
    total_maint = sum([formulas.get_ability_maintenance(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
    st.write(f"智庫: {view_party.predict_ability*10:.1f}% | 情報處: {view_party.investigate_ability*10:.1f}%")
    st.write(f"黨媒: {view_party.media_ability*10:.1f}% | 反情報處: {view_party.stealth_ability*10:.1f}%")
    st.write(f"工程處: {view_party.build_ability*10:.1f}%")
    st.write(f"**(依據當前機構投資，明年維護費估算: -${total_maint:.0f})**")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write(f"**公告衰退:** {plan['claimed_decay']:.2f} | **目標 GDP 成長:** {plan['target_gdp_growth']}%")
        st.write(f"**總額:** {plan['total_funds']} (監管出資: {plan['r_pays']} | 執行出資: {plan['h_pays']})")
        
    with c2:
        o_gdp_pct, o_h_g, o_h_n, o_r_g, o_r_n, o_h_sup, o_r_sup, o_est_gdp, o_est_h_fund, o_h_roi, o_r_roi = formulas.calculate_preview(cfg, game, plan['total_funds'], plan['h_ratio'], plan['r_value'], view_party.current_forecast, game.h_role_party.build_ability, plan['r_pays'], plan['h_pays'])
        my_is_h = (view_party.name == game.h_role_party.name)
        my_net, my_sup, my_roi = (o_h_n, o_h_sup, o_h_roi) if my_is_h else (o_r_n, o_r_sup, o_r_roi)
        opp_net, opp_sup, opp_roi = (o_r_n, o_r_sup, o_r_roi) if my_is_h else (o_h_n, o_h_sup, o_h_roi)
        
        st.markdown(f"**📊 智庫評估報告 (依自己預測: -{view_party.current_forecast:.2f})**")
        st.markdown(f"我方預估收益: {my_net:.0f} (ROI: {my_roi:.1f}%)")
        st.markdown(f"對方預估收益: {opp_net:.0f} (ROI: {opp_roi:.1f}%)")
        st.markdown(f"支持度預估: {my_sup:+.2f}%")
        st.markdown(f"📈 預期 GDP: {game.gdp:.0f} ➔ {o_est_gdp:.0f} ({o_gdp_pct:+.2f}%)")
        
        diff = abs(plan['claimed_decay'] - view_party.current_forecast)
        if diff > 0.3: risk_txt = "🔴 風險極高 (數據嚴重偏離預估)"
        elif diff > 0.1: risk_txt = "🟡 風險中等 (數據略有出入)"
        else: risk_txt = "🟢 風險極低 (基準比對)"
        st.markdown(f"衰退值判讀: {risk_txt}")

def ability_slider(label, key, current_val, wealth, cfg):
    current_pct = current_val * 10.0
    t_pct = st.slider(f"{label} (當前: {current_pct:.1f}%)", 0.0, 100.0, float(current_pct), 1.0, key=key)
    t_val = t
