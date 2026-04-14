# ==========================================
# ui_formulas.py
# Responsible for formula calculation and monitoring (Think Tank Analysis)
# ==========================================
import streamlit as st
import formulas
import i18n

t = i18n.t

def render_formula_panel(game, view_party, cfg):
    with st.expander(t("🧮 Game Formulas & Calculation Monitor (Think Tank Analysis)"), expanded=False):
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
        
        build_val = game.h_role_party.build_ability
        build_str = f"{build_val:.1f}{TAG_CFM}"
        
        h_wealth_val = game.h_role_party.wealth
        h_wealth_str = f"{h_wealth_val:.1f}{TAG_CFM}"

        plan_tag = TAG_CFM if is_selected else TAG_TMP
        
        def get_val(key, fmt=".1f"):
            if plan and key in plan and plan[key] is not None:
                return plan[key], f"{plan[key]:{fmt}}{plan_tag}"
            return None, "pending (Empty)"

        proj_fund_v, proj_fund_s = get_val('proj_fund')
        bid_cost_v, bid_cost_s = get_val('bid_cost')
        r_pays_v, r_pays_s = get_val('r_pays')
        
        st.markdown("### 📊 Think Tank Real-time Variable Monitor")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"- GDP: `{gdp_str}`")
            st.write(f"- Est. Decay: `{decay_str}`")
            st.write(f"- Engineering Ability: `{build_str}`")
        with col2:
            st.write(f"- Project Reward: `{proj_fund_s}`")
            st.write(f"- Total Benefit: `{bid_cost_s}`")
            st.write(f"- R-Pays: `{r_pays_s}`")

        st.markdown("---")
        st.markdown("### 🧮 Core Economic Formula Breakdown")

        st.markdown("**1. Expected Economic Loss**")
        st.latex(r"Loss = GDP \times (Decay \times 0.05 + 0)")
        loss_v = gdp_val * (decay_val * 0.05)
        st.write(f"> **Calc**: `{gdp_str}` × (`{decay_str}` × `0.05{TAG_CON}` + `0{TAG_CON}`) = **{loss_v:.2f}**")

        st.markdown("**2. Unit Construction Cost**")
        st.latex(r"Cost = \frac{0.5}{Build / 10} \times 2^{(2 \times Decay - 1)} \times (1 + Inflation)")
        
        b_norm = max(0.01, build_val / 10.0)
        inflation = max(0.0, (gdp_val - 5000.0) / 10000.0)
        unit_cost_v = (0.5 / b_norm) * (2 ** (2 * decay_val - 1)) * (1 + inflation)
        st.write(f"> **Calc**: (0.5 / `{build_val/10:.2f}{TAG_CFM}`) × 2^(2 × `{decay_val:.3f}{TAG_EST}` - 1) × (1 + `{inflation:.2f} Inflation{TAG_CON}`) = **{unit_cost_v:.2f}**")

        st.markdown("**3. Project Execution & Final GDP Forecast**")
        st.latex(r"Required = BidCost \times UnitCost")
        st.latex(r"Available = ProjFund + RPays + HWealth")
        
        can_calc = all(v is not None for v in [proj_fund_v, bid_cost_v, r_pays_v])
        
        if can_calc:
            req_v = bid_cost_v * unit_cost_v
            avail_v = proj_fund_v + r_pays_v + h_wealth_val
            st.write(f"> **Req. Funds**: `{bid_cost_s}` × `{unit_cost_v:.2f}` = **{req_v:.2f}**")
            st.write(f"> **Avail. Funds**: `{proj_fund_s}` + `{r_pays_s}` + `{h_wealth_str}` = **{avail_v:.2f}**")
            
            if avail_v >= req_v:
                st.success(f"✅ Sufficient Funds (Available {avail_v:.1f} >= Required {req_v:.1f}), plan 100% completed.")
                c_net = bid_cost_v
            else:
                st.error(f"❌ Funding Gap (Available {avail_v:.1f} < Required {req_v:.1f}), plan will partially fail based on ratio.")
                c_net = avail_v / unit_cost_v
            
            st.latex(r"GDP_{new} = GDP_{old} - Loss + (C_{net} \times 0.2)")
            new_gdp = gdp_val - loss_v + (c_net * 0.2)
            st.write(f"> **Result**: `{gdp_str}` - `{loss_v:.2f}` + (`{c_net:.2f}{TAG_EST}` × `0.2{TAG_CON}`) = **{new_gdp:.2f}**")
        else:
            st.info("💡 Some key data (like rewards or benefits) are still pending, unable to complete forecast calculation.")
