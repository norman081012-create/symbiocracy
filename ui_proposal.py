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
    st.markdown(f"#### {title}")
    
    c_tog1, c_tog2 = st.columns(2)
    use_tt = c_tog1.toggle("Toggle to Think Tank Estimate (Default: Claimed)", False, key=f"tg_tt_{title}_{plan.get('author', 'sys')}")
    use_claimed = not use_tt
    simulate_swap = c_tog2.toggle("Toggle: Simulate if Swap Happens (Calculated by new roles)", False, key=f"sim_sw_{title}_{plan.get('author', 'sys')}")
    
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
        
        st.write(f"**Claimed Decay Rate:** {cl_decay:.3f}")
        st.write(f"**(Equals {equiv_infra_loss:.1f} infra loss)**")
        st.write(f"**Plan Achievement Reward:** {plan['proj_fund']:.1f} | **Total Plan Benefit:** {plan['bid_cost']:.1f}")
        
        if simulate_swap:
            st.info(f"🔧 **Simulated H-System Subsidy:** Total {eval_req_cost:.1f} (R-Pays: {eval_r_pays:.1f} | H-Pays: {eval_h_pays:.1f})")
        else:
            st.write(f"**Total Required Cost:** {eval_req_cost:.1f} (R-Pays: {eval_r_pays:.1f} | H-Pays: {eval_h_pays:.1f})")
            
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
        
        shift_preview = formulas.calc_performance_amounts(
            cfg, sim_h_party, sim_r_party, sim_ruling_name,
            res['est_gdp'], game.gdp, 
            cl_decay, game.sanity, game.emotion, plan['bid_cost'], res['c_net']
        )
        
        my_perf = shift_preview[view_party.name]['perf']
        opp_perf = shift_preview[sim_r_party.name if my_is_h else sim_h_party.name]['perf']
        proj_perf = shift_preview['project_perf']
        
        base_my_perf = my_perf - (proj_perf if my_is_h else 0.0)
        base_opp_perf = opp_perf - (proj_perf if not my_is_h else 0.0)
        
        o_gdp_pct = ((res['est_gdp'] - game.gdp) / max(1.0, game.gdp)) * 100.0
        def fmt_roi(val): return "∞%" if val == float('inf') else f"{val:+.1f}%"

        st.markdown("### 📝 Think Tank Analysis Report")
        st.markdown(f"1. Our Estimated Total Revenue: **{my_net:.1f}** (Project ROI: {fmt_roi(my_roi)})")
        st.markdown(f"2. Opponent Estimated Total Revenue: **{opp_net:.1f}** (Project ROI: {fmt_roi(opp_roi)})")
        
        st.markdown(f"3. Expected Base Performance (Unfiltered by Media): Us **{base_my_perf:+.1f}** / Opp **{base_opp_perf:+.1f}**")
        st.caption(f"*(⚠️ Draft phase assumes incomplete. If H-System fulfills 100%, an extra `{proj_perf:+.1f}` points will be awarded in Phase 2)*")
        
        st.markdown(f"4. Expected GDP Change: {game.gdp:.1f} ➔ **{res['est_gdp']:.1f}** ({o_gdp_pct:+.2f}%)")
        
        diff = cl_decay - tt_decay
        abs_diff = abs(diff)
        
        author_role = plan.get('author')
        viewer_role = 'H' if my_is_h else 'R'
        is_self = (author_role == viewer_role)

        if abs_diff > 0.3: 
            light = "🔴"
            if is_self:
                if cl_decay > tt_decay: risk_txt = "Brilliant move, sir. Overestimating the decay effectively lowers public expectations. If we exceed targets, we will reap a massive expectation bonus."
                else: risk_txt = "Wise choice, sir. Underestimating the decay paints a rosy picture, but beware of public backlash if the economy falls short."
            else:
                if cl_decay > tt_decay: risk_txt = "Alert! The opponent is maliciously overestimating the decay rate. They aim to create panic, lower expectations, and harvest a contrast bonus!"
                else: risk_txt = "Alert! The opponent is underestimating the decay rate to whitewash the situation. They will face severe backlash if they fail to deliver!"
        elif abs_diff > 0.1: 
            light, risk_txt = "🟡", "Medium Risk (Claimed decay slightly differs from expectations, may affect voter psychology)"
        else: 
            light, risk_txt = "🟢", "Minimal Difference (Honest decay claim, no room for psychological manipulation)"
            
        st.markdown(f"5. Decay Value Analysis: {light} {risk_txt} (Claimed: {cl_decay:.3f} / Think Tank: {tt_decay:.3f})")
        
        diff_c = cl_cost - tt_unit_cost
        abs_diff_c = abs(diff_c)

        if abs_diff_c > 0.5:
            light_c = "🔴"
            if is_self:
                if cl_cost > tt_unit_cost: risk_txt_c = "Copy that, sir. Over-reporting unit costs gives us more operational leeway."
                else: risk_txt_c = "Sir, under-reporting unit costs shows administrative efficiency, but squeezing the budget might lead to construction risks."
            else:
                if cl_cost > tt_unit_cost:
                    risk_txt_c = "Opponent (H) intends to pocket excess construction funds!" if author_role == 'H' else "Opponent (R) is maliciously inflating the base unit cost to set a budget hurdle!"
                else:
                    risk_txt_c = "Opponent (H) is trying to hide low efficiency!" if author_role == 'H' else "Opponent (R) is maliciously underestimating the unit cost to exploit our budget!"
        elif abs_diff_c > 0.2:
            light_c, risk_txt_c = "🟡", "Medium Risk (Slight discrepancy in unit cost, watch out for quality issues or budget overruns)"
        else:
            light_c, risk_txt_c = "🟢", "Minimal Difference (Claimed unit cost matches Intel estimates, normal valuation)"

        st.markdown(f"6. Unit Cost Analysis: {light_c} {risk_txt_c} (Claimed: {cl_cost:.2f} / Intel: {tt_unit_cost:.2f})")
