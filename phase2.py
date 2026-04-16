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
    
    d = st.session_state.get('turn_data', {})
    req_cost = float(d.get('req_cost', 0.0))
    bid_cost = float(d.get('bid_cost', 1.0))
    
    if is_h: cw = float(view_party.wealth) + req_cost
    else: cw = float(view_party.wealth)
    
    h_bonus = 1.2 if is_h else 1.0
    r_bonus = 1.2 if not is_h else 1.0
    
    med_cap = view_party.media_ability * 10.0 * h_bonus
    inv_cap = view_party.investigate_ability * 10.0 * r_bonus
    ci_cap = view_party.stealth_ability * 10.0
    edu_cap = view_party.edu_ability * 10.0 * r_bonus
    eng_base_ev = view_party.build_ability * 10.0 * h_bonus
    eng_limit = view_party.build_ability * 10.0 * 2.0  
    
    last_acts = view_party.last_acts if hasattr(view_party, 'last_acts') else {}

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(t("#### 📣 Resource Allocation"))
        
        st.write(f"**{t('Intelligence')} (Capacity: {inv_cap:.1f} EV)**")
        col_i1, col_i2, col_i3 = st.columns(3)
        w_i_cen = col_i1.number_input(t("Media Censorship"), min_value=0, max_value=100, value=last_acts.get('w_i_cen', 0))
        w_i_org = col_i2.number_input(t("Org Audit"), min_value=0, max_value=100, value=last_acts.get('w_i_org', 0))
        w_i_fin = col_i3.number_input(t("Investigate Fin."), min_value=0, max_value=100, value=last_acts.get('w_i_fin', 0))
        i_tot = max(1, w_i_cen + w_i_org + w_i_fin)
        alloc_inv_censor = inv_cap * (w_i_cen / i_tot) if w_i_cen else 0
        alloc_inv_audit = inv_cap * (w_i_org / i_tot) if w_i_org else 0
        alloc_inv_fin = inv_cap * (w_i_fin / i_tot) if w_i_fin else 0
        
        st.write(f"**{t('Counter-Intel')} (Capacity: {ci_cap:.1f} EV)**")
        col_c1, col_c2, col_c3 = st.columns(3)
        w_c_cen = col_c1.number_input(t("Anti-Censorship"), min_value=0, max_value=100, value=last_acts.get('w_c_cen', 0))
        w_c_org = col_c2.number_input(t("Hide Org"), min_value=0, max_value=100, value=last_acts.get('w_c_org', 0))
        w_c_fin = col_c3.number_input(t("Hide Fin."), min_value=0, max_value=100, value=last_acts.get('w_c_fin', 0))
        c_tot = max(1, w_c_cen + w_c_org + w_c_fin)
        alloc_ci_anticen = ci_cap * (w_c_cen / c_tot) if w_c_cen else 0
        alloc_ci_hideorg = ci_cap * (w_c_org / c_tot) if w_c_org else 0
        alloc_ci_hidefin = ci_cap * (w_c_fin / c_tot) if w_c_fin else 0
        
        st.write(f"**{t('Media Dept')} (Capacity: {med_cap:.1f} EV)**")
        col_m1, col_m2, col_m3 = st.columns(3)
        w_m_cam = col_m1.number_input(t("Campaign"), min_value=0, max_value=100, value=last_acts.get('w_m_cam', 0))
        w_m_inc = col_m2.number_input(t("Incite Emotion"), min_value=0, max_value=100, value=last_acts.get('w_m_inc', 0))
        w_m_con = col_m3.number_input(t("Media Control"), min_value=0, max_value=100, value=last_acts.get('w_m_con', 0))
        m_tot = max(1, w_m_cam + w_m_inc + w_m_con)
        alloc_med_camp = med_cap * (w_m_cam / m_tot) if w_m_cam else 0
        alloc_med_incite = med_cap * (w_m_inc / m_tot) if w_m_inc else 0
        alloc_med_control = med_cap * (w_m_con / m_tot) if w_m_con else 0
        
        st.write(f"**{t('Edu Dept')} (Capacity: {edu_cap:.1f} EV)**")
        old_edu_stance = view_party.edu_stance
        e_dir = st.radio(t("Education Shift Direction"), ["Maintain", "Shift Left (Rote)", "Shift Right (Critical)"], horizontal=True)
        if e_dir == "Shift Left (Rote)": edu_shift = -edu_cap * 0.5
        elif e_dir == "Shift Right (Critical)": edu_shift = edu_cap * 0.5
        else: edu_shift = 0.0
        new_edu_stance = max(-100.0, min(100.0, old_edu_stance + edu_shift))
        st.info(f"Education Stance: `{old_edu_stance:.1f}` ➔ `{new_edu_stance:.1f}`")

    with c2:
        st.markdown(t("#### 🔒 Financial & Engineering (EV)"))
        
        h_crony_amt = 0.0
        invest_wealth = 0.0
        total_ev = 0.0
        c_net = 0.0
        
        unit_cost = formulas.calc_unit_cost(cfg, game.gdp, view_party.build_ability, view_party.current_forecast)
        
        if is_h:
            invest_wealth = st.number_input(t("Invest Party Wealth into Engineering ($)"), min_value=0.0, max_value=float(view_party.wealth), value=min(req_cost, float(view_party.wealth)))
            crony_max = min(invest_wealth, req_cost)
            h_crony_amt = st.number_input(t("Cronyism ($)"), min_value=0.0, max_value=float(crony_max), value=float(min(last_acts.get('crony_amt', 0.0), crony_max)))
            
            total_money = invest_wealth - h_crony_amt
            total_ev = total_money / max(0.01, unit_cost)
            
            st.markdown(f"**💰 {t('Total Available EV')}:** `{total_ev:.1f}` EV")
            
            c_net = st.number_input(f"Allocate EV to National Project (Target EV: {bid_cost})", min_value=0.0, max_value=float(total_ev), value=float(min(total_ev, bid_cost)))
            available_upgrade_ev = total_ev - c_net
        else:
            invest_wealth = st.number_input(t("Invest Party Wealth into Engineering ($)"), min_value=0.0, max_value=float(view_party.wealth), value=0.0)
            total_money = invest_wealth
            total_ev = total_money / max(0.01, unit_cost)
            st.markdown(f"**💰 {t('Total Available EV')}:** `{total_ev:.1f}` EV")
            available_upgrade_ev = total_ev

        st.markdown("##### 🛠️ Upgrade Departments (Target Value)")
        st.caption(f"*(All abilities scale from 0 to infinity. Upgrade Costs limited to `{eng_limit:.1f}` EV by Engineering.)*")
        
        def render_dept(label, key, obj_val, cap_text_func):
            old_ui_val = obj_val * 10.0
            col_l, col_r = st.columns([1, 2.5])
            with col_l:
                new_ui_val = st.number_input(label, min_value=1.0, value=float(old_ui_val), step=1.0, key=key)
            with col_r:
                old_raw = old_ui_val / 10.0
                new_raw = new_ui_val / 10.0
                maint_now = old_raw * 1.5
                maint_new = new_raw * 1.5
                
                cost_for_plus_1 = ((old_raw + 0.1)**2 - old_raw**2) * 1.5
                refund_for_minus_1 = (old_raw**2 - max(0.1, old_raw - 0.1)**2) * 0.75
                
                if new_ui_val > old_ui_val:
                    cost = (new_raw**2 - old_raw**2) * 1.5
                    st.caption(f"**Current:** `{old_ui_val:.0f}` (Maint: -{maint_now:.2f}) ➔ **New:** `{new_ui_val:.0f}` (Maint: -{maint_new:.2f}) | <span style='color:orange'>**Upgrade Cost:** -{cost:.2f} EV</span>", unsafe_allow_html=True)
                    ev_cost = cost
                    is_up = True
                elif new_ui_val < old_ui_val:
                    refund = (old_raw**2 - new_raw**2) * 0.75
                    st.caption(f"**Current:** `{old_ui_val:.0f}` (Maint: -{maint_now:.2f}) ➔ **New:** `{new_ui_val:.0f}` (Maint: -{maint_new:.2f}) | <span style='color:blue'>**Downgrade Refund:** +{refund:.2f} EV</span>", unsafe_allow_html=True)
                    ev_cost = -refund
                    is_up = False
                else:
                    st.caption(f"**Current:** `{old_ui_val:.0f}` (Maint: -{maint_now:.2f}) ➔ **Unchanged** | (+1 Cost: `{cost_for_plus_1:.2f}` EV, -1 Refund: `+{refund_for_minus_1:.2f}` EV)", unsafe_allow_html=True)
                    ev_cost = 0.0
                    is_up = False

                st.caption(f"💡 *{cap_text_func(new_ui_val)}*")
            return new_raw, ev_cost, maint_new, (ev_cost if is_up else 0.0)

        t_pre, pre_cost, pre_maint, pre_up = render_dept(t("Think Tank"), "tt_pre", view_party.predict_ability, lambda v: f"Produces {v:.1f} EV for Forecasting Accuracy")
        t_inv, inv_cost, inv_maint, inv_up = render_dept(t("Intelligence"), "tt_inv", view_party.investigate_ability, lambda v: f"Produces {v * r_bonus:.1f} EV for Investigations")
        t_med, med_cost, med_maint, med_up = render_dept(t("Media Dept"), "tt_med", view_party.media_ability, lambda v: f"Produces {v * h_bonus:.1f} EV for PR & Control")
        t_stl, stl_cost, stl_maint, stl_up = render_dept(t("Counter-Intel"), "tt_stl", view_party.stealth_ability, lambda v: f"Produces {v:.1f} EV for Concealment")
        t_bld, bld_cost, bld_maint, bld_up = render_dept(t("Engineering"), "tt_bld", view_party.build_ability, lambda v: f"Produces {v * h_bonus:.1f} Base Construction EV & {v * 2.0:.1f} EV Upgrade Limit")
        t_edu, edu_cost, edu_maint, edu_up = render_dept(t("Edu Dept"), "tt_edu", view_party.edu_ability, lambda v: f"Produces {v * r_bonus:.1f} EV for Ideology Shift")

        total_upgrade_cost = pre_cost + inv_cost + med_cost + stl_cost + bld_cost + edu_cost
        total_maint_cost = pre_maint + inv_maint + med_maint + stl_maint + bld_maint + edu_maint
        pure_upgrades = pre_up + inv_up + med_up + stl_up + bld_up + edu_up
        
        net_ev = available_upgrade_ev - total_maint_cost - total_upgrade_cost
        
        st.write(f"**Total Costs EV:** `{total_maint_cost + total_upgrade_cost:.1f}` (Maint: {total_maint_cost:.1f} + Net Changes: {total_upgrade_cost:.1f})")
        
        is_invalid = False
        if pure_upgrades > eng_limit:
            st.error(f"🚨 Upgrades exceed Engineering Limit! Max upgrade EV allowed: `{eng_limit:.1f}`. (Current pure upgrades: `{pure_upgrades:.1f}`)")
            is_invalid = True
        elif net_ev < 0:
            st.error(f"🚨 Insufficient EV! Deficit of {-net_ev:.1f} EV. Downgrade departments or inject more Party Wealth.")
            is_invalid = True
        else:
            if is_h:
                st.success(f"✅ EV flow is valid. Excess `{net_ev:.1f}` EV will be discarded at year-end.")
            else:
                st.info(f"✅ EV flow is valid. Excess `{net_ev:.1f}` EV will be discarded at year-end.")

    my_acts = {
        'w_i_cen': w_i_cen, 'w_i_org': w_i_org, 'w_i_fin': w_i_fin,
        'alloc_inv_censor': alloc_inv_censor, 'alloc_inv_audit': alloc_inv_audit, 'alloc_inv_fin': alloc_inv_fin,
        'w_c_cen': w_c_cen, 'w_c_org': w_c_org, 'w_c_fin': w_c_fin,
        'alloc_ci_anticen': alloc_ci_anticen, 'alloc_ci_hideorg': alloc_ci_hideorg, 'alloc_ci_hidefin': alloc_ci_hidefin,
        'w_m_cam': w_m_cam, 'w_m_inc': w_m_inc, 'w_m_con': w_m_con,
        'alloc_med_camp': alloc_med_camp, 'alloc_med_incite': alloc_med_incite, 'alloc_med_control': alloc_med_control,
        'edu_stance': new_edu_stance, 'crony_amt': h_crony_amt, 
        't_pre': t_pre, 't_inv': t_inv, 't_med': t_med, 't_stl': t_stl, 't_bld': t_bld, 't_edu': t_edu,
        'invest_wealth': invest_wealth, 'c_net': c_net
    }
    
    st.markdown("---")
    
    if is_h:
        act_ha = my_acts
        act_ra = st.session_state.get(f"{opponent_party.name}_acts", {'alloc_med_control': 0, 'alloc_med_camp': 0, 'alloc_med_incite': 0, 'alloc_inv_censor': 0, 'alloc_inv_fin': 0})
    else:
        act_ra = my_acts
        act_ha = st.session_state.get(f"{opponent_party.name}_acts", {'alloc_med_control': 0, 'alloc_med_camp': 0, 'alloc_med_incite': 0, 'crony_amt': 0, 'c_net': float(d.get('bid_cost') or 1.0), 'alloc_ci_hidefin': 0})

    claimed_decay = float(d.get('claimed_decay') or 0.0)
    r_pays = float(d.get('r_pays') or 0.0)
    proj_fund = float(d.get('proj_fund') or 0.0)
    
    orig_crony_income = float(act_ha.get('crony_amt', 0.0)) * cfg.get('CRONY_PROFIT_RATE', 0.2)
    
    h_base_expected = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == game.h_role_party.name else 0))
    expected_h_wealth = view_party.wealth - act_ha.get('invest_wealth', 0) + req_cost if is_h else float(game.h_role_party.wealth) - float(act_ha.get('invest_wealth', 0)) + req_cost
    
    eval_c_net = float(act_ha.get('c_net', 0))
    
    res_prev = formulas.calc_economy(cfg, float(game.gdp), float(game.total_budget), proj_fund, bid_cost, float(game.h_role_party.build_ability), float(view_party.current_forecast), r_pays=r_pays, h_wealth=expected_h_wealth, c_net_override=eval_c_net)
    
    hp_net_est = h_base_expected + res_prev['h_project_profit'] + orig_crony_income
    rp_net_est = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == game.r_role_party.name else 0)) + res_prev['payout_r'] - r_pays

    eval_req_cost = res_prev['req_cost']
    eval_h_pays = eval_req_cost - r_pays
    
    o_h_roi = (res_prev['h_project_profit'] / eval_h_pays) * 100.0 if eval_h_pays > 0 else float('inf')
    o_r_roi = ((res_prev['payout_r'] - r_pays) / r_pays) * 100.0 if r_pays > 0 else float('inf')

    h_media_pwr = float(act_ha.get('alloc_med_control', 0.0))
    r_media_pwr = float(act_ra.get('alloc_med_control', 0.0))

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
    
    if not is_invalid and st.button(t("Confirm Action & Execute"), use_container_width=True, type="primary"):
        st.session_state[f"{view_party.name}_acts"] = my_acts
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party
            st.rerun()
        else:
            game.phase = 3
            game.proposing_party = game.r_role_party
            st.rerun()
