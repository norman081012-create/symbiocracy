# ==========================================
# phase2.py
# ==========================================
import streamlit as st
import config
import formulas
import ui_core
import i18n
t = i18n.t

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    h_label = t('🛡️ H-System')
    r_label = t('⚖️ R-System')
    st.subheader(f"{t('🛠️ Phase 2: Execution - Turn:')} {view_party.name} ({h_label if is_h else r_label})")
    
    if not hasattr(view_party, 'edu_stance'): view_party.edu_stance = 0.0
    if not hasattr(opponent_party, 'edu_stance'): opponent_party.edu_stance = 0.0
    
    d = st.session_state.get('turn_data', {})
    req_pay = float(d.get('h_pays') or 0.0) if is_h else float(d.get('r_pays') or 0.0)
    cw = max(0.0, float(view_party.wealth))
    proj_fund = float(d.get('proj_fund') or 0.0)
    inflation = max(0.0, (game.gdp - cfg.get('CURRENT_GDP', 5000.0)) / cfg.get('GDP_INFLATION_DIVISOR', 10000.0))
    
    h_corr_amt = 0.0
    h_crony_amt = 0.0
    
    old_jud = float(view_party.last_acts.get('judicial_lvl', 0.0)) if not is_h else 0.0
    old_edu = float(view_party.edu_stance)
    
    judicial_lvl = old_jud
    new_edu = old_edu

    last_media = min(float(view_party.last_acts.get('media', 0.0)), cw)
    last_camp = min(float(view_party.last_acts.get('camp', 0.0)), cw)
    last_incite = min(float(view_party.last_acts.get('incite', 0.0)), cw)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(t("#### 📣 Policy & Media"))
        if is_h: st.caption(t("💡 **H-System Perk**: Media Control x1.2"))
        else: st.caption(t("💡 **R-System Perk**: Intelligence x1.2"))
        
        if is_h:
            st.markdown("##### 🕵️ Under-the-Table Operations")
            my_stl_pct = view_party.stealth_ability / 10.0
            opp_inv_obs = ui_core.get_observed_abilities(view_party, opponent_party, game, cfg)['investigate'] / 10.0
            est_catch_mult = max(0.1, (opp_inv_obs * cfg['R_INV_BONUS']) - my_stl_pct + 1.0)
            
            last_corr = min(float(view_party.last_acts.get('corr_amt', 0.0)), proj_fund)
            h_corr_amt = st.slider(t("💸 Secret Corruption ($)"), 0.0, proj_fund, last_corr, 1.0)
            
            corr_catch_ratio = min(1.0, cfg.get('CATCH_RATE_PER_DOLLAR', 0.10) * est_catch_mult)
            est_caught_amt = h_corr_amt * corr_catch_ratio
            est_fine = est_caught_amt * cfg.get('CORRUPTION_FINE_MULT', 0.4)
            est_net_corr = h_corr_amt - est_caught_amt - est_fine
            
            risk_color = "red" if corr_catch_ratio > 0.5 else "orange" if corr_catch_ratio > 0.2 else "green"
            st.caption(f"*(⚠️ Est. Seizure Rate: <span style='color:{risk_color}'>`{corr_catch_ratio*100:.1f}%`</span> | Est. Net Profit: `${est_net_corr:.1f}`)*", unsafe_allow_html=True)
            
            max_crony = max(0.0, proj_fund - h_corr_amt)
            last_crony = min(float(view_party.last_acts.get('crony_amt', 0.0)), max_crony)
            h_crony_amt = st.slider(t("🏢 Cronyism ($)"), 0.0, max_crony, last_crony, 1.0)
            
            crony_catch_ratio = min(1.0, cfg.get('CRONY_CATCH_RATE_DOLLAR', 0.05) * est_catch_mult)
            crony_profit_rate = cfg.get('CRONY_PROFIT_RATE', 0.2)
            
            total_crony_profit = h_crony_amt * crony_profit_rate
            est_crony_caught_profit = total_crony_profit * crony_catch_ratio
            est_crony_fine = est_crony_caught_profit * 1.5 
            est_net_crony = total_crony_profit - est_crony_caught_profit - est_crony_fine
            
            risk_color_c = "red" if crony_catch_ratio > 0.5 else "orange" if crony_catch_ratio > 0.2 else "green"
            st.caption(f"*(⚠️ Est. Crony Seizure Rate: <span style='color:{risk_color_c}'>`{crony_catch_ratio*100:.1f}%`</span> | Est. Net Profit: `${est_net_crony:.1f}`)*", unsafe_allow_html=True)

        else:
            st.markdown("##### 🎓 Ideology & Media Censorship")
            # 🚀 便宜的二次方維護費邏輯 (Max = 20)
            judicial_lvl = st.slider(t("⚖️ Media Censorship (0~100)"), 0.0, 100.0, float(old_jud), 1.0)
            judicial_cost = (judicial_lvl / 10.0) ** 2 * 2.0 
            
            # 🚀 每年限制更動 10 級
            min_edu = max(-100.0, old_edu - 10.0)
            max_edu = min(100.0, old_edu + 10.0)
            new_edu = st.slider(t("🎓 Education Policy (Left: Rote | Right: Critical)"), float(min_edu), float(max_edu), float(old_edu), 1.0)
            edu_maint_cost = (abs(new_edu) / 10.0) ** 2 * 2.0
            
            st.caption(f"💰 Maint. Costs: Judicial `${judicial_cost:.1f}` | Education `${edu_maint_cost:.1f}`")
            
        st.markdown("##### 📺 Campaigns & Public Relations")
        st.caption(f"*(Benefits from **{cfg.get('PR_EFFICIENCY_MULT', 3.0)}x** PR conversion efficiency)*")
        media_amt = st.slider(t("📺 Media Control ($)"), 0.0, cw, last_media)
        camp_amt = st.slider(t("🎉 Campaign ($)"), 0.0, cw, last_camp)
        incite_amt = st.slider(t("🔥 Incite Emotion ($)"), 0.0, cw, last_incite)
        
    with c2:
        c_dept1, c_dept2 = st.columns([0.65, 0.35])
        c_dept1.markdown(t("#### 🔒 Dept. Investment"))
        
        if c_dept2.button(t("🔄 Reset to Current Maintenance"), use_container_width=True):
            st.session_state[f'up_pre_{view_party.name}_{game.year}'] = view_party.predict_ability * 10.0
            st.session_state[f'up_inv_{view_party.name}_{game.year}'] = view_party.investigate_ability * 10.0
            st.session_state[f'up_med_{view_party.name}_{game.year}'] = view_party.media_ability * 10.0
            st.session_state[f'up_stl_{view_party.name}_{game.year}'] = view_party.stealth_ability * 10.0
            st.session_state[f'up_bld_{view_party.name}_{game.year}'] = view_party.build_ability * 10.0
            st.rerun()

        t_pre, c_pre = ui_core.ability_slider(t("Think Tank"), f"up_pre_{view_party.name}_{game.year}", view_party.predict_ability, cw, cfg, view_party.build_ability, is_build=False)
        t_inv, c_inv = ui_core.ability_slider(t("Intelligence"), f"up_inv_{view_party.name}_{game.year}", view_party.investigate_ability, cw, cfg, view_party.build_ability, is_build=False)
        t_med, c_med = ui_core.ability_slider(t("Media Dept"), f"up_med_{view_party.name}_{game.year}", view_party.media_ability, cw, cfg, view_party.build_ability, is_build=False)
        t_stl, c_stl = ui_core.ability_slider(t("Counter-Intel"), f"up_stl_{view_party.name}_{game.year}", view_party.stealth_ability, cw, cfg, view_party.build_ability, is_build=False)
        t_bld, c_bld = ui_core.ability_slider(t("Engineering"), f"up_bld_{view_party.name}_{game.year}", view_party.build_ability, cw, cfg, view_party.build_ability, is_build=True)

    tot_action = media_amt + camp_amt + incite_amt
    refund_action = abs(min(0.0, c_inv)) + abs(min(0.0, c_pre)) + abs(min(0.0, c_med)) + abs(min(0.0, c_stl)) + abs(min(0.0, c_bld))
    
    edu_maint_cost = (abs(new_edu) / 10.0) ** 2 * 2.0 if not is_h else 0.0
    judicial_cost = (judicial_lvl / 10.0) ** 2 * 2.0 if not is_h else 0.0
    
    tot_maint = float(max(0.0, c_inv)) + float(max(0.0, c_pre)) + float(max(0.0, c_med)) + float(max(0.0, c_stl)) + float(max(0.0, c_bld)) + edu_maint_cost + judicial_cost
    
    tot_spending_now = tot_action + tot_maint - refund_action
    
    st.write(f"**PR Costs:** `{tot_action:.1f}` / **Dept. Maint:** `{tot_maint:.1f}` / **Downgrade Refunds:** `+{refund_action:.1f}` / **Avail. Cash:** `{cw - tot_spending_now:.1f}`")
    st.info(f"📌 **Legal Promises (`{req_pay:.1f}`) will be deducted from Next Year's Base Income, not current cash.**")
    
    if tot_spending_now > cw:
        st.error(f"🚨 Insufficient Funds! Over budget by {tot_spending_now - cw:.1f}. Lower investments.")
    
    my_acts_temp = {
        'media': media_amt, 'camp': camp_amt, 'incite': incite_amt,
        'edu_stance': new_edu, 'judicial_lvl': judicial_lvl, 
        'corr_amt': h_corr_amt, 'crony_amt': h_crony_amt
    }
    
    if is_h:
        act_ha = my_acts_temp
        act_ra = st.session_state.get(f"{opponent_party.name}_acts", {'media': 0, 'camp': 0, 'incite': 0, 'edu_stance': opponent_party.edu_stance, 'judicial_lvl': 0})
    else:
        act_ra = my_acts_temp
        act_ha = st.session_state.get(f"{opponent_party.name}_acts", {'media': 0, 'camp': 0, 'incite': 0, 'corr_amt': 0, 'crony_amt': 0})

    bid_cost = float(d.get('bid_cost') or 1.0)
    claimed_decay = float(d.get('claimed_decay') or 0.0)
    r_pays = float(d.get('r_pays') or 0.0)

    orig_corr_amt = float(act_ha.get('corr_amt', 0.0))
    orig_crony_income = float(act_ha.get('crony_amt', 0.0)) * cfg.get('CRONY_PROFIT_RATE', 0.2)
    
    h_base_expected = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == game.h_role_party.name else 0))
    expected_h_wealth = cw - tot_spending_now + h_base_expected if is_h else float(game.h_role_party.wealth)
    
    res_prev = formulas.calc_economy(cfg, float(game.gdp), float(game.total_budget), proj_fund, bid_cost, float(game.h_role_party.build_ability), float(view_party.current_forecast), corr_amt=orig_corr_amt, r_pays=r_pays, h_wealth=expected_h_wealth)
    h_base = h_base_expected
    r_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == game.r_role_party.name else 0))
    
    hp_net_est = h_base + res_prev['h_project_profit'] + orig_corr_amt + orig_crony_income
    rp_net_est = r_base + res_prev['payout_r'] - r_pays

    eval_req_cost = res_prev['req_cost']
    eval_r_pays = r_pays
    eval_h_pays = eval_req_cost - eval_r_pays
    
    o_h_roi = (res_prev['h_project_profit'] / eval_h_pays) * 100.0 if eval_h_pays > 0 else float('inf')
    o_r_roi = ((res_prev['payout_r'] - eval_r_pays) / eval_r_pays) * 100.0 if eval_r_pays > 0 else float('inf')

    cramming_factor = max(0.0, (50.0 - game.sanity) / 100.0) 
    emo_factor = game.emotion / 100.0
    media_multiplier = max(0.1, 1.0 + cramming_factor + emo_factor)
    
    sim_judicial_lvl = float(act_ra.get('judicial_lvl', 0.0))
    h_censor_penalty = max(0.1, 1.0 - (sim_judicial_lvl / 100.0)) 
    
    pr_mult = cfg.get('PR_EFFICIENCY_MULT', 3.0)
    h_media_pwr = float(act_ha.get('media', 0.0)) * pr_mult * (game.h_role_party.media_ability / 10.0) * cfg.get('H_MEDIA_BONUS', 1.2) * media_multiplier * h_censor_penalty
    r_media_pwr = float(act_ra.get('media', 0.0)) * pr_mult * (game.r_role_party.media_ability / 10.0) * media_multiplier

    shift_preview = formulas.calc_performance_preview(
        cfg, game.h_role_party, game.r_role_party, game.ruling_party.name,
        res_prev['est_gdp'], game.gdp, 
        claimed_decay, game.sanity, game.emotion, bid_cost, res_prev['c_net'],
        h_media_pwr, r_media_pwr
    )
    
    preview_data = {
        'gdp': res_prev['est_gdp'], 'budg': game.total_budget, 'h_fund': res_prev['payout_h'],
        'san': game.sanity, 'emo': game.emotion,
        'h_inc': hp_net_est, 'r_inc': rp_net_est,
        'my_roi': o_h_roi if is_h else o_r_roi,
        'opp_roi': o_r_roi if is_h else o_h_roi,
        'my_perf_gdp': shift_preview[view_party.name]['perf_gdp'],
        'my_perf_proj': shift_preview[view_party.name]['perf_proj'],
        'opp_perf_gdp': shift_preview[opponent_party.name]['perf_gdp'],
        'opp_perf_proj': shift_preview[opponent_party.name]['perf_proj']
    }
    
    ui_core.render_dashboard(game, view_party, cfg, is_preview=True, preview_data=preview_data)
    
    if tot_spending_now <= cw and st.button(t("Confirm Action & Execute"), use_container_width=True, type="primary"):
        my_acts = {
            'media': media_amt, 'camp': camp_amt, 'incite': incite_amt,
            'edu_stance': new_edu, 'judicial_lvl': judicial_lvl, 
            'corr_amt': h_corr_amt, 'crony_amt': h_crony_amt, 
            't_inv': t_inv, 't_pre': t_pre, 't_med': t_med, 't_stl': t_stl, 't_bld': t_bld,
            'legal': req_pay, 'tot_action': tot_action, 'tot_maint': tot_maint, 'refund_action': refund_action
        }
        st.session_state[f"{view_party.name}_acts"] = my_acts
        
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party
            st.rerun()
        else:
            game.phase = 3
            game.proposing_party = game.r_role_party
            st.rerun()
