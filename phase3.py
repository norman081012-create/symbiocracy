# ==========================================
# phase3.py
# Responsible for Phase 3 (Annual Settlement Report and Visualization)
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
        
        # [Crucial] Pass is_preview=False, triggering the actual point-by-point rolling mechanism!
        shifts = formulas.calc_performance_amounts(
            cfg, hp, rp, game.ruling_party.name, 
            res_exec['est_gdp'], game.gdp, 
            claimed_decay, game.sanity, game.emotion, bid_cost, res_exec['c_net'],
            is_preview=False
        )
        
        h_media = hp.media_ability / 10.0
        r_media = rp.media_ability / 10.0
        shifts[hp.name]['camp'] = float(ha.get('camp', 0)) * h_media * 0.1
        shifts[rp.name]['camp'] = float(ra.get('camp', 0)) * r_media * 0.1
        shifts[hp.name]['backlash'] = 0.0
        shifts[rp.name]['backlash'] = 0.0
        
        a_sup_amt, b_sup_amt = game.update_support_queues({
            game.party_A.name: shifts[game.party_A.name],
            game.party_B.name: shifts[game.party_B.name]
        })
        
        gdp_grw_bonus = ((res_exec['est_gdp'] - game.gdp)/max(1.0, game.gdp)) * 100.0
        emotion_delta = (float(ha.get('incite') or 0) + float(ra.get('incite') or 0)) * 0.1 - gdp_grw_bonus - (game.sanity * 0.20)
        new_emotion = max(0.0, min(100.0, game.emotion + emotion_delta))
        
        f_target_san = max(0.0, min(100.0, 50.0 + (float(ra.get('edu_amt') or 0) / 500.0) * 50.0))
        f_san_move = (f_target_san - game.sanity) * 0.2
        new_sanity = max(0.0, min(100.0, game.sanity - (new_emotion * 0.02) + f_san_move))
        
        game.last_year_report = {
            'old_gdp': game.gdp, 'old_san': game.sanity, 'old_emo': game.emotion, 'old_budg': game.total_budget, 'old_h_fund': game.h_fund,
            'new_san': new_sanity, 'new_emo': new_emotion,
            'h_party_name': hp.name, 'r_party_name': rp.name,
            'shifts': shifts, 
            'h_inc': hp_inc, 'r_inc': rp_inc, 
            'h_base': hp_base, 'r_base': rp_base, 
            'h_project_net': hp_project_net, 'r_project_net': rp_project_net,
            'h_extra': corr_amt + crony_income, 'r_extra': returned_to_r,
            'h_pol_cost': h_tot_action, 'r_pol_cost': r_tot_action,
            'h_maint': h_tot_maint, 'r_maint': r_tot_maint,
            'corr_caught': corr_caught, 'crony_caught': crony_caught
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
        st.markdown(f"### 💰 {t('Economy & Finance Settlement')}")
        st.write(f"**GDP:** `{rep['old_gdp']:.1f}` ➔ `{game.gdp:.1f}`")
        
        with st.expander(f"📊 {rep['h_party_name']} ({t('H-System')}) {t('Profit Summary')}"):
            st.write(f"- {t('Base Funding (inc. Ruling Bonus)')}: `${rep['h_base']:.1f}`")
            st.write(f"- {t('Project Execution Profit')}: `${rep['h_project_net']:.1f}`")
            if rep['h_extra'] > 0:
                st.write(f"- {t('Secret Income (Corruption/Cronyism)')}: `${rep['h_extra']:.1f}`")
            st.write(f"- {t('Admin & Dept Cost')}: `-${rep['h_pol_cost'] + rep['h_maint']:.1f}`")
            st.write(f"**{t('Final Net Profit')}: `${rep['h_inc'] - (rep['h_pol_cost'] + rep['h_maint']):.1f}`**")

        with st.expander(f"📊 {rep['r_party_name']} ({t('R-System')}) {t('Profit Summary')}"):
            st.write(f"- {t('Base Funding (inc. Ruling Bonus)')}: `${rep['r_base']:.1f}`")
            st.write(f"- {t('Project Oversight Remainder')}: `${rep['r_project_net']:.1f}`")
            if rep['r_extra'] > 0:
                st.write(f"- {t('Seized Income/Bounty')}: `${rep['r_extra']:.1f}`")
            st.write(f"- {t('Admin & Dept Cost')}: `-${rep['r_pol_cost'] + rep['r_maint']:.1f}`")
            st.write(f"**{t('Final Net Profit')}: `${rep['r_inc'] - (rep['r_pol_cost'] + rep['r_maint']):.1f}`**")

        if rep.get('corr_caught'): st.error(t("🚨 H-System corruption detected! Illegal funds seized and returned to treasury."))
        if rep.get('crony_caught'): st.error(t("🚨 H-System cronyism detected! Associated funds completely frozen."))

    with c2:
        st.markdown(f"### 🧠 {t('Social Indicators & National Changes')}")
        s_move = game.sanity - rep['old_san']
        e_move = game.emotion - rep['old_emo']
        
        st.write(f"**{t('Civic Literacy (Critical)')}:** `{rep['old_san']:.1f}` ➔ `{game.sanity:.1f}` ({s_move:+.1f})")
        st.write(f"**{t('Voter Emotion (Volatility)')}:** `{rep['old_emo']:.1f}` ➔ `{game.emotion:.1f}` ({e_move:+.1f})")
        
        st.markdown("---")
        st.markdown(f"### 📈 {t('Support Attribution Analysis')}")
        
        # Display this year's voter literacy level
        correct_prob = rep['shifts'].get('correct_prob', 0.5)
        st.caption(f"*(📡 This year's voter correct attribution rate: `{correct_prob*100:.1f}%`)*")
        
        for p_name in [rep['h_party_name'], rep['r_party_name']]:
            is_h = (p_name == rep['h_party_name'])
            role_label = t("Execution") if is_h else t("Oversight")
            shift = rep['shifts'][p_name]
            is_ruling = (p_name == game.ruling_party.name)
            
            with st.expander(f"🔎 {p_name} ({role_label}) {t('Support Sources')}"):
                if is_h:
                    if shift.get('perf_proj', 0.0) != 0:
                        st.write(f"- 🏗️ **{t('Project Performance')}**: `{shift.get('perf_proj', 0.0):+.1f}` (Earned fairly by correct attribution)")
                    if shift.get('perf_gdp', 0.0) != 0:
                        reason = "Ruling Advantage" if is_ruling else "Voters mistakenly attributed credit to you"
                        st.write(f"- 🌐 **{t('Macro-Environment Performance')}**: `{shift.get('perf_gdp', 0.0):+.1f}` (From GDP Shift - {reason})")
                else:
                    if shift.get('perf_proj', 0.0) != 0:
                        st.write(f"- 🎁 **{t('Project Performance')}**: `{shift.get('perf_proj', 0.0):+.1f}` (Voter error, free-riding on H-System's hard work)")
                    if shift.get('perf_gdp', 0.0) != 0:
                        reason = "Ruling Advantage" if is_ruling else "Voters mistakenly attributed credit to you"
                        st.write(f"- 🌐 **{t('Macro-Environment Performance')}**: `{shift.get('perf_gdp', 0.0):+.1f}` (From GDP Shift - {reason})")
                        
                st.write(f"- 📢 **{t('Media & Campaigns')}**: `{shift['camp']:+.1f}`")

    st.markdown("---")
    if st.button(t("⏩ Confirm & Next Year"), type="primary", use_container_width=True):
        game.year += 1
        if game.year > cfg['END_YEAR']: game.phase = 4
        else:
            game.phase = 1; game.p1_step = 'draft_r'
            game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
            for k in list(st.session_state.keys()):
                if k.endswith('_acts'): del st.session_state[k]
            if 'turn_initialized' in st.session_state: del st.session_state.turn_initialized
        st.rerun()
