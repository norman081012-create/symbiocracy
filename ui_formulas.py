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

        st.markdown("---")
        st.markdown(f"### ⚖️ Fake EV Audit Model ({t('Fake EV Investigation')})")
        
        st.markdown("**🔍 Chunk-based Dice Roll**")
        st.latex(r"Net\_Fin\_EV = R\_Investigate\_Fin - H\_Hide\_Fin")
        st.latex(r"ChunkSize = \frac{10}{Net\_Fin\_EV}")
        st.latex(r"CatchProb = BaseRate \times \max(1.0, Net\_Fin\_EV \times 0.1)")
        st.write(f"> **Cost of 1 Fake EV**: `{cfg.get('FAKE_EV_COST_RATIO', 0.2)}x Unit Cost`")
        
        st.markdown("**💸 Expected Penalties**")
        st.latex(r"CaughtValue = Caught\_Fake\_EV \times RealUnitCost")
        st.latex(r"Fine = CaughtValue \times FineMult")
