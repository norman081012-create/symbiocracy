# ==========================================
# phase2.py
# Handles Phase 2 (Execution and Action Selection) UI & Logic
# ==========================================
import streamlit as st
import config
import formulas
import ui_core
import i18n
t = i18n.t

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    h_label = t('🛡️ H-System', '🛡️ H-System')
    r_label = t('⚖️ R-System', '⚖️ R-System')
    st.subheader(f"{t('🛠️ Phase 2: Execution - Turn:', '🛠️ Phase 2: Execution - Turn:')} {view_party.name} ({h_label if is_h else r_label})")
    
    d = st.session_state.get('turn_data', {})
    req_pay = float(d.get('h_pays') or 0.0) if is_h else float(d.get('r_pays') or 0.0)
    cw = max(0.0, float(view_party.wealth))
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(t("#### 📣 Policy & Media", "#### 📣 Policy & Media"))
        if is_h: st.caption(t("💡 **H-System Perk**: Media Control x1.2", "💡 **H-System Perk**: Media Control x1.2"))
        else: st.caption(t("💡 **R-System Perk**: Intelligence x1.2", "💡 **R-System Perk**: Intelligence x1.2"))
        
        h_corr_pct = 0; h_crony_pct = 0
        judicial_amt = 0.0; edu_policy_amt = 0.0
        
        last_media = min(float(view_party.last_acts.get('media', 0.0)), cw)
        last_camp = min(float(view_party.last_acts.get('camp', 0.0)), cw)
        last_incite = min(float(view_party.last_acts.get('incite', 0.0)), cw)
        last_judicial = min(float(view_party.last_acts.get('judicial', 0.0)), cw)
        
        if is_h:
            last_corr = int(view_party.last_acts.get('corr', 0))
            last_crony = int(view_party.last_acts.get('crony', 0))
            h_corr_pct = st.slider(t("💸 Secret Corruption (%)", "💸 Secret Corruption (%)"), 0, 100, last_corr)
            
            max_crony = max(0, 100 - h_corr_pct)
            safe_crony = min(last_crony, max_crony)
            
            if max_crony <= 0:
                h_crony_pct = 0
                st.info(t("Secret corruption has reached the limit, cronyism is no longer possible.", "Secret corruption has reached the limit, cronyism is no longer possible."))
            else:
                h_crony_pct = st.slider(t("🏢 Cronyism (%)", "🏢 Cronyism (%)"), 0, max_crony, safe_crony)
        else:
            judicial_amt = st.slider(t("⚖️ Media Censorship (Reduces opp. media, penalizes own support)", "⚖️ Media Censorship (Reduces opp. media, penalizes own support)"), 0.0, cw, last_judicial)
            edu_policy_amt = st.slider(t("🎓 Education Policy (Left: Canned, Right: Critical)", "🎓 Education Policy (Left: Canned, Right: Critical)"), -cw, cw, 0.0)
            
        media_ctrl = st.slider(t("📺 Media Control (Changes policy impact)", "📺 Media Control (Changes policy impact)"), 0.0, cw, last_media)
        camp_amt = st.slider(t("🎉 Campaign (Lower sanity = higher effect)", "🎉 Campaign (Lower sanity = higher effect)"), 0.0, cw, last_camp)
        incite_emo = st.slider(t("🔥 Incite Emotion (Reduces sanity short-term)", "🔥 Incite Emotion (Reduces sanity short-term)"), 0.0, cw, last_incite)
        
    with c2:
        # 🚀 Fix: Placed downgrade button on the right side of the header
        c_dept1, c_dept2 = st.columns([0.65, 0.35])
        c_dept1.markdown(t("#### 🔒 Dept. Investment", "#### 🔒 Dept. Investment"))
        if c_dept2.button(t("Reset to Current Maintenance", "Reset to Current Maintenance"), use_container_width=True):
            st.session_state['up_pre'] = view_party.predict_ability * 10.0
            st.session_state['up_inv'] = view_party.investigate_ability * 10.0
            st.session_state['up_med'] = view_party.media_ability * 10.0
            st.session_state['up_stl'] = view_party.stealth_ability * 10.0
            st.session_state['up_bld'] = view_party.build_ability * 10.0
            st.rerun()

        t_pre, c_pre = ui_core.ability_slider(t("Think Tank (Accurate decay prediction, reduces policy errors)", "Think Tank (Accurate decay prediction, reduces policy errors)"), "up_pre", view_party.predict_ability, cw, cfg, view_party.build_ability, is_build=False)
        t_inv, c_inv = ui_core.ability_slider(t("Intelligence (Catches opp. corruption/cronyism, improves observation accuracy)", "Intelligence (Catches opp. corruption/cronyism, improves observation accuracy)"), "up_inv", view_party.investigate_ability, cw, cfg, view_party.build_ability, is_build=False)
        t_med, c_med = ui_core.ability_slider(t("Media Dept (Amplifies media control, incite, and campaign effects)", "Media Dept (Amplifies media control, incite, and campaign effects)"), "up_med", view_party.media_ability, cw, cfg, view_party.build_ability, is_build=False)
        t_stl, c_stl = ui_core.ability_slider(t("Counter-Intel (Covers own corruption/cronyism, disrupts opp. observation)", "Counter-Intel (Covers own corruption/cronyism, disrupts opp. observation)"), "up_stl", view_party.stealth_ability, cw, cfg, view_party.build_ability, is_build=False)
        t_bld, c_bld = ui_core.ability_slider(t("Engineering (Improves construction output, lowers dept. upgrade costs)", "Engineering (Improves construction output, lowers dept. upgrade costs)"), "up_bld", view_party.build_ability, cw, cfg, view_party.build_ability, is_build=True)

    tot_action = float(media_ctrl) + float(camp_amt) + float(incite_emo) + abs(float(edu_policy_amt)) + float(judicial_amt)
    tot_maint = float(c_inv) + float(c_pre) + float(c_med) + float(c_stl) + float(c_bld)
    tot = req_pay + tot_action + tot_maint
    
    legal_str = t("Legal Project Funds:", "Legal Project Funds:")
    policy_str = t("Policy & Media:", "Policy & Media:")
    dept_str = t("Dept. Investment:", "Dept. Investment:")
    rem_str = t("Remaining Net Available:", "Remaining Net Available:")
    
    st.write(f"**{legal_str}** `{req_pay:.1f}` / **{policy_str}** `{tot_action:.1f}` / **{dept_str}** `{tot_maint:.1f}` / **{rem_str}** `{cw - tot:.1f}`")
    
    if tot > cw:
        st.error(f"{t('🚨 Insufficient Funds! Over budget by', '🚨 Insufficient Funds! Over budget by')} {tot - cw:.1f} {t('dollars, please reduce funding.', 'dollars, please reduce funding.')}")
    
    ra_dummy = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'judicial': judicial_amt}
    ha_dummy = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'corr': h_corr_pct, 'crony': h_crony_pct}
    
    act_ra = ra_dummy if not is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_amt': 0, 'judicial': 0}
    act_ha = ha_dummy if is_h else {'media': 0, 'camp': 0, 'incite': 0, 'corr': 0, 'crony': 0}
    
    if f"{opponent_party.name}_acts" in st.session_state:
        opp_acts = st.session_state[f"{opponent_party.name}_acts"]
        if is_h: act_ra = opp_acts
        else: act_ha = opp_acts

    proj_fund = float(d.get('proj_fund') or 0.0)
    bid_cost = float(d.get('bid_cost') or 1.0)
    claimed_decay = float(d.get('claimed_decay') or 0.0)
    r_pays = float(d.get('r_pays') or 0.0)

    corr_val = float(h_corr_pct) if is_h else 0.0
    crony_val = float(h_crony_pct) if is_h else 0.0
    orig_corr_amt = proj_fund * (corr_val / 100.0)
    orig_crony_income = (proj_fund * (crony_val / 100.0)) * 0.1
    
    res_prev = formulas.calc_economy(cfg, float(game.gdp), float(game.total_budget), proj_fund, bid_cost, float(game.h_role_party.build_ability), float(view_party.current_forecast), corr_amt=orig_corr_amt, r_pays=r_pays, h_wealth=cw if is_h else float(game.h_role_party.wealth))
    h_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == game.h_role_party.name else 0))
    r_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == game.r_role_party.name else 0))
    
    hp_net_est = h_base + res_prev['h_project_profit'] + orig_corr_amt + orig_crony_income
    rp_net_est = r_base + res_prev['payout_r'] - r_pays

    shift_preview = formulas.calc_performance_preview(
        cfg, game.h_role_party, game.r_role_party, game.ruling_party.name,
        res_prev['est_gdp'], game.gdp, 
        claimed_decay, game.sanity, game.emotion, bid_cost, res_prev['c_net']
    )
    
    preview_data = {
        'gdp': res_prev['est_gdp'], 'budg': game.total_budget, 'h_fund': res_prev['payout_h'],
        'san': game.sanity, 'emo': game.emotion,
        'h_inc': hp_net_est, 'r_inc': rp_net_est,
        'my_perf_gdp': shift_preview[view_party.name]['perf_gdp'],
        'my_perf_proj': shift_preview[view_party.name]['perf_proj'],
        'opp_perf_gdp': shift_preview[opponent_party.name]['perf_gdp'],
        'opp_perf_proj': shift_preview[opponent_party.name]['perf_proj']
    }
    
    ui_core.render_dashboard(game, view_party, cfg, is_preview=True, preview_data=preview_data)
    
    if tot <= cw and st.button(t("Confirm & Execute", "Confirm & Execute"), use_container_width=True, type="primary"):
        my_acts = {
            'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 
            'edu_amt': edu_policy_amt, 'judicial': judicial_amt,
            'corr': h_corr_pct, 'crony': h_crony_pct, 
            't_inv': t_inv, 't_pre': t_pre, 't_med': t_med, 't_stl': t_stl, 't_bld': t_bld,
            'legal': req_pay, 'tot_action': tot_action, 'tot_maint': tot_maint
        }
        st.session_state[f"{view_party.name}_acts"] = my_acts
        
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party
            st.rerun()
        else:
            game.phase = 3
            game.proposing_party = game.r_role_party
            st.rerun()
