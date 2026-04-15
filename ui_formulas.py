# ==========================================
# ui_formulas.py
# ==========================================
import streamlit as st
import formulas
import ui_core
import i18n

t = i18n.t

def render_formula_panel(game, view_party, cfg):
    with st.expander(t("🧮 Think Tank Formula & Calculation Monitor"), expanded=False):
        plan = None
        is_selected = False
        
        if game.phase == 1:
            if getattr(game, 'p1_selected_plan', None):
                plan = game.p1_selected_plan
                is_selected = True
            else:
                active_role = 'R' if game.p1_step in ['draft_r', 'ultimatum_draft_r'] else 'H'
                plan = game.p1_proposals.get(active_role)
        elif game.phase >= 2:
            plan = st.session_state.get('turn_data')
            is_selected = True

        TAG_EST = " (Est)"  
        TAG_TMP = " (Tmp)"  
        TAG_CFM = " (Cfm)"  
        TAG_CON = " (Const)"  

        gdp_val = game.gdp
        gdp_str = f"{gdp_val:.1f}{TAG_CFM}"
        
        decay_val = view_party.current_forecast
        decay_str = f"{decay_val:.3f}{TAG_EST}"
        
        is_simulating = st.session_state.get("sim_sw_📜 Current Draft Preview_R") or st.session_state.get("sim_sw_📜 Opponent Draft Ref._H")
        if is_simulating:
            active_h = game.r_role_party
        else:
            active_h = game.h_role_party
            
        obs_abis = ui_core.get_observed_abilities(view_party, active_h, game, cfg)
        build_val = obs_abis['build']
        is_my_h = (view_party.name == active_h.name)
        build_tag = TAG_CFM if (is_my_h or st.session_state.get('god_mode')) else TAG_EST
        build_str = f"{build_val:.1f}{build_tag}"
        
        h_wealth_val = active_h.wealth
        h_wealth_str = f"{h_wealth_val:.1f}{TAG_CFM}"

        plan_tag = TAG_CFM if is_selected else TAG_TMP
        
        def get_val(key, fmt=".1f"):
            if plan and key in plan and plan[key] is not None:
                return plan[key], f"{plan[key]:{fmt}}{plan_tag}"
            return None, "pending"

        proj_fund_v, proj_fund_s = get_val('proj_fund')
        bid_cost_v, bid_cost_s = get_val('bid_cost')
        r_pays_v, r_pays_s = get_val('r_pays')
        
        st.markdown("### 📊 Think Tank Real-time Variables")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"- GDP: `{gdp_str}`")
            st.write(f"- Est. Decay: `{decay_str}`")
            st.write(f"- H-System Eng. Ability: `{build_str}`" + (" *(Simulated)*" if is_simulating else "")) 
        with col2:
            st.write(f"- Plan Reward: `{proj_fund_s}`")
            st.write(f"- Total Benefit: `{bid_cost_s}`")
            st.write(f"- R-Pays: `{r_pays_s}`")

        st.markdown("---")
        st.markdown("### 🧮 Support Engine 2.0")
        st.markdown("**1. Macro Environment Support** - *Combines Absolute Growth and Expectation Gap*")
        st.latex(r"P_{plan} = (\Delta A \times 0.05) + (\Delta A - \Delta E) \times 0.15")
        st.markdown("**2. Project Execution Support** - *Tied to Scale and Completion*")
        st.latex(r"TargetGrowth = \frac{BidCost \times 0.2}{GDP} \times 100\%")
        st.latex(r"P_{exec} = TargetGrowth \times \left(\frac{C_{actual}}{C_{target}} - 0.5\right) \times 2.0 \times 0.1")
        st.markdown("**3. Support Shift Win Prob**")
        st.latex(r"WinProb = 1.0 - Rigidity(target\_index)")

        st.markdown("---")
        st.markdown("### 🧮 Core Economic Breakdown")

        st.markdown("**1. Expected Economic Loss**")
        st.latex(r"Loss = GDP \times (Decay \times 0.05 + 0)")
        loss_v = gdp_val * (decay_val * 0.05)
        st.write(f"> **Calc**: `{gdp_str}` × (`{decay_str}` × `0.05{TAG_CON}` + `0{TAG_CON}`) = **{loss_v:.2f}**")

        st.markdown("**2. Unit Construction Cost (w/ Inflation)**")
        st.latex(r"Cost = \frac{0.85}{Build / 10} \times 2^{(2 \times Decay - 1)} \times (1 + Inflation)")
        
        b_norm = max(0.01, build_val / 10.0)
        inflation = max(0.0, (gdp_val - 5000.0) / 10000.0)
        unit_cost_v = (0.85 / b_norm) * (2 ** (2 * decay_val - 1)) * (1 + inflation)
        st.write(f"> **Calc**: (0.85 / `{build_val/10:.2f}{TAG_CFM}`) × 2^(2 × `{decay_val:.3f}{TAG_EST}` - 1) × (1 + `{inflation:.2f} Inf{TAG_CON}`) = **{unit_cost_v:.2f}**")

        st.markdown("**3. Project Delivery & GDP Impact**")
        st.latex(r"Required = BidCost \times UnitCost")
        st.latex(r"Available = ProjFund + RPays + HWealth")
        
        can_calc = all(v is not None for v in [proj_fund_v, bid_cost_v, r_pays_v])
        
        if can_calc:
            req_v = bid_cost_v * unit_cost_v
            avail_v = proj_fund_v + r_pays_v + h_wealth_val
            st.write(f"> **Required Funds**: `{bid_cost_s}` × `{unit_cost_v:.2f}` = **{req_v:.2f}**")
            st.write(f"> **Available Funds**: `{proj_fund_s}` + `{r_pays_s}` + `{h_wealth_str}` = **{avail_v:.2f}**")
            
            if avail_v >= req_v:
                st.success(f"✅ Sufficient Funds (Available {avail_v:.1f} >= Required {req_v:.1f}). 100% Completion.")
                c_net = bid_cost_v
            else:
                st.error(f"❌ Funding Gap (Available {avail_v:.1f} < Required {req_v:.1f}). Project will under-deliver.")
                c_net = avail_v / unit_cost_v
            
            st.latex(r"GDP_{new} = GDP_{old} - Loss + (C_{net} \times 0.2)")
            new_gdp = gdp_val - loss_v + (c_net * 0.2)
            st.write(f"> **Result**: `{gdp_str}` - `{loss_v:.2f}` + (`{c_net:.2f}{TAG_EST}` × `0.2{TAG_CON}`) = **{new_gdp:.2f}**")
        else:
            st.info("💡 Some key metrics are still pending; unable to calculate preview.")

        st.markdown("---")
        st.markdown("### ⚖️ Linear Confiscation Model (Corruption/Cronyism)")
        
        rp = game.r_role_party
        hp = game.h_role_party
        
        rp_inv_pct = rp.investigate_ability / 10.0
        hp_stl_pct = hp.stealth_ability / 10.0
        catch_mult = max(0.1, (rp_inv_pct * cfg.get('R_INV_BONUS', 1.2)) - hp_stl_pct + 1.0)
        
        corr_base_rate = cfg.get('CATCH_RATE_PER_DOLLAR', 0.10)
        crony_base_rate = cfg.get('CRONY_CATCH_RATE_DOLLAR', 0.05)
        
        corr_catch_ratio = min(1.0, corr_base_rate * catch_mult)
        crony_catch_ratio = min(1.0, crony_base_rate * catch_mult)
        
        st.write(f"**🛡️ Catch Multiplier**: `max(0.1, (R-Intel {rp_inv_pct:.2f} × 1.2) - H-Stealth {hp_stl_pct:.2f} + 1.0) = {catch_mult:.2f}x`")
        
        st.markdown("**💸 Expected Corruption Profit**")
        st.latex(r"Caught_{corr} = Amount_{corr} \times \min(1.0, 10\% \times CatchMult)")
        st.latex(r"Net_{corr} = Amount_{corr} - Caught_{corr} - (Caught_{corr} \times 0.4_{fine})")
        st.write(f"> **Current Base Corr. Rate**: `{corr_base_rate*100:.1f}% × {catch_mult:.2f} = {corr_catch_ratio*100:.1f}%` (Pre-inflation correction)")
        
        st.markdown("**🏢 Expected Cronyism Profit**")
        st.latex(r"Caught_{crony} = Amount_{crony} \times \min(1.0, 5\% \times CatchMult)")
        st.latex(r"Net_{crony} = (Amount_{crony} - Caught_{crony}) \times 20\% - Caught_{crony} \times 0.7_{fine}")
        st.write(f"> **Current Base Crony Rate**: `{crony_base_rate*100:.1f}% × {catch_mult:.2f} = {crony_catch_ratio*100:.1f}%`")
        st.caption(f"*(⚖️ The 0.7x Crony Fine comes from: Forfeiting the `{cfg.get('CRONY_PROFIT_RATE', 0.20)*100:.0f}%` profit + paying a `50%` punitive fine on the caught contract value)*")
