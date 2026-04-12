# ==========================================
# phase2.py
# 負責 第二階段 (政策執行與結算) 的 UI 與邏輯
# ==========================================
import streamlit as st
import random
import formulas
import ui_core

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    role_str = "🛡️ 執行系統" if is_h else "⚖️ 監管系統"
    st.subheader(f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name} ({role_str})")
    
    d = st.session_state.turn_data
    req_pay = d.get('h_pays', 0) if is_h else d.get('r_pays', 0)
    current_wealth = int(view_party.wealth)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📣 政策與媒體")
        st.info(f"📜 **法定專案款 (不可動用):** `${req_pay}`")
        if is_h: st.caption("💡 **執行系統特性**: 媒體操控值 1.2 倍加成")
        else: st.caption("💡 **監管系統特性**: 調查能力值 1.2 倍加成")
        
        media_ctrl = st.slider("📺 媒體操控 (推卸責任/攻擊)", 0, current_wealth, min(50, current_wealth))
        camp_amt = st.slider("🎉 舉辦競選 (提升自身支持度)", 0, current_wealth, 0)
        incite_emo = st.slider("🔥 煽動情緒 (短期降理智)", 0, current_wealth, 0)
        edu_up = st.slider("🎓 推行教育 (提升理智)", 0, current_wealth, 0) if not is_h else 0
        edu_down = st.slider("🧠 推行降智 (降低理智)", 0, current_wealth, 0) if not is_h else 0
        
        h_corr_pct = st.slider("💸 秘密貪污 (%)", 0, 100, 0) if is_h else 0
        inv_corr_amt = st.slider("🔍 調查貪污 (投入資金)", 0, current_wealth, 0) if not is_h else 0
        
    with c2:
        st.markdown("#### 🔒 內部升級與維護")
        priv_inv = ui_core.ability_slider("🔍 調查能力", f"up_inv_{view_party.name}", view_party.investigate_ability, current_wealth, cfg)
        priv_pre = ui_core.ability_slider("🕵️ 預測能力", f"up_pre_{view_party.name}", view_party.predict_ability, current_wealth, cfg)
        priv_media = ui_core.ability_slider("📺 媒體操控力", f"up_med_{view_party.name}", view_party.media_ability, current_wealth, cfg)
        priv_edu = ui_core.ability_slider("🎓 教育能力", f"up_edu_{view_party.name}", view_party.edu_ability, current_wealth, cfg)
        h_build_up = ui_core.ability_slider("🏗️ 建設能力", f"up_bld_{view_party.name}", view_party.build_ability, current_wealth, cfg) if is_h else 0

    tot = req_pay + media_ctrl + camp_amt + incite_emo + edu_up + edu_down + inv_corr_amt + priv_inv + priv_pre + priv_media + priv_edu + h_build_up
    st.write(f"**總花費:** `{tot}` / `{current_wealth}`")
    
    if f"{opponent_party.name}_acts" in st.session_state:
        opp_acts = st.session_state[f"{opponent_party.name}_acts"]
        ra = opp_acts if is_h else {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct, 'inv_corr': inv_corr_amt}
        ha = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct, 'inv_corr': inv_corr_amt} if is_h else opp_acts
    else:
        ra = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct, 'inv_corr': inv_corr_amt} if not is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_up': 0, 'edu_down': 0, 'corr': 0, 'inv_corr': 0}
        ha = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct, 'inv_corr': inv_corr_amt} if is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_up': 0, 'edu_down': 0, 'corr': 0, 'inv_corr': 0}

    corr_amt = d.get('total_funds', 0) * (ha['corr'] / 100.0)
    act_build = d.get('total_funds', 0) - corr_amt
    h_bst = (act_build * d.get('h_ratio', 1.0) * game.h_role_party.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
    new_h_fund = max(0.0, game.h_fund + h_bst - (view_party.current_forecast * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
    gdp_bst = (act_build * game.h_role_party.build_ability) / cfg['BUILD_DIFF']
    new_gdp = max(0.0, game.gdp + gdp_bst - (view_party.current_forecast * 1000))
    budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
    h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
    
    hp_inc_est = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.h_role_party.name else 0) + (budg * h_shr) - d.get('h_pays',0) + corr_amt
    rp_inc_est = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.r_role_party.name else 0) + (budg * (1 - h_shr)) - d.get('r_pays',0)

    shift_preview = formulas.calc_support_shift(cfg, game.h_role_party, game.r_role_party, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha, ra)
    
    preview_data = {
        'gdp': new_gdp, 'budg': budg, 'h_fund': new_h_fund,
        'san': max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + ((ra['edu_up']+ha['edu_up']) * 0.005) - ((ra['edu_down']+ha['edu_down']) * 0.005))),
        'emo': max(0.0, min(100.0, game.emotion + (ha['incite'] + ra['incite']) * 0.1 - (((new_gdp - game.gdp)/max(1.0, game.gdp))*100) - (game.sanity * 20.0))),
        'h_inc': hp_inc_est, 'r_inc': rp_inc_est,
        'h_roi': (hp_inc_est / max(1.0, float(d.get('h_pays',0)))) * 100.0 if d.get('h_pays',0) > 0 else float('inf'),
        'r_roi': (rp_inc_est / max(1.0, float(d.get('r_pays',0)))) * 100.0 if d.get('r_pays',0) > 0 else float('inf'),
        'my_sup_shift': shift_preview['actual_shift'] if is_h else -shift_preview['actual_shift'],
        'opp_sup_shift': -shift_preview['actual_shift'] if is_h else shift_preview['actual_shift']
    }
    
    ui_core.render_dashboard(game, view_party, cfg, is_preview=True, preview_data=preview_data)
    
    if tot <= current_wealth and st.button("確認行動/結算", use_container_width=True, type="primary"):
        st.session_state[f"{view_party.name}_acts"] = {
            'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct, 'inv_corr': inv_corr_amt,
            'p_inv': priv_inv, 'p_pre': priv_pre, 'p_media': priv_media, 'p_edu': priv_edu, 'p_bld': h
