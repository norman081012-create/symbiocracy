# ==========================================
# phase2.py
# ==========================================
import streamlit as st

def render_dept_upgrade(label, key, dept, cw, cfg):
    st.markdown(f"**{label}** (當前效率: `{dept.eff:.1f}%` / 目標: `{dept.target:.1f}%`)")
    t_val = st.slider("🎯 設定新目標", 0.0, 100.0, float(dept.target), 1.0, key=f"t_{key}", label_visibility="collapsed")
    
    # 維護費依照「目標 (t_val)」收取，也就是如果拉低目標，即刻省錢
    maint = cfg['MAINTENANCE_BASE'] + max(0, (t_val - cfg['EFF_DEFAULT']) * 0.5)
    
    if t_val > dept.eff:
        total_cost = max(0, (t_val - dept.eff) * cfg['UPGRADE_COST_PER_PCT'])
        rem_cost = max(0, total_cost - dept.invested)
        if rem_cost > 0:
            inv_val = st.slider(f"💰 本年投入資金 (剩餘需 ${rem_cost:.0f})", 0.0, float(min(cw, rem_cost)), 0.0, 1.0, key=f"i_{key}")
            eta = rem_cost / inv_val if inv_val > 0 else float('inf')
            st.caption(f"📈 升級中 | 目標維護費: ${maint:.0f} | 預計 {eta:.1f} 年完成")
            return t_val, inv_val
        else:
            st.caption(f"✅ 升級資金已滿，年底結算達標 | 維護費: ${maint:.0f}")
            return t_val, 0.0
    elif t_val < dept.eff:
        st.caption(f"📉 降級縮編中 | 每年衰退 {cfg['DOWNGRADE_RATE_PER_YEAR']}% | 維護費即刻降至: ${maint:.0f}")
        return t_val, 0.0
    else:
        st.caption(f"✅ 穩定維持現狀 | 維護費: ${maint:.0f}")
        return t_val, 0.0

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    st.subheader(f"🛠️ Phase 2: 資源分配 - {view_party.name} ({'🛡️ 執行系統' if is_h else '⚖️ 監管系統'})")
    
    d = st.session_state.turn_data
    req_pay = d.get('h_pays', 0) if is_h else d.get('r_pays', 0)
    cw = int(view_party.wealth)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📣 政策與行動")
        st.info(f"📜法定專案款: `${req_pay}`")
        
        h_corr_pct = st.slider("💸 秘密貪污 (%)", 0, 100, 0) if is_h else 0
        h_crony_pct = st.slider("🏢 圖利自身廠商 (%)", 0, max(0, 100 - h_corr_pct), 0) if is_h else 0
        inv_corr_amt = st.slider("🔍 調查貪污 (投入資金)", 0, cw, 0) if not is_h else 0
        edu_up = st.slider("🎓 促進思辨 (投入資金)", 0, cw, 0)
        edu_down = st.slider("🎓 填鴨愚化 (投入資金)", 0, cw, 0)
        media_ctrl = st.slider("📺 媒體操控 (推卸/攻擊)", 0, cw, 0)
        camp_amt = st.slider("🎉 舉辦競選 (短期支持)", 0, cw, 0)
        incite_emo = st.slider("🔥 煽動情緒 (短期降理智)", 0, cw, 0)
        policy_tot = req_pay + media_ctrl + camp_amt + incite_emo + edu_up + edu_down + inv_corr_amt
        
    with c2:
        st.markdown("#### 🏢 部門效率與縮編計畫")
        rem_w = cw - policy_tot
        
        t_inv, i_inv = render_dept_upgrade("🔍 調查部門", "inv", view_party.depts['investigate'], rem_w, cfg); rem_w -= i_inv
        t_stl, i_stl = render_dept_upgrade("🥷 隱密部門", "stl", view_party.depts['stealth'], rem_w, cfg); rem_w -= i_stl
        t_pre, i_pre = render_dept_upgrade("🕵️ 預測部門", "pre", view_party.depts['predict'], rem_w, cfg); rem_w -= i_pre
        t_med, i_med = render_dept_upgrade("📺 媒體部門", "med", view_party.depts['media'], rem_w, cfg); rem_w -= i_med
        t_edu, i_edu = render_dept_upgrade("🎓 教育部門", "edu", view_party.depts['edu'], rem_w, cfg); rem_w -= i_edu
        
        if is_h:
            t_bld, i_bld = render_dept_upgrade("🏗️ 建設部門", "bld", view_party.depts['build'], rem_w, cfg); rem_w -= i_bld
        else:
            t_bld, i_bld = view_party.depts['build'].target, 0.0
            
        upg_tot = i_inv + i_stl + i_pre + i_med + i_edu + i_bld

    tot = policy_tot + upg_tot
    st.write(f"**本回合支出總計:** `{int(tot)}` / 預算餘額: `{cw - int(tot)}`")
    
    if tot <= cw and st.button("✅ 鎖定決策 (進入結算)", use_container_width=True, type="primary"):
        st.session_state[f"{view_party.name}_acts"] = {
            'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 
            'corr': h_corr_pct, 'crony': h_crony_pct, 'inv_corr': inv_corr_amt, 'legal': req_pay,
            'upgrades': {'inv': (t_inv, i_inv), 'stl': (t_stl, i_stl), 'pre': (t_pre, i_pre), 'med': (t_med, i_med), 'edu': (t_edu, i_edu), 'bld': (t_bld, i_bld)}
        }
        
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            game.phase = 3; game.proposing_party = game.ruling_party; st.rerun()
