# ==========================================
# phase3.py
# Handles Phase 3 (Annual Report & Visualization)
# ==========================================
import streamlit as st
import random
import formulas
import i18n
t = i18n.t

def render(game, cfg):
    st.header(t("⚖️ Phase 3: Annual Report"))
    
    if not game.last_year_report:
        rp, hp = game.r_role_party, game.h_role_party
        ra = st.session_state.get(f"{rp.name}_acts", {})
        ha = st.session_state.get(f"{hp.name}_acts", {})
        d = st.session_state.get('turn_data', {})
        
        returned_to_r = 0.0
        confiscated_to_budget = 0.0
        corr_caught = False
        crony_caught = False
        
        proj_fund = float(d.get('proj_fund') or 0.0)
        bid_cost = float(d.get('bid_cost') or 1.0)
        claimed_decay = float(d.get('claimed_decay') or 0.0)
        r_pays = float(d.get('r_pays') or 0.0)
        h_pays = float(d.get('h_pays') or 0.0)
        
        h_tot_action = float(ha.get('tot_action') or 0)
        r_tot_action = float(ra.get('tot_action') or 0)
        h_tot_maint = float(ha.get('tot_maint') or 0)
        r_tot_maint = float(ra.get('tot_maint') or 0)
        
        corr_pct_val = float(ha.get('corr') or 0)
        crony_pct_val = float(ha.get('crony') or 0)
        
        corr_amt = proj_fund * (corr_pct_val / 100.0)
        crony_base = proj_fund * (crony_pct_val / 100.0)
        crony_income = crony_base * 0.1  
        
        rp_inv_pct = rp.investigate_ability / 10.0
        hp_stl_pct = hp.stealth_ability / 10.0
        actual_catch_mult = max(0.1, (rp_inv_pct * cfg['R_INV_BONUS']) - hp_stl_pct + 1.0)
        
        rolls_corr = corr_pct_val * actual_catch_mult
        catch_prob_corr = 1.0 - (1.0 - cfg['CATCH_RATE_PER_PERCENT'])**rolls_corr
        
        rolls_crony = crony_pct_val * actual_catch_mult
        catch_prob_crony = 1.0 - (1.0 - cfg['CRONY_CATCH_RATE_PER_PERCENT'])**rolls_crony
        
        if corr_amt > 0 and random.random() < catch_prob_corr:
            returned_to_r += corr_amt
            confiscated_to_budget += corr_amt * 0.4
            corr_caught = True
            corr_amt = 0

        if crony_base > 0 and random.random() < catch_prob_crony:
            returned_to_r += crony_base
            confiscated_to_budget += crony_base * 0.5
            crony_caught = True
            crony_base = 0
            crony_income = 0
            
        actual_h_wealth_available = hp.wealth - h_tot_action - h_tot_maint
        res_exec = formulas.calc_economy(cfg, float(game.gdp), float(game.total_budget), proj_fund, bid_cost, float(hp.build_ability), float(game.current_real_decay), corr_amt=corr_amt, r_pays=r_pays, h_wealth=max(0.0, actual_h_wealth_available))
        budg = cfg['BASE_TOTAL_BUDGET'] + (res_exec['est_gdp'] * cfg['HEALTH_MULTIPLIER'])
        
        hp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == hp.name else 0))
        rp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == rp.name else 0))
        
        hp_project_net = res_exec['h_project_profit']
        rp_project_net = res_exec['payout_r'] - r_pays
        
        hp_inc = hp_base + hp_project_net + corr_amt + crony_income
        rp_inc = rp_base + rp_project_net + returned_to_r
        
        # 🚀 Fix: Correctly call generate_raw_support
        raw_p_plan, raw_p_exec, d_a, d_e, d_c = formulas.generate_raw_support(cfg, res_exec['est_gdp'], game.gdp, claimed_decay, bid_cost, res_exec['c_net'])
        
        plan_correct, plan_wrong, correct_prob = formulas.apply_sanity_filter(raw_p_plan, game.sanity, game.emotion, is_preview=False)
        exec_correct, exec_wrong, _ = formulas.apply_sanity_filter(raw_p_exec, game.sanity, game.emotion, is_preview=False)
        
        ammo_A = 0.0
        ammo_B = 0.0
        ruling_name = game.ruling_party.name

        if ruling_name == game.party_A.name:
            ammo_A += plan_correct; ammo_B += plan_wrong
        else:
            ammo_B += plan_correct; ammo_A += plan_wrong

        if hp.name == game.party_A.name:
            ammo_A += exec_correct; ammo_B += exec_wrong
        else:
            ammo_B += exec_correct; ammo_A += exec_wrong
            
        h_media = hp.media_ability / 10.0
        r_media = rp.media_ability / 10.0
        camp_A = (float(ha.get('camp', 0)) if hp.name == game.party_A.name else float(ra.get('camp', 0))) * (h_media if hp.name == game.party_A.name else r_media) * 0.5
        camp_B = (float(ha.get('camp', 0)) if hp.name == game.party_B.name else float(ra.get('camp', 0))) * (h_media if hp.name == game.party_B.name else r_media) * 0.5

        ammo_A += camp_A
        ammo_B += camp_B

        net_ammo_A = ammo_A - ammo_B
        old_boundary = game.boundary_B
        new_boundary, used_ammo, conquered = formulas.run_conquest(game.boundary_B, net_ammo_A)
        
        game.boundary_B = new_boundary
        game.party_A.support = new_boundary * 0.5
        game.party_B.support = 100.0 - game.party_A.support
        
        gdp_grw_bonus = ((res_exec['est_gdp'] - game.gdp)/max(1.0, game.gdp)) * 100.0
        emotion_delta = (float(ha.get('incite') or 0) + float(ra.get('incite') or 0)) * 0.1 - gdp_grw_bonus - (game.sanity * 0.20)
        new_emotion = max(0.0, min(100.0, game.emotion + emotion_delta))
        
        f_target_san = max(0.0, min(100.0, 50.0 + (float(ra.get('edu_amt') or 0) / 500.0) * 50.0))
        f_san_move = (f_target_san - game.sanity) * 0.2
        new_sanity = max(0.0, min(100.0, game.sanity - (new_emotion * 0.02) + f_san_move))
        
        total_bonus_deduction = game.total_budget * ((cfg['BASE_INCOME_RATIO'] * 2) + cfg['RULING_BONUS_RATIO'])
        
        game.last_year_report = {
            'old_gdp': game.gdp, 'old_san': game.sanity, 'old_emo': game.emotion, 'old_budg': game.total_budget, 'old_h_fund': game.h_fund,
            'new_san': new_sanity, 'new_emo': new_emotion,
            'h_party_name': hp.name, 'r_party_name': rp.name,
            'raw_p_plan': raw_p_plan, 'raw_p_exec': raw_p_exec,
            'ammo_A': ammo_A, 'ammo_B': ammo_B, 'net_ammo_A': net_ammo_A,
            'old_boundary': old_boundary, 'new_boundary': new_boundary, 'used_ammo': used_ammo, 'conquered': conquered,
            'correct_prob': correct_prob,
            'h_inc': hp_inc, 'r_inc': rp_inc, 
            'h_base': hp_base, 'r_base': rp_base, 
            'h_project_net': hp_project_net, 'r_project_net': rp_project_net,
            'h_extra': corr_amt + crony_income, 'r_extra': returned_to_r,
            'h_pol_cost': h_tot_action, 'r_pol_cost': r_tot_action,
            'h_maint': h_tot_maint, 'r_maint': r_tot_maint,
            'corr_caught': corr_caught, 'crony_caught': crony_caught,
            'proj_fund': proj_fund, 'h_idx': res_exec['h_idx'], 'r_pays': r_pays, 'total_bonus_deduction': total_bonus_deduction
        }
        
        game.gdp = res_exec['est_gdp']
        game.sanity = new_sanity
        game.emotion = new_emotion
        game.h_fund = res_exec['payout_h']
        game.total_budget = budg + confiscated_to_budget
        
        hp.wealth += hp_inc - h_tot_action - h_tot_maint
        rp.wealth += rp_inc - r_tot_action - r_tot_maint

        if game.year % cfg['ELECTION_CYCLE'] == 1:
            winner = hp if hp.support > rp.support else rp
            game.ruling_party = winner

        hp.last_acts = ha.copy(); rp.last_acts = ra.copy()
        game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
    
    rep = game.last_year_report
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 💰 {t('Economy & Finance', 'Economy & Finance')}")
        st.write(f"**GDP:** `{rep['old_gdp']:.1f}` ➔ `{game.gdp:.1f}`")
        
        with st.expander(f"📊 {rep['h_party_name']} ({t('H-System')}) {t('Profit Summary')}"):
            st.write(f"- {t('Base Funding (Inc. Ruling Bonus)', 'Base Funding (Inc. Ruling Bonus)')}: `${rep['h_base']:.1f}`")
            st.write(f"- {t('Project Execution Profit', 'Project Execution Profit')}: `${rep['h_project_net']:.1f}`")
            if rep['h_extra'] > 0:
                st.write(f"- {t('Secret Income (Corruption/Cronyism)', 'Secret Income (Corruption/Cronyism)')}: `${rep['h_extra']:.1f}`")
            st.write(f"- {t('Admin & Dept Expenses', 'Admin & Dept Expenses')}: `-${rep['h_pol_cost'] + rep['h_maint']:.1f}`")
            st.write(f"**{t('Final Net Profit', 'Final Net Profit')}: `${rep['h_inc'] - (rep['h_pol_cost'] + rep['h_maint']):.1f}`**")

        with st.expander(f"📊 {rep['r_party_name']} ({t('R-System')}) {t('Profit Summary')}"):
            st.write(f"- {t('Base Funding (Inc. Ruling Bonus)', 'Base Funding (Inc. Ruling Bonus)')}: `${rep['r_base']:.1f}`")
            
            unspent_proj = rep['proj_fund'] * (1.0 - rep['h_idx'])
            st.write(f"- {t('Unspent Project Funds Returned', 'Unspent Project Funds Returned')}: `${unspent_proj:.1f}`")
            
            base_r_surplus = rep['old_budg'] - rep['total_bonus_deduction'] - rep['proj_fund']
            st.write(f"- {t('R-System Budget Surplus', 'R-System Budget Surplus')}: `${max(0.0, base_r_surplus) - rep['r_pays']:.1f}`")
            
            if rep['r_extra'] > 0:
                st.write(f"- {t('Confiscated Income/Catch Bonus', 'Confiscated Income/Catch Bonus')}: `${rep['r_extra']:.1f}`")
            st.write(f"- {t('Admin & Dept Expenses', 'Admin & Dept Expenses')}: `-${rep['r_pol_cost'] + rep['r_maint']:.1f}`")
            st.write(f"**{t('Final Net Profit', 'Final Net Profit')}: `${rep['r_inc'] - (rep['r_pol_cost'] + rep['r_maint']):.1f}`**")

        if rep.get('corr_caught'): st.error(t("🚨 Corruption Caught! Funds seized.", "🚨 Corruption Caught! Funds seized."))
        if rep.get('crony_caught'): st.error(t("🚨 Cronyism Caught! Funds seized.", "🚨 Cronyism Caught! Funds seized."))

    with c2:
        st.markdown(f"### 🧠 {t('Society & Opinion (New Shifts)', 'Society & Opinion (New Shifts)')}")
        s_move = game.sanity - rep['old_san']
        e_move = game.emotion - rep['old_emo']
        
        st.write(f"**{t('Civic Literacy', 'Civic Literacy')}:** `{rep['old_san']:.1f}` ➔ `{game.sanity:.1f}` ({s_move:+.1f})")
        st.write(f"**{t('Voter Emotion', 'Voter Emotion')}:** `{rep['old_emo']:.1f}` ➔ `{game.emotion:.1f}` ({e_move:+.1f})")
        
        st.markdown("---")
        st.markdown(f"### ⚔️ Support Impact Settlement")
        
        # 🚀 Fix: Replaced ammo text with support points, hiding explicit armor checks under God Mode
        if st.session_state.get('god_mode'):
            st.caption(f"*(👁️ God Mode | Macro Plan Perf: `{rep['raw_p_plan']/cfg['AMMO_MULTIPLIER']:+.2f}` | Execution Perf: `{rep['raw_p_exec']/cfg['AMMO_MULTIPLIER']:+.2f}`)*")
        
        st.caption(f"*(📡 This Year Voter Correct Attribution Rate: `{rep['correct_prob']*100:.1f}%`)*")
        
        st.write(f"**{game.party_A.name} Total Support Points:** `{rep['ammo_A']:.1f}` | **{game.party_B.name} Total Support Points:** `{rep['ammo_B']:.1f}`")
        
        net_ammo = rep['net_ammo_A']
        atk_party = game.party_A.name if net_ammo > 0 else game.party_B.name
        def_party = game.party_B.name if net_ammo > 0 else game.party_A.name
        
        if abs(net_ammo) < 1.0:
            st.info("🤝 Support points are locked in a stalemate, no change in public opinion territory.")
        else:
            st.success(f"**Net Support Points Advantage:** `{abs(net_ammo):.1f}` pts! **{atk_party}** influenced the voters of **{def_party}**! But what voters actually think, only God knows...")
            
            if st.session_state.get('god_mode'):
                st.write(f"👁️ *(God Mode)* Penetrated through rigid armor checks, consumed `{rep['used_ammo']:.1f}` support points, successfully conquered **{rep['conquered']}** opponent sectors (0.5% each)!")
                
                old_sup = rep['old_boundary'] * 0.5
                new_sup = rep['new_boundary'] * 0.5
                st.write(f"📊 👁️ **{game.party_A.name} New Support:** `{old_sup:.1f}%` ➔ `{new_sup:.1f}%`")

    st.markdown("---")
    if st.button(t("⏩ Confirm & Next Year", "⏩ Confirm & Next Year"), type="primary", use_container_width=True):
        game.year += 1
        if game.year > cfg['END_YEAR']: game.phase = 4
        else:
            game.phase = 1; game.p1_step = 'draft_r'
            game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
            for k in list(st.session_state.keys()):
                if k.endswith('_acts'): del st.session_state[k]
            if 'turn_initialized' in st.session_state: del st.session_state.turn_initialized
        st.rerun()
