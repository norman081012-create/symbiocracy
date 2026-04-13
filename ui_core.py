# ==========================================
# ui_core.py
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

def render_dashboard(game, view_party, cfg):
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🌐 國家總體現況")
        st.markdown(f"**資訊辨識:** `{config.get_civic_index_text(game.sanity)}`")
        st.markdown(f"**選民情緒:** `{config.get_emotion_text(game.emotion)}`")
        st.markdown(f"**當前 GDP:** `{game.gdp:.1f}`")
    with c2:
        st.markdown("### 💰 標案預算池")
        st.markdown(f"**可用標案總額 (P):** `{game.current_budget_pool:.0f}`")
    with c3:
        st.markdown("### 🕵️ 智庫情報")
        fc = view_party.current_forecast
        acc = min(100, int((view_party.depts['predict'].eff / cfg['EFF_DEFAULT']) * 100))
        st.info(f"經濟預估: {config.get_economic_forecast_text(fc)}\n\n(預估衰退值: -{fc:.2f})\n\n準確度: {acc}%")
    st.markdown("---")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    st.header("👤 玩家頁面")
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    
    # 動態背景色: 輪到的黨派更亮
    a_is_active = (view_party.name == game.party_A.name)
    b_is_active = (view_party.name == game.party_B.name)
    a_bg = f"{cfg['PARTY_A_COLOR']}33" if a_is_active else f"{cfg['PARTY_A_COLOR']}0A"
    b_bg = f"{cfg['PARTY_B_COLOR']}33" if b_is_active else f"{cfg['PARTY_B_COLOR']}0A"

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
            crown = "👑 當權" if is_winner else "🎯 候選"
            logo = config.get_party_logo(party.name)
            eye = "👁️ " if party.name == view_party.name else ""
            
            st.markdown(f"## {eye}{logo} {party.name} {crown}")
            st.markdown(f"#### {role_badge}")
            st.markdown(f"**黨產資金:** `${party.wealth:.0f}`")

            # 選舉年絕對顯示真實支持度
            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_winner and is_election_year else "")
            else:
                if party.latest_poll is not None:
                    best_type = next((t for t in ['大型', '中型', '小型'] if party.poll_history[t]), None)
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
    st.title("📈 審計處")
    total_maint = sum([formulas.get_ability_maintenance(dept, cfg) for dept in view_party.depts.values()])
    with st.expander("自身各部門效率及維護費", expanded=True):
        st.write(f"建設:{view_party.depts['build'].eff:.1f}% | 調查:{view_party.depts['investigate'].eff:.1f}%")
        st.write(f"教育:{view_party.depts['edu'].eff:.1f}% | 媒體:{view_party.depts['media'].eff:.1f}%")
        st.write(f"預測:{view_party.depts['predict'].eff:.1f}% | 隱密:{view_party.depts['stealth'].eff:.1f}%")
        st.write(f"**明年維護費估算:** -${total_maint:.0f}")

def render_debug_panel(game, cfg):
    with st.expander("⚙️ 遊戲底層引擎與數學監控 (Debug UI)", expanded=False):
        st.markdown("### Symbiocracy 經濟系統運作公式 (Hardcoded)")
        st.markdown("""
        **一、 預算與物理運作規則**
        1. **稅收預算化**：當年 GDP 的 20% 轉化為總預算 (T)。
        2. **年金先領制**：今年年初優先從 T 扣除政黨基本金 (p_b 5%) 與當權紅利 (p_r 10%) 撥入政黨口袋。
        3. **標案與殘值**：預算扣除年金後為標案池上限 (P)。監管系統 (R) 決定投標資金 (C) 後，未撥款的殘值 (P - C) 於**下一年年初**撥入 R 口袋。
        4. **環境物理**：衰退值換算為衰退率 (R_decay)，產生 GDP 損耗量 (L_gdp)。衰退率經由倍率 (M) 放大，形成建設阻力。
        5. **實質產出**：執行系統 (H) 投入資金與建設能力產出的毛量，扣除建設阻力後為實質建設量 (C_net)。更新當年 GDP。
        6. **H 指數結算**：依據 C_net 對比標案要求算出達標率 (H)。下一年年初，H 領取標案收益 (C * H)，R 領取失敗退款 (C * (1-H))。
        """)
        st.code(f"""
[本回合參數狀態]
真實衰退率 = {game.current_real_decay:.3f}
當前 GDP = {game.gdp:.1f}
標案池 (P) = {game.current_budget_pool:.1f}
A黨待領收益 = {game.pending_payouts['A']:.1f}
B黨待領收益 = {game.pending_payouts['B']:.1f}
        """)

def render_endgame_charts(history_data, cfg):
    st.balloons(); st.title("🏁 遊戲結束！共生內閣軌跡總結算")
    df = pd.DataFrame(history_data)
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['GDP'], name="總 GDP", line=dict(color='blue', width=3)), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity']*100, name="資訊辨識 (0-100)", line=dict(color='purple', width=3)), secondary_y=True)
    st.plotly_chart(fig1, use_container_width=True)
