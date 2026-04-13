# ==========================================
# phase2.py
# 負責 第二階段 (政策執行與結算) 的 UI 與邏輯
# ==========================================
import streamlit as st
import random
import config
import formulas
import ui_core

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    st.subheader(f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name} ({'🛡️ 執行系統' if is_h else '⚖️ 監管系統'})")
    
    d = st.session_state.turn_data
    req_pay = d.get('h_pays', 0) if is_h else d.get('r_pays', 0)
    cw = max(0, int(view_party.wealth))
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📣 政策與媒體")
        if is_h: st.caption("💡 **執行系統特性**: 媒體操控值 1.2 倍加成")
        else: st.caption("💡 **監管系統特性**: 調查能力值 1.2 倍加成")
        
        h_corr_pct = st.slider("💸 秘密貪污 (%)", 0, 100, 0) if is_h else 0
        h_crony_pct = st.slider("🏢 圖利自身廠商 (%)", 0, max(0, 100 - h_corr_pct), 0) if is_h else 0
        
        judicial_amt = st.slider("⚖️ 司法審查 (扣抵媒體效果, 投入資金)", 0, cw, 0) if not is_h else 0
        media_ctrl = st.slider("📺 媒體操控 (甩鍋/搶功勞, 投入資金)", 0, cw, 0)
        
        # 教育方針採漸近線收斂模型
        edu_policy_amt = st.slider("🎓 教育方針 (左:填鴨 右:思辨, 投入資金)", -cw, cw, 0) if not is_h else 0
        target_san = max(0.0, min(100.0, 50.0 + (edu_policy_amt / 500.0) * 50.0))
        san_move = (target_san - game.sanity) * 0.2
        new_san_preview = game.sanity + san_move
        if not is_h:
            st.caption(f"資訊辨識: {config.get_civic_index_text(game.sanity)} -> {config.get_civic_index_text(new_san_preview)} (變動: {san_move:+.1f}/年 {abs(edu_policy_amt):.0f}元)")
            
        camp_amt = st.slider("🎉 舉辦競選 (提升自身支持度, 投入資金)", 0, cw, 0)
        incite_emo = st.slider("🔥 煽動情緒 (短期降資訊辨識, 投入資金)", 0, cw, 0)
        
    with c2:
        st.markdown("#### 🔒 內部部門投資")
        t_pre, c_pre = ui_core.ability_slider("智庫", f"up_pre", view_party.predict_ability, cw, cfg)
        t_inv, c_inv = ui_core.ability_slider("情報處", f"up_inv", view_party.investigate_ability, cw, cfg)
        t_med, c_med = ui_core.ability_slider("黨媒", f"up_med", view_party.media_ability, cw, cfg)
        t_stl, c_stl = ui_core.ability_slider("反情報處", f"up_stl", view_party.stealth_ability, cw, cfg)
        t_bld, c_bld = ui_core.ability_slider("工程處", f"up_bld", view_party.build_ability, cw, cfg) if is_h else (view_party.build_ability, 0)

    tot_action = media_ctrl + camp_amt + incite_emo + abs(edu_policy_amt) + judicial_amt
    tot_maint = c_inv + c_pre + c_med + c_stl + c_bld
    tot = req_pay + tot_action + tot_maint
    
    st.write(f"**法定專案款:** `{int(req_pay)}` / **政策與媒體:** `{int(tot_action)}` / **內部部門投資:** `{int(tot_maint)}` / **剩餘可用淨值:** `{int(cw - tot)}`")
    
    # 防呆提示：如果拉桿花費超過資產，按鈕會隱藏並給予明確警告
    if tot > cw:
        st.error(f"🚨 資金不足！當前行動預算已超支 {int(tot - cw)} 元，請降低投入資金。")
    
    ra, ha = {}, {}
    if f"{opponent_party.name}_acts" in st.session_state:
        opp_acts = st.session_state[f"{opponent_party.name}_acts"]
        ra = opp_acts if is_h else {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt}
        ha = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt} if is_h else opp_acts
    else:
        ra = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt} if not is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_amt': 0, 'corr': 0, 'crony': 0, 'judicial': 0}
        ha = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt} if is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_amt': 0, 'corr': 0, 'crony': 0, 'judicial': 0}

    corr_amt = d.get('total_funds', 0) * (ha.get('corr', 0) / 100.0)
    crony_base = d.get('total_funds', 0) * (ha.get('crony', 0) / 100.0)
    crony_income = crony_base * 0.1 * d.get('r_value', 1.0)
    act_build = d.get('total_funds', 0) - corr_amt
    
    h_bst = (act_build * d.get('h_ratio', 1.0) * game.h_role_party.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
    new_h_fund = max(0.0, game.h_fund + h_bst - (view_party.current_forecast * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
    gdp_bst = (act_build * game.h_role_party.build_ability) / cfg['BUILD_DIFF']
    new_gdp = max(0.0, game.gdp + gdp_bst - (view_party.current_forecast * 1000))
    budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
    h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
    
    hp_inc_est = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.h_role_party.name else 0) + (budg * h_shr) - d.get('h_pays',0) + corr_amt + crony_income
    rp_inc_est = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.r_role_party.name else 0) + (budg * (1 - h_shr)) - d.get('r_pays',0)

    shift_preview = formulas.calc_support_shift(cfg, game.h_role_party, game.r_role_party, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha, ra)
    
    # 預覽資訊辨識的漸近線變動
    t_san_preview = max(0.0, min(100.0, 50.0 + (ra.get('edu_amt', 0) / 500
