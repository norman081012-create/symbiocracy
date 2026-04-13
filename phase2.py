# ==========================================
# phase2.py
# ==========================================
import streamlit as st
import formulas

def render_dept_upgrade(label, key, dept, cw, cfg):
    st.markdown(f"**{label}** (當前: `{dept.eff:.1f}%`)")
    t_val = st.slider("🎯 設定新目標", 0.0, 100.0, float(dept.target), 1.0, key=f"t_{key}", label_visibility="collapsed")
    
    curr_cost = formulas.get_dept_cost_cumulative(dept.eff, cfg)
    targ_cost = formulas.get_dept_cost_cumulative(t_val, cfg)
    maint = targ_cost * 0.1 # 10% 維護費
    
    if t_val > dept.eff:
        total_needed = max(0, targ_cost - curr_cost)
        rem_cost = max(0, total_needed - dept.invested)
        if rem_cost > 0:
            inv_val = st.slider(f"投入 (需 ${rem_cost:.0f})", 0.0, float(min(cw, rem_cost)), 0.0, 1.0, key=f"i_{key}")
            st.caption(f"📈 升級中 | 維護費: ${maint:.0f}")
            return t_val, inv_val
        else:
            st.caption(f"✅ 資金滿載 | 維護費: ${maint:.0f}")
            return t_val, 0.0
    else:
        st.caption(f"📉 降級/維持 | 維護費: ${maint:.0f}")
        return t_val, 0.0

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    st.subheader(f"🛠️ Phase 2: 資源分配 - {view_party.name}")
    
    cw = int(view_party.wealth)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📣 行動操作")
        camp_amt = st.slider("🎉 舉辦競選", 0, cw, 0)
        edu_up = st.slider("🎓 促進思辨", 0, cw, 0)
        policy_tot = camp_amt + edu_up
        
    with c2:
        st.markdown("#### 🏢 指數化部門升級")
        rem_w = cw - policy_tot
        
        t_inv, i_inv = render_dept_upgrade("🔍 調查", "inv", view_party.depts['investigate'], rem_w, cfg); rem_w -= i_inv
        t_pre, i_pre = render_dept_upgrade("🕵️ 預測", "pre", view_party.depts['predict'], rem_w, cfg); rem_w -= i_pre
        t_edu, i_edu = render_dept_upgrade("🎓 教育", "edu", view_party.depts['edu'], rem_w, cfg); rem_w -= i_edu
        
        if is_h:
            t_bld, i_bld = render_dept_upgrade("🏗️ 建設", "bld", view_party.depts['build'], rem_w, cfg); rem_w -= i_bld
            upg_tot = i_inv + i_pre + i_edu + i_bld
        else:
            t_bld, i_bld = view_party.depts['build'].target, 0.0
            upg_tot = i_inv + i_pre + i_edu

    tot = policy_tot + upg_tot
    can_afford = tot <= cw
    
    st.write(f"**支出總計:** `{int(tot)}` / 餘額: `{cw - int(tot)}`")
    if not can_afford: st.error("❌ 資金不足，請調降支出！")
    
    if st.button("✅ 鎖定決策 (進入結算)", use_container_width=True, type="primary", disabled=not can_afford):
        st.session_state[f"{view_party.name}_acts"] = {
            'camp': camp_amt, 'edu_up': edu_up, 
            'upgrades': {'inv': (t_inv, i_inv), 'pre': (t_pre, i_pre), 'edu': (t_edu, i_edu), 'bld': (t_bld, i_bld)}
        }
        
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            game.phase = 3; game.proposing_party = game.ruling_party; st.rerun()
