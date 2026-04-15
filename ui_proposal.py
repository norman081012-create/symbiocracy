# ==========================================
# ui_proposal.py
# Handles Proposal Draft Rendering
# ==========================================
import streamlit as st
import formulas
import ui_core
import config
import i18n
t = i18n.t

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    
    c_tog1, c_tog2 = st.columns(2)
    use_tt = c_tog1.toggle(t("Switch to Think Tank Estimate (Default: Claimed Values)", "Switch to Think Tank Estimate (Default: Claimed Values)"), False, key=f"tg_tt_{title}_{plan.get('author', 'sys')}")
    use_claimed = not use_tt
    simulate_swap = c_tog2.toggle(t("Simulate if Swap Happens (Calculated by new roles)", "Simulate if Swap Happens (Calculated by new roles)"), False, key=f"sim_sw_{title}_{plan.get('author', 'sys')}")
    
    c1, c2 = st.columns(2)
    
    if simulate_swap:
        sim_h_party = game.r_role_party
        sim_r_party = game.h_role_party
        sim_ruling_name = game.party_B.name if game.ruling_party.name == game.party_A.name else game.party_A.name
        my_is_h = (view_party.name == sim_h_party.name)
    else:
        sim_h_party = game.h_role_party
        sim_r_party = game.r_role_party
        sim_ruling_name = game.ruling_party.name
        my_is_h = (view_party.name == sim_h_party.name)

    # === Intelligence Baseline Decoupling ===
    tt_decay = view_party.current_forecast
    obs_abis = ui_core.get_observed_abilities(view_party, sim_h_party, game, cfg)
    obs_bld = obs_abis['build']
    tt_unit_cost = round(formulas.calc_unit_cost(cfg, game.gdp, obs_bld, tt_decay), 2)
    
    cl_decay = plan.get('claimed_decay', tt_decay)
    cl_cost = plan.get('claimed_cost', tt_unit_cost)

    if use_claimed:
        eval_decay = cl_decay
        eval_cost = cl_cost
    else:
        eval_decay = tt_decay
        eval_cost = tt_unit_cost

    res = formulas.calc_economy(cfg, game.gdp, game.total_budget, plan['proj_fund'], plan['bid_cost'], sim_h_party.build_ability, eval_decay, override_unit_cost=eval_cost, r_pays=plan['r_pays'], h_wealth=sim_h_party.wealth)
    
    eval_req_cost = res['req_cost']          
    eval_unit_cost = res.get('unit_cost', 1.0)
    eval_r_pays = plan['r_pays']             
    eval_h_pays = eval_req_cost - eval_r_pays 
    
    with c1:
        conv_rate = cfg.get('GDP_CONVERSION_RATE', 0.2)
        equiv_infra_loss = (game.gdp * (cl_decay * cfg.get('DECAY_WEIGHT_MULT', 0.05) + cfg.get('BASE_DECAY_RATE', 0.0))) / conv_rate
        
        st.write(f"**{t('Claimed Decay', 'Claimed Decay')}:** {cl_decay:.3f}")
        st.write(f"**({t(f'Equivalent to {equiv_infra_loss:.1f} construction loss', f'Equivalent to {equiv_infra_loss:.1f} construction loss')})**")
        st.write(f"**{t('Plan Reward', 'Plan Reward')}:** {plan['proj_fund']:.1f} | **{t('Plan Total Benefit', 'Plan Total Benefit')}:** {plan['bid_cost']:.1f}")
        
        if simulate_swap:
            st.info(f"🔧 **{t('Simulated H-System Pays', 'Simulated H-System Pays')}:** {t('Total', 'Total')} {eval_req_cost:.1f} ({t('R-Pays', 'R-Pays')}: {eval_r_pays:.1f} | {t('H-Pays', 'H-Pays')}: {eval_h_pays:.1f})")
        else:
            st.write(f"**{t('Total Req. Cost', 'Total Req. Cost')}:** {eval_req_cost:.1f} ({t('R-Pays', 'R-Pays')}: {eval_r_pays:.1f} | {t('H-Pays', 'H-Pays')}: {eval_h_pays:.1f})")
            
    with c2:
        h_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if sim_ruling_name == sim_h_party.name else 0))
        r_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if sim_ruling_name == sim_r_party.name else 0))
        
        h_project_profit = res['h_project_profit']
        r_project_profit = res['payout_r'] - eval_r_pays
        
        o_h_roi = (h_project_profit / float(eval_h_pays)) * 100.0 if eval_h_pays > 0 else float('inf')
        o_r_roi = (r_project_profit / float(eval_r_pays)) * 100.0 if eval_r_pays > 0 else float('inf')
        
        my_roi = o_h_roi if my_is_h else o_r_roi
        opp_roi = o_r_roi if my_is_h else o_h_roi
        
        my_net = h_base + h_project_profit if my_is_h else r_base + r_project_profit
        opp_net = r_base + r_project_profit if my_is_h else h_base + h_project_profit
        
        # 🚀 Support 2.0 Update: Call new array preview function
        shift_preview = formulas.calc_performance_preview(
            cfg, sim_h_party, sim_r_party, sim_ruling_name,
            res['est_gdp'], game.gdp, 
            cl_decay, game.sanity, game.emotion, plan['bid_cost'], res['c_net']
        )
        
        opp_party_name = sim_r_party.name if my_is_h else sim_h_party.name
        base_my_perf = shift_preview[view_party.name]['perf_gdp']
        base_opp_perf = shift_preview[opp_party_name]['perf_gdp']
        
        h_gain = shift_preview[sim_h_party.name]['perf_proj']
        r_gain = shift_preview[sim_r_party.name]['perf_proj']
        prob = shift_preview['correct_prob']
        
        o_gdp_pct = ((res['est_gdp'] - game.gdp) / max(1.0, game.gdp)) * 100.0
        def fmt_roi(val): return "∞%" if val == float('inf') else f"{val:+.1f}%"

        st.markdown(t("### 📝 Think Tank Analysis Report", "### 📝 Think Tank Analysis Report"))
        st.markdown(f"1. {t('Our Est. Total Profit', 'Our Est. Total Profit')}: **{my_net:.1f}** (Project ROI: {fmt_roi(my_roi)})")
        st.markdown(f"2. {t('Opp. Est. Total Profit', 'Opp. Est. Total Profit')}: **{opp_net:.1f}** (Project ROI: {fmt_roi(opp_roi)})")
        
        st.markdown(f"3. {t('Expected Base Perf (No Media)', 'Expected Base Perf (No Media)')}: Us **{base_my_perf:+.1f}** / Opp **{base_opp_perf:+.1f}**")
        st.caption(f"*(⚠️ {t('Draft phase does not assume completion. If H-System fulfills 100%, since voter correct attribution rate is just', 'Draft phase does not assume completion. If H-System fulfills 100%, since voter correct attribution rate is just')} `{prob*100:.1f}%`, {t('Expected: H-System gets', 'Expected: H-System gets')} `{h_gain:+.1f}` {t('pts / R-System gets', 'pts / R-System gets')} `{r_gain:+.1f}` {t('pts', 'pts')})*")
        
        st.markdown(f"4. {t('Expected GDP Shift', 'Expected GDP Shift')}: {game.gdp:.1f} ➔ **{res['est_gdp']:.1f}** ({o_gdp_pct:+.2f}%)")
        
        diff = cl_decay - tt_decay
        abs_diff = abs(diff)
        
        author_role = plan.get('author')
        viewer_role = 'H' if my_is_h else 'R'
        is_self = (author_role == viewer_role)

        if abs_diff > 0.3: 
            light = "🔴"
            if is_self:
                if cl_decay > tt_decay: risk_txt = t("Brilliant move, sir. Deliberately overstating the decay lowers public expectations; if we over-deliver, we will harvest a huge expectation bonus.", "Brilliant move, sir. Deliberately overstating the decay lowers public expectations; if we over-deliver, we will harvest a huge expectation bonus.")
                else: risk_txt = t("Wise choice, sir. Understating the decay to paint a rosy picture has its tricks, but if the final economy falls short, we must guard against public backlash.", "Wise choice, sir. Understating the decay to paint a rosy picture has its tricks, but if the final economy falls short, we must guard against public backlash.")
            else:
                if cl_decay > tt_decay: risk_txt = t("Alert! Opponent is maliciously exaggerating the decay rate. They intend to create panic to lower expectations and harvest a contrast bonus!", "Alert! Opponent is maliciously exaggerating the decay rate. They intend to create panic to lower expectations and harvest a contrast bonus!")
                else: risk_txt = t("Based on comparisons, the opponent is maliciously understating the decay rate to whitewash reality. If their administration fails, they will face severe backlash!", "Based on comparisons, the opponent is maliciously understating the decay rate to whitewash reality. If their administration fails, they will face severe backlash!")
        elif abs_diff > 0.1: 
            light, risk_txt = "🟡", t("Medium Risk (Claimed decay differs slightly from expectations, may affect voter psychology)", "Medium Risk (Claimed decay differs slightly from expectations, may affect voter psychology)")
        else: 
            light, risk_txt = "🟢", t("Minimal Difference (Claimed decay is honest, no room for psychological manipulation)", "Minimal Difference (Claimed decay is honest, no room for psychological manipulation)")
            
        st.markdown(f"5. {t('Drop Analysis', 'Drop Analysis')}: {light} {risk_txt} ({t('Claimed', 'Claimed')}: {cl_decay:.3f} / {t('Think Tank', 'Think Tank')}: {tt_decay:.3f})")
        
        diff_c = cl_cost - tt_unit_cost
        abs_diff_c = abs(diff_c)

        if abs_diff_c > 0.5:
            light_c = "🔴"
            if is_self:
                if cl_cost > tt_unit_cost: risk_txt_c = t("Understood, sir. Inflating the unit cost will give us more flexible operational space.", "Understood, sir. Inflating the unit cost will give us more flexible operational space.")
                else: risk_txt_c = t("Sir, deliberately low-balling the unit cost shows administrative efficiency, but excessively squeezing the budget might trigger engineering hazards.", "Sir, deliberately low-balling the unit cost shows administrative efficiency, but excessively squeezing the budget might trigger engineering hazards.")
            else:
                if cl_cost > tt_unit_cost:
                    risk_txt_c = t("Opponent (H-System) intends to pocket excess engineering funds!", "Opponent (H-System) intends to pocket excess engineering funds!") if author_role == 'H' else t("Opponent (R-System) is maliciously inflating the baseline unit cost to create a budget hurdle!", "Opponent (R-System) is maliciously inflating the baseline unit cost to create a budget hurdle!")
                else:
                    risk_txt_c = t("Opponent (H-System) is trying to hide low efficiency!", "Opponent (H-System) is trying to hide low efficiency!") if author_role == 'H' else t("Opponent (R-System) is maliciously low-balling the unit cost to exploit our budget!", "Opponent (R-System) is maliciously low-balling the unit cost to exploit our budget!")
        elif abs_diff_c > 0.2:
            light_c, risk_txt_c = "🟡", t("Medium Risk (Unit cost differs slightly, keep an eye on project quality or overspending)", "Medium Risk (Unit cost differs slightly, keep an eye on project quality or overspending)")
        else:
            light_c, risk_txt_c = "🟢", t("Minimal Difference (Claimed unit cost matches intel estimates, standard valuation)", "Minimal Difference (Claimed unit cost matches intel estimates, standard valuation)")

        st.markdown(f"6. {t('Unit Cost Analysis', 'Unit Cost Analysis')}: {light_c} {risk_txt_c} ({t('Claimed', 'Claimed')}: {cl_cost:.2f} / {t('Intel', 'Intel')}: {tt_unit_cost:.2f})")
