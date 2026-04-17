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
    h_label = t('🛡️ Executive')
    r_label = t('⚖️ Regulator')
    st.subheader(f"🛠️ Phase 2: Execution & Ops - Turn: {view_party.name} ({h_label if is_h else r_label})")
    
    d = st.session_state.get('turn_data', {})
    req_cost = float(d.get('req_cost', 0.0))
    bid_cost = float(d.get('bid_cost', 1.0))
    
    if is_h: cw = float(view_party.wealth) + float(d.get('r_pays', 0.0))
    else: cw = float(view_party.wealth) - float(d.get('r_pays', 0.0))
    
    h_bonus = 1.2 if is_h else 1.0
    r_bonus = 1.2 if not is_h else 1.0
    
    med_cap = int(view_party.media_ability * 10.0 * r_bonus)
    
    # 📌 Intel 與 Stealth 合併為 Intel & Ops Div.
    inv_cap = int((view_party.investigate_ability + view_party.stealth_ability) * 10.0 * r_bonus) 
    
    # 📌 執行方 (H) 的 Think Tank 產出享有 1.2x 加成
    tt_cap = int(view_party.predict_ability * 10.0 * (1.2 if is_h else 1.0))
    
    eng_base_ev = view_party.build_ability * 10.0 * h_bonus
    eng_limit = 100.0 + (view_party.build_ability * 100.0) * h_bonus
    
    last_acts = view_party.last_acts if hasattr(view_party, 'last_acts') else {}

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(t("#### 📣 Operations Allocation"))
        
        # 1. Think Tank
        st.write(f"**Think Tank Div.** (Capacity: {tt_cap} EP)")
        col_t1, col_t2, col_t3 = st.columns(3)
        w_t_dec = col_t1.number_input("Observe Decay", min_value=0, max_value=tt_cap, value=int(last_acts.get('alloc_tt_dec', 0)), key=f"w_t_dec_{view_party.name}")
        w_t_obs = col_t2.number_input("Observe Proj", min_value=0, max_value=tt_cap, value=int(last_acts.get('alloc_tt_obs', 0)), key=f"w_t_obs_{view_party.name}")
        w_t_opt = col_t3.number_input("Optimize Proj", min_value=0, max_value=tt_cap, value=int(last_acts.get('alloc_tt_opt', 0)), key=f"w_t_opt_{view_party.name}")
        
        tt_used = w_t_dec + w_t_obs + w_t_opt
        tt_invalid = tt_used > tt_cap
        if tt_invalid: st.error(f"Exceeded Think Tank Capacity! ({tt_used}/{tt_cap})")

        # 2. Combined Intel & Ops
        st.write(f"**Intel & Ops Div.** (Capacity: {inv_cap} Ops)")
        col_i1, col_i2, col_i3 = st.columns(3)
        if not is_h:
            w_i_cen = col_i1.number_input("Censorship", min_value=0, max_value=inv_cap, value=int(last_acts.get('alloc_inv_censor', 0)), key=f"w_i_cen_{view_party.name}")
        else:
            w_i_cen = col_i1.number_input("Anti-Censor", min_value=0, max_value=inv_cap, value=int(last_acts.get('alloc_ci_anticen', 0)), key=f"w_c_cen_{view_party.name}")
            
        w_i_org = col_i2.number_input("Audit Org", min_value=0, max_value=inv_cap, value=int(last_acts.get('alloc_inv_audit', 0)), key=f"w_i_org_aud_{view_party.name}")
        w_i_horg = col_i2.number_input("Hide Org", min_value=0, max_value=inv_cap, value=int(last_acts.get('alloc_ci_hideorg', 0)), key=f"w_i_org_hid_{view_party.name}")
        
        w_i_fin = col_i3.number_input("Trace Finances", min_value=0, max_value=inv_cap, value=int(last_acts.get('alloc_inv_fin', 0)), key=f"w_i_fin_trc_{view_party.name}")
        w_i_hfin = col_i3.number_input("Hide Finances", min_value=0, max_value=inv_cap, value=int(last_acts.get('alloc_ci_hidefin', 0)), key=f"w_i_fin_hid_{view_party.name}")
        
        inv_used = w_i_cen + w_i_org + w_i_horg + w_i_fin + w_i_hfin
        inv_invalid = inv_used > inv_cap
        if inv_invalid: st.error(f"Exceeded Intel & Ops Capacity! ({inv_used}/{inv_cap})")

        # 3. Media & PR
        st.write(f"**PR & Media Div.** (Capacity: {med_cap} Power)")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        w_m_cam = col_m1.number_input("Campaign", min_value=0, max_value=med_cap, value=int(last_acts.get('alloc_med_camp', 0)), key=f"w_m_cam_{view_party.name}")
        w_m_inc = col_m2.number_input("Incite", min_value=0, max_value=med_cap, value=int(last_acts.get('alloc_med_incite', 0)), key=f"w_m_inc_{view_party.name}")
        w_m_con = col_m3.number_input("Control", min_value=0, max_value=med_cap, value=int(last_acts.get('alloc_med_control', 0)), key=f"w_m_con_{view_party.name}")
        
        if is_h:
            w_m_edu = col_m4.number_input(t("Edu Shift"), min_value=0, max_value=med_cap, value=int(last_acts.get('alloc_med_edu', 0)), key=f"w_m_edu_{view_party.name}")
        else:
            w_m_edu = 0
            col_m4.write(f"**{t('Edu Shift')}**")
            col_m4.caption("(Executive Only)")
            
        med_used = w_m_cam + w_m_inc + w_m_con + w_m_edu
        med_invalid = med_used > med_cap
        if med_invalid: st.error(f"Exceeded PR & Media Capacity! ({med_used}/{med_cap})")
        
        old_edu_stance = view_party.edu_stance
        if is_h and w_m_edu > 0:
            e_dir = st.radio("Education Direction", ["Shift Left (Rote/Obedience)", "Shift Right (Critical Thinking)"], horizontal=True, key=f"e_dir_{view_party.name}")
            edu_shift = -w_m_edu * 0.5 if "Left" in e_dir else w_m_edu * 0.5
        else:
            edu_shift = 0.0
            
        new_edu_stance = max(-100.0, min(100.0, old_edu_stance + edu_shift))
        st.info(f"Education Stance: `{old_edu_stance:.1f}` ➔ `{new_edu_stance:.1f}`")

    with c2:
        st.markdown(t(f"#### 🔒 Finance & Construction (EV)") + f"  *(Max real EV produced per year: `{eng_limit:.1f}`)*")
        
        c_net_total = 0.0
        fake_ev_total = 0.0
        allocations = {}
        alloc_invalid = False
        
        unit_cost = formulas.calc_unit_cost(cfg, game.gdp, view_party.build_ability, game.current_real_decay)
        proj_fund = float(d.get('proj_fund', 0.0))
        
        if is_h:
            st.markdown(f"**{t('Allocate EV to active projects:')}**")
            if not game.active_projects:
                st.info("No active projects.")
            else:
                for p in game.active_projects:
                    invested = sum(inv.get('real', inv['amount']) + inv.get('fake', 0) for inv in p.get('investments', []))
                    remaining = max(0.0, p['ev'] - invested)
                    min_req = remaining * 0.2
                    
                    est_reward = proj_fund * (p['ev'] / max(1.0, bid_cost))
                    est_my_perf = (p['ev'] * p['exec_mult'] * (5000.0 / game.gdp)) / 20.0
                    est_opp_perf = p['ev'] * p['macro_mult'] * cfg.get('GDP_CONVERSION_RATE', 0.2) / max(1.0, game.gdp) * 100.0 * 0.05 * 50.0
                    
                    st.write(f"**[{p['author'][:1]}] {p['name']}** (Rem: {remaining:.1f} | Min Req: {min_req:.1f})")
                    st.caption(f"🏆 Est. Reward: ${est_reward:.1f} | 📈 Est. Perf (Me: +{est_my_perf:.1f} / Opp: +{est_opp_perf:.1f})")
                    
                    col_p1, col_p2, col_status = st.columns([2, 2, 1])
                    
                    real_alloc = col_p1.number_input(f"{t('Real EV')}", min_value=0.0, max_value=float(remaining*1.5), value=float(min_req), key=f"real_{p['id']}")
                    fake_alloc = col_p2.number_input(f"{t('Fake EV')}", min_value=0.0, max_value=float(remaining*1.5), value=0.0, key=f"fake_{p['id']}")
                    
                    total_eff = real_alloc + fake_alloc
                    eff_survival = real_alloc + (fake_alloc * 0.2)
                    
                    if total_eff + invested >= p['ev'] * 0.99:
                        status = "🟢 Done"
                    elif eff_survival >= min_req - 0.01:
                        status = "🟡 Surv"
                    else:
                        status = "🔴 Fail"
                        
                    col_status.markdown(f"<br>{status}", unsafe_allow_html=True)
                    
                    allocations[p['id']] = {'real': real_alloc, 'fake': fake_alloc}
                    c_net_total += real_alloc
                    fake_ev_total += fake_alloc
            
            project_ev_cost = c_net_total + (fake_ev_total * cfg.get('FAKE_EV_COST_RATIO', 0.2))
        else:
            project_ev_cost = 0.0

        st.markdown(t("##### 🛠️ Upgrade Dept. (Target Level)"))
        
        def render_dept(label, key, obj_val, cap_text_func):
            old_ui_val = obj_val * 10.0
            col_l, col_r = st.columns([1, 2.5])
            with col_l:
                new_ui_val = st.number_input(label, min_value=1.0, value=float(old_ui_val), step=1.0, key=key)
            with col_r:
                old_raw = old_ui_val / 10.0
                new_raw = new_ui_val / 10.0
                maint_now = old_raw * 5.0
                maint_new = new_raw * 5.0
                
                if new_ui_val > old_ui_val:
                    cost = (new_raw**2 - old_raw**2) * 10.0
                    st.caption(f"**Cur:** `{old_ui_val:.0f}` (Maint: -{maint_now:.1f}) ➔ **New:** `{new_ui_val:.0f}` (Maint: -{maint_new:.1f}) | <span style='color:orange'>**Cost:** -{cost:.1f} EV</span>", unsafe_allow_html=True)
                    ev_cost = cost
                    is_up = True
                elif new_ui_val < old_ui_val:
                    refund = (old_raw**2 - new_raw**2) * 5.0
                    st.caption(f"**Cur:** `{old_ui_val:.0f}` (Maint: -{maint_now:.1f}) ➔ **New:** `{new_ui_val:.0f}` (Maint: -{maint_new:.1f}) | <span style='color:blue'>**Refund:** +{refund:.1f} EV</span>", unsafe_allow_html=True)
                    ev_cost = -refund
                    is_up = False
                else:
                    st.caption(f"**Cur:** `{old_ui_val:.0f}` (Maint: -{maint_now:.1f}) ➔ **Unchanged**", unsafe_allow_html=True)
                    ev_cost = 0.0
                    is_up = False

            return new_raw, ev_cost, maint_new, (ev_cost if is_up else 0.0)

        t_pre, pre_cost, pre_maint, pre_up = render_dept("Think Tank", f"tt_pre_{view_party.name}", view_party.predict_ability, lambda v: f"Generates {v * (1.2 if is_h else 1.0):.1f} EP for prediction & optimization.")
        t_inv, inv_cost, inv_maint, inv_up = render_dept("Intel & Ops", f"tt_inv_{view_party.name}", view_party.investigate_ability, lambda v: f"Generates {v * r_bonus:.1f} Ops.")
        t_med, med_cost, med_maint, med_up = render_dept("PR Media", f"tt_med_{view_party.name}", view_party.media_ability, lambda v: f"Generates {v * r_bonus:.1f} Pwr for PR/Control/Edu.")
        t_bld, bld_cost, bld_maint, bld_up = render_dept("Engineering", f"tt_bld_{view_party.name}", view_party.build_ability, lambda v: f"Unlocks {100.0 + (v * 100.0 * h_bonus):.1f} EV upgrade cap.")

        total_upgrade_cost = pre_cost + inv_cost + med_cost + bld_cost
        total_maint_cost = pre_maint + inv_maint + med_maint + bld_maint
        pure_upgrades = pre_up + inv_up + med_up + bld_up
        
        unit_cost_eff = unit_cost / 1.2 if is_h else unit_cost
        total_ev_required = project_ev_cost + total_maint_cost + total_upgrade_cost
        invest_wealth = total_ev_required * max(0.01, unit_cost_eff)
        
        remaining_wealth = cw - invest_wealth
        
        st.markdown("---")
        st.markdown(t(f"**💰 Financial Checkout**"))
        st.write(f"- Total EV Cost: `{total_ev_required:.1f}` EV *(Effective Unit Rate: `${unit_cost_eff:.2f}`)*")
        st.write(f"- Total Funds Required: `${invest_wealth:.1f}`")
        
        is_invalid = tt_invalid or inv_invalid or med_invalid
        
        if remaining_wealth < 0:
            st.error(t(f"🚨 **Insufficient Funds**: Estimated remainder `${remaining_wealth:.1f}`. Reduce EV spending!"))
            is_invalid = True
        else:
            st.success(t(f"✅ **Est. Remaining Funds:** `${cw:.1f}` - `${invest_wealth:.1f}` = **`${remaining_wealth:.1f}`**"))

        if pure_upgrades > eng_limit:
            st.error(t(f"🚨 Upgrade exceeded cap! Max allowed: `{eng_limit:.1f}`. (Current: `{pure_upgrades:.1f}`)"))
            is_invalid = True

    my_acts = {
        'alloc_tt_dec': float(w_t_dec), 'alloc_tt_obs': float(w_t_obs), 'alloc_tt_opt': float(w_t_opt),
        'alloc_inv_censor': float(w_i_cen) if not is_h else 0.0,
        'alloc_inv_audit': float(w_i_org),
        'alloc_inv_fin': float(w_i_fin),
        'alloc_ci_anticen': float(w_i_cen) if is_h else 0.0,
        'alloc_ci_hideorg': float(w_i_horg),
        'alloc_ci_hidefin': float(w_i_hfin),
        'alloc_med_camp': float(w_m_cam), 'alloc_med_incite': float(w_m_inc), 
        'alloc_med_control': float(w_m_con), 'alloc_med_edu': float(w_m_edu),
        'edu_stance': new_edu_stance, 'fake_ev': fake_ev_total, 'allocations': allocations,
        't_pre': t_pre, 't_inv': t_inv, 't_med': t_med, 't_bld': t_bld,
        'invest_wealth': invest_wealth, 'c_net': c_net_total
    }
    
    st.markdown("---")
    
    if is_h:
        act_ha = my_acts
        act_ra = st.session_state.get(f"{opponent_party.name}_acts", {'alloc_med_control': 0, 'alloc_med_camp': 0, 'alloc_med_incite': 0, 'alloc_inv_censor': 0, 'alloc_inv_fin': 0, 'invest_wealth': 0})
    else:
        act_ra = my_acts
        act_ha = st.session_state.get(f"{opponent_party.name}_acts", {'alloc_med_control': 0, 'alloc_med_camp': 0, 'alloc_med_incite': 0, 'fake_ev': 0, 'c_net': float(d.get('bid_cost') or 1.0), 'alloc_ci_hidefin': 0, 'invest_wealth': 0, 'allocations': {}})

    # --- 以下省略預覽圖表的計算 (因為目前 Phase 2 UI 並沒有顯示完整預覽) ---
    
    if not is_invalid and st.button(t("Confirm Actions"), use_container_width=True, type="primary"):
        st.session_state[f"{view_party.name}_acts"] = my_acts
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party
            st.rerun()
        else:
            game.phase = 3
            game.proposing_party = game.r_role_party
            st.rerun()
