# ==========================================
# ui_proposal.py
# ==========================================
import streamlit as st
import formulas
import ui_core
import config
import i18n
t = i18n.t

def render_proposal_component(title, plan, game, view_party, cfg):
    
    col_left, col_right = st.columns(2)
    
    selected_projects = plan.get('selected_projects', [])
    proj_names_str = ", ".join([p['name'] for p in selected_projects]) if selected_projects else "None"
    
    with col_left:
        st.markdown(f"""
        <div style="border: 2px solid #AAAAAA; padding: 20px; border-radius: 5px; background-color: #1E1E1E; margin-bottom: 20px;">
            <h3 style="text-align: center; color: #FFFFFF;">📜 {t('Reconstruction Contract')}</h3>
            <hr style="border-color: #AAAAAA;">
            <p style="color: #FFFFFF;"><b>{t('Client (Regulator)')}:</b> {game.r_role_party.name}</p>
            <p style="color: #FFFFFF;"><b>{t('Contractor (Executive)')}:</b> {game.h_role_party.name}</p>
            <p style="color: #FFFFFF;"><b>Projects:</b> {proj_names_str}</p>
            <p style="color: #FFFFFF;"><b>{t('Required Total EV')}:</b> {plan.get('bid_cost', 0):.1f} EV</p>
            <hr style="border-color: #AAAAAA;">
            <h4 style="color: #FFFFFF;">Financial Terms</h4>
            <p style="color: #FFFFFF;"><b>{t('Regulator Provision')}:</b> ${plan.get('r_pays', 0):.1f}</p>
            <p style="color: #FFFFFF;"><b>{t('Executive Provision')}:</b> ${plan.get('h_pays', 0):.1f}</p>
            <p style="color: #FFFFFF;"><b>{t('Total Reward Pool')}:</b> ${plan.get('proj_fund', 0):.1f}</p>
            <hr style="border-color: #AAAAAA;">
            <p style="color: #FFFFFF;"><b>Judicial Fine Multiplier:</b> {plan.get('fine_mult', 0.3)}x</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        st.markdown(t("#### 📝 Think Tank Analysis Report"))
        
        c_tog1, c_tog2 = st.columns(2)
        use_tt = c_tog1.toggle(t("Switch to Think Tank Estimate"), False, key=f"tg_tt_{title}_{plan.get('author', 'sys')}")
        use_claimed = not use_tt
        simulate_swap = c_tog2.toggle(t("Simulate Role Swap"), False, key=f"sim_sw_{title}_{plan.get('author', 'sys')}")
        
        if simulate_swap:
            sim_h_party = game.r_role_party
            sim_r_party = game.h_role_party
            sim_ruling_name = game.ruling_party.name 
            my_is_h_in_sim = (view_party.name == sim_h_party.name)
            swap_penalty = game.total_budget * cfg.get('TRUST_BREAK_PENALTY_RATIO', 0.05)
            st.warning("⚠️ Simulating: Evaluating profit and loss from the opponent's perspective.")
        else:
            sim_h_party = game.h_role_party
            sim_r_party = game.r_role_party
            sim_ruling_name = game.ruling_party.name
            my_is_h_in_sim = (view_party.name == sim_h_party.name)
            swap_penalty = 0.0

        tt_decay = view_party.current_forecast
        obs_abis = ui_core.get_observed_abilities(view_party, sim_h_party, game, cfg)
        obs_bld = obs_abis.get('build', 3.0)
        
        tt_unit_cost = round(formulas.calc_unit_cost(cfg, game.gdp, obs_bld, tt_decay), 2)
        
        cl_decay = plan.get('claimed_decay', tt_decay)
        cl_cost = plan.get('claimed_cost', tt_unit_cost)

        eval_decay = cl_decay if use_claimed else tt_decay
        eval_cost = cl_cost if use_claimed else tt_unit_cost

        preview_allocations = {p['id']: {'real': p['ev'], 'fake': 0.0} for p in selected_projects}
        
        res = formulas.calc_economy(
            cfg=cfg, gdp=game.gdp, budget_t=game.total_budget, 
            proj_fund=plan.get('proj_fund', 0), total_bid_cost=plan.get('bid_cost', 1), 
            build_abi=sim_h_party.build_ability, real_decay=eval_decay, 
            override_unit_cost=eval_cost, r_pays=plan.get('r_pays', 0), 
            h_wealth=sim_h_party.wealth, c_net_override=None, 
            fake_ev_spent=0.0, fake_ev_safe=0.0, 
            active_projects=selected_projects, allocations=preview_allocations, 
            fake_ev_caught=0.0, current_year=game.year
        )
        
        eval_req_cost = res.get('req_cost', 0.0)          
        eval_r_pays = plan.get('r_pays', 0.0)             
        eval_h_pays = eval_req_cost - eval_r_pays 

        h_base = game.total_budget * (cfg.get('BASE_INCOME_RATIO', 0.05) + (cfg.get('RULING_BONUS_RATIO', 0.1) if sim_ruling_name == sim_h_party.name else 0))
        r_base = game.total_budget * (cfg.get('BASE_INCOME_RATIO', 0.05) + (cfg.get('RULING_BONUS_RATIO', 0.1) if sim_ruling_name == sim_r_party.name else 0))
        
        h_project_profit = res.get('h_project_profit', 0.0)
        r_project_profit = res.get('payout_r', 0.0) - eval_r_pays
        
        my_net = (h_base + h_project_profit if my_is_h_in_sim else r_base + r_project_profit) - swap_penalty
        opp_net = (r_base + r_project_profit if my_is_h_in_sim else h_base + h_project_profit) - swap_penalty
        
        o_h_roi = (h_project_profit / float(eval_h_pays)) * 100.0 if eval_h_pays > 0 else float('inf')
        o_r_roi = (r_project_profit / float(eval_r_pays)) * 100.0 if eval_r_pays > 0 else float('inf')
        
        my_roi = o_h_roi if my_is_h_in_sim else o_r_roi
        opp_roi = o_r_roi if my_is_h_in_sim else o_h_roi
        
        ha = st.session_state.get(f"{sim_h_party.name}_acts", {})
        ra = st.session_state.get(f"{sim_r_party.name}_acts", {})
        
        h_spin_pwr = float(ha.get('alloc_med_control', 0.0)) + float(ha.get('alloc_med_camp', 0.0))
        r_spin_pwr = float(ra.get('alloc_med_control', 0.0)) + float(ra.get('alloc_med_camp', 0.0))
        
        # 🛡️ 呼叫終極防呆版的 preview
        shift_preview = formulas.calc_performance_preview(
            cfg=cfg, hp=sim_h_party, rp=sim_r_party, ruling_party_name=sim_ruling_name,
            curr_gdp=game.gdp, claimed_decay=cl_decay, sanity=game.sanity, emotion=game.emotion, 
            projects=res.get('completed_projects', []), h_spin_pwr=h_spin_pwr, r_spin_pwr=r_spin_pwr, 
            real_decay=eval_decay, current_year=game.year
        )
        
        opp_party_name = sim_r_party.name if my_is_h_in_sim else sim_h_party.name
        
        my_total_perf = shift_preview.get(view_party.name, {}).get('perf', 0.0)
        my_total_spin = shift_preview.get(view_party.name, {}).get('spin', 0.0)
        
        opp_total_perf = shift_preview.get(opp_party_name, {}).get('perf', 0.0)
        opp_total_spin = shift_preview.get(opp_party_name, {}).get('spin', 0.0)

        o_gdp_pct = ((res.get('est_gdp', game.gdp) - game.gdp) / max(1.0, game.gdp)) * 100.0
        def fmt_roi(val): return "∞%" if val == float('inf') else f"{val:+.1f}%"

        st.markdown(f"1. {t('Our Est. Net Profit')}: **{my_net:.1f}** (ROI: {fmt_roi(my_roi)})")
        st.markdown(f"2. {t('Opp. Est. Net Profit')}: **{opp_net:.1f}** (ROI: {fmt_roi(opp_roi)})")
        
        my_role = "Executive" if my_is_h_in_sim else "Regulator"
        opp_role = "Regulator" if my_role == "Executive" else "Executive"

        st.markdown(f"3. {t('Total Expected Support')}:")
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🔹 **{t('Our Side')} ({t(my_role)}):** {t('Perf.')} `{my_total_perf:+.1f}` | {t('Spin')} `{my_total_spin:+.1f}`")
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🔸 **{t('Opp. Side')} ({t(opp_role)}):** {t('Perf.')} `{opp_total_perf:+.1f}` | {t('Spin')} `{opp_total_spin:+.1f}`")
        
        st.markdown(f"4. {t('Expected GDP Shift')}: {game.gdp:.1f} ➔ **{res.get('est_gdp', game.gdp):.1f}** ({o_gdp_pct:+.2f}%)")
        
        is_self_draft = (plan.get('author_party') == view_party.name)
        diff = cl_decay - tt_decay
        if abs(diff) > 0.3: 
            light = "🔴"
            if is_self_draft: risk_txt = "Contrast strategy applied."
            else: risk_txt = "Warning: Opponent manipulating expectations."
        elif abs(diff) > 0.1: light, risk_txt = "🟡", "Medium Gap"
        else: light, risk_txt = "🟢", "Honest & Accurate"
            
        st.markdown(f"5. {t('Drop Analysis')}: {light} {t(risk_txt)} (Claimed: {cl_decay:.3f} / TT: {tt_decay:.3f})")
        
        diff_c = cl_cost - tt_unit_cost
        if abs(diff_c) > 0.5:
            light_c = "🔴"
            if is_self_draft: risk_txt_c = "Pricing for future options."
            else: risk_txt_c = "Price detached from real costs."
        elif abs(diff_c) > 0.2: light_c, risk_txt_c = "🟡", "Price Deviation"
        else: light_c, risk_txt_c = "🟢", "Fair Market Value"

        st.markdown(f"6. {t('Unit Cost Analysis')}: {light_c} {t(risk_txt_c)} (Claimed: {cl_cost:.2f} / TT Base: {tt_unit_cost:.2f})")
