# phase2.py
import streamlit as st
import ui_core

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    st.subheader(f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name}")
    
    cw = max(0, int(view_party.wealth))
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 📣 政策與媒體")
        media_ctrl = st.slider("📺 媒體操控 (投入資金)", 0.0, float(cw), 0.0)
        camp_amt = st.slider("🎉 舉辦競選 (投入資金)", 0.0, float(cw), 0.0)
        incite_emo = st.slider("🔥 煽動情緒 (投入資金)", 0.0, float(cw), 0.0)
        
    with c2:
        st.markdown("#### 🔒 部門投資池 (漸進升級)")
        inv_pre, tgt_pre = ui_core.ability_investment_ui("智庫", "pre", view_party.predict_ability, view_party.invest_pools['pre'], cw, cfg)
        inv_med, tgt_med = ui_core.ability_investment_ui("黨媒", "med", view_party.media_ability, view_party.invest_pools['media'], cw, cfg)
        inv_bld, tgt_bld = ui_core.ability_investment_ui("工程", "bld", view_party.build_ability, view_party.invest_pools['build'], cw, cfg) if is_h else (0.0, view_party.build_ability)

    tot = media_ctrl + camp_amt + incite_emo + inv_pre + inv_med + inv_bld
    st.write(f"**總花費:** `{tot:.0f}` / **剩餘可用:** `{cw - tot:.0f}`")
    
    if tot > cw: st.error("🚨 資金不足！")
    elif st.button("確認行動", type="primary"):
        st.session_state[f"{view_party.name}_acts"] = {
            'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo,
            'inv_pre': inv_pre, 'inv_med': inv_med, 'inv_bld': inv_bld,
            'tgt_pre': tgt_pre, 'tgt_med': tgt_med, 'tgt_bld': tgt_bld
        }
        
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            game.phase = 3; st.rerun()
