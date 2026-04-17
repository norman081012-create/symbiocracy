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
    obs_bld = obs_abis['build']
    
    tt_unit_cost = round(formulas.calc_unit_cost(cfg, game.gdp, obs_bld, tt_decay), 2)
    
    cl_decay = plan.get('claimed_decay', tt_decay)
    cl_cost = plan.get('claimed_cost', tt_unit_cost)

    eval_decay = cl_decay if use_claimed else tt_decay
    eval_cost = cl_cost if use_claimed else tt_unit_cost

    res = formulas.calc_economy(cfg, game.gdp, game.total_budget, plan['proj_fund'], plan['bid_cost'], sim_h_party.build_ability, eval_decay, override_unit_cost=eval_cost, r_pays=plan['r_pays'], h_wealth=sim_h_party.wealth)
    
    eval_req_cost = res['req_cost']          
    eval_r_pays = plan['r_pays']             
    eval_h_pays = eval_req_cost - eval_r_pays 

    h_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if sim_ruling_name == sim_h_party.name else 0))
    r_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if sim_ruling_name == sim_r_party.name else 0))
    
    h_project_profit = res['h_project_profit']
    r_project_profit = res['payout_r'] - eval_r_pays
    
    my_net = (h_base + h_project_profit if my_is_h_in_sim else r_base + r_project_profit) - swap_penalty
    opp_net = (r_base + r_project_profit if my_is_h_in_sim else h_base + h_project_profit) - swap_penalty
    
    o_h_roi = (h_project_profit / float(eval_h_pays)) * 100.0 if eval_h_pays > 0 else float('inf')
    o_r_roi = (r_project_profit / float(eval_r_pays)) * 100.0 if eval_r_pays > 0 else float('inf')
    
    my_roi = o_h_roi if my_is_h_in_sim else o_r_roi
    opp_roi = o_r_roi if my_is_h_in_sim else o_h_roi
    
    cramming_factor = max(0.0, (50.0 - game.sanity) / 100.0) 
    emo_factor = game.emotion / 100.0
    media_multiplier = max(0.1, 1.0 + cramming_factor + emo_factor)
    
    ha = st.session_state.get(f"{sim_h_party.name}_acts", {})
    ra = st.session_state.get(f"{sim_r_party.name}_acts", {})
    
    sim_judicial_lvl = float(ra.get('alloc_inv_censor', 0.0))
    h_censor_penalty = max(0.1, 1.0 - (sim_judicial_lvl / 100.0)) 
    
    pr_mult = cfg.get('PR_EFFICIENCY_MULT', 3.0)
    h_media_pwr = float(ha.get('alloc_med_control', 0.0)) * pr_mult * media_multiplier * h_censor_penalty
    r_media_pwr = float(ra.get('alloc_med_control', 0.0)) * pr_mult * media_multiplier
    
    avg_edu_stance = (sim_h_party.edu_stance + sim_r_party.edu_stance) / 2.0

    shift_preview = formulas.calc_performance_preview(
        cfg, sim_h_party, sim_r_party, sim_ruling_name,
        res['est_gdp'], game.gdp, 
        cl_decay, game.sanity, game.emotion, plan['bid_cost'], res['c_net_total'],
        h_media_pwr, r_media_pwr, avg_edu_stance
    )
    
    opp_party_name = sim_r_party.name if my_is_h_in_sim else sim_h_party.name
    
    my_total_perf = shift_preview[view_party.name]['perf']
    my_total_spin = shift_preview[view_party.name]['spin']
    
    opp_total_perf = shift_preview[opp_party_name]['perf']
    opp_total_spin = shift_preview[opp_party_name]['spin']

    o_gdp_pct = ((res['est_gdp'] - game.gdp) / max(1.0, game.gdp)) * 100.0
    def fmt_roi(val): return "∞%" if val == float('inf') else f"{val:+.1f}%"

    st.markdown(f"1. {t('Our Est. Net Profit')}: **{my_net:.1f}** (ROI: {fmt_roi(my_roi)})")
    st.markdown(f"2. {t('Opp. Est. Net Profit')}: **{opp_net:.1f}** (ROI: {fmt_roi(opp_roi)})")
    
    my_role = "Executive" if my_is_h_in_sim else "Regulator"
    opp_role = "Regulator" if my_role == "Executive" else "Executive"
    
    my_perf_type = "Proj Perf." if my_role == "Executive" else "Macro Perf."
    opp_perf_type = "Macro Perf." if my_role == "Executive" else "Proj Perf."

    st.markdown(f"3. {t('Total Expected Support')}:")
    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🔹 **{t('Our Side')} ({t(my_role)}):** {t(my_perf_type)} `{my_total_perf:+.1f}` | {t('Spin')} `{my_total_spin:+.1f}`")
    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🔸 **{t('Opp. Side')} ({t(opp_role)}):** {t(opp_perf_type)} `{opp_total_perf:+.1f}` | {t('Spin')} `{opp_total_spin:+.1f}`")
    
    st.markdown(f"4. {t('Expected GDP Shift')}: {game.gdp:.1f} ➔ **{res['est_gdp']:.1f}** ({o_gdp_pct:+.2f}%)")
    
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

    st.markdown("---")
    st.markdown(f"#### {title}")
    conv_rate = cfg.get('GDP_CONVERSION_RATE', 0.2)
    equiv_infra_loss = (game.gdp * (cl_decay * cfg.get('DECAY_WEIGHT_MULT', 0.05))) / conv_rate
    
    equiv_str = f"Eqv. to {equiv_infra_loss:.1f} EV Loss"
    st.write(f"**{t('Claimed Decay')}:** {cl_decay:.3f} **({t(equiv_str)})**")
    
    st.write(f"**{t('Total Plan Reward (Max=Budget-Salaries)')}:** {plan['proj_fund']:.1f} | **{t('Plan Total Benefit (Construction Volume)')}:** {plan['bid_cost']:.1f}")
    
    if simulate_swap:
        st.info(f"🔧 **Simulated Executive Pays:** {t('Total Req. Cost')} {eval_req_cost:.1f} ({t('Reg-Pays')}: {eval_r_pays:.1f} | {t('Exec-Pays')}: {eval_h_pays:.1f})")
    else:
        st.write(f"**{t('Total Req. Cost')}:** {eval_req_cost:.1f} ({t('Reg-Pays')}: {eval_r_pays:.1f} | {t('Exec-Pays')}: {eval_h_pays:.1f})")
