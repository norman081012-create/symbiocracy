\# ==========================================
# phase2.py
# ==========================================
import streamlit as st
import ui_core

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    st.subheader(f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name}")
    
    cw = max(0, int(view_party.wealth))
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 📣 政策與行動")
        h_corr_pct = st.slider("💸 秘密貪污 (%)", 0, 100, 0) if is_h else 0
        h_crony_pct = st.slider("🏢 圖利自身廠商 (%)", 0, max(0, 100 - h_corr_pct), 0) if is_h else 0
        
        judicial_amt = st.slider("⚖️ 司法審查 (投入資金)", 0.0, float(cw), 0.0) if not is_h else 0
        edu_policy_amt = st.slider("🎓 教育方針 (左填鴨/右思辨, 投入資金)", -float(cw), float(cw), 0.0) if not is_h else 0
        
        media_ctrl = st.slider("📺 媒體操控 (投入資金)", 0.0, float(cw), 0.0)
        camp_amt = st.slider("🎉 舉辦競選 (投入資金)", 0.0, float(cw), 0.0)
        incite_emo = st.slider("🔥 煽動情緒 (投入資金)", 0.0, float(cw), 0.0)
        
    with c2:
        st.markdown("#### 🔒 部門投資池 (資金投滿立即升級)")
        inv_pre, tgt_pre = ui_core.ability_investment_ui("智庫", "pre", view_party.predict_ability, view_party.invest_pools['pre'], cw, is_h, cfg)
        inv_inv, tgt_inv = ui_core.ability_investment_ui("情報處", "inv", view_party.investigate_ability, view_party.invest_pools['inv'], cw, is_h, cfg)
        inv_med, tgt_med = ui_core.ability_investment_ui("黨媒", "med", view_party.media_ability, view_party.invest_pools['media'], cw, is_h, cfg)
        inv_stl, tgt_stl = ui_core.ability_investment_ui("反情報", "stl", view_party.stealth_ability, view_party.invest_pools['stl'], cw, is_h, cfg)
        inv_bld, tgt_bld = ui_core.ability_investment_ui("工程", "bld", view_party.build_ability, view_party.invest_pools['build'], cw, is_h, cfg) if is_h else (0.0, view_party.build_ability)

    tot = media_ctrl + camp_amt + incite_emo + abs(edu_policy_amt) + judicial_amt + inv_pre + inv_inv + inv_med + inv_stl + inv_bld
    st.write(f"**總花費:** `{tot:.0f}` / **剩餘可用:** `{cw - tot:.0f}`")
    
    if tot > cw: st.error("🚨 資金不足！請降低投入金額。")
    elif st.button("確認行動/結束回合", type="primary"):
        st.session_state[f"{view_party.name}_acts"] = {
            'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt, 'edu_amt': edu_policy_amt,
            'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo,
            'inv_pre': inv_pre, 'inv_inv': inv_inv, 'inv_med': inv_med, 'inv_stl': inv_stl, 'inv_bld': inv_bld
        }
        
        view_party.last_acts = st.session_state[f"{view_party.name}_acts"].copy()
        
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            game.phase = 3; st.rerun()
