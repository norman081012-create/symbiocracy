# ==========================================
# phase3.py
# ==========================================
import streamlit as st
import random
import formulas
import i18n
t = i18n.t

def render(game, cfg):
    st.header("THE SYMBIOCRACY TIMES - Annual Report")
    
    if not game.last_year_report:
        rp, hp = game.r_role_party, game.h_role_party
        ra = st.session_state.get(f"{rp.name}_acts", {})
        ha = st.session_state.get(f"{hp.name}_acts", {})
        d = st.session_state.get('turn_data', {})
        
        fine_mult = float(d.get('fine_mult', 0.3)) 
        
        for k in ['t_pre', 't_inv', 't_med', 't_stl', 't_bld', 't_edu', 'edu_stance']:
            if k in ra: setattr(rp, 'predict_ability' if k == 't_pre' else 'investigate_ability' if k == 't_inv' else 'media_ability' if k == 't_med' else 'stealth_ability' if k == 't_stl' else 'build_ability' if k == 't_bld' else 'edu_ability' if k == 't_edu' else 'edu_stance', float(ra[k]))
            if k in ha: setattr(hp, 'predict_ability' if k == 't_pre' else 'investigate_ability' if k == 't_inv' else 'media_ability' if k == 't_med' else 'stealth_ability' if k == 't_stl' else 'build_ability' if k == 't_bld' else 'edu_ability' if k == 't_edu' else 'edu_stance', float(ha[k]))
        
        returned_to_r = 0.0
        confiscated_to_budget = 0.0
        hp_wealth_penalty = 0.0
        
        req_cost = float(d.get('req_cost', 0.0))
        proj_fund = float(d.get('proj_fund') or 0.0)
        bid_cost = float(d.get('bid_cost') or 1.0)
        claimed_decay = float(d.get('claimed_decay') or 0.0)
        r_pays = float(d.get('r_pays') or 0.0)
        
        fake_ev = float(ha.get('fake_ev') or 0.0)
        c_net_h = float(ha.get('c_net', 0))
        
        r_inv_fin = float(ra.get('alloc_inv_fin', 0))
        h_ci_fin = float(ha.get('alloc_ci_hidefin', 0))
        net_fin_ev = r_inv_fin - h_ci_fin
        
        if net_fin_ev > 0:
            chunk_size = max(0.01, 10.0 / net_fin_ev)
            catch_prob = min(1.0, cfg.get('FAKE_EV_CATCH_BASE_RATE', 0.10) * max(1.0, net_fin_ev * 0.1))
        else:
            chunk_size = float('inf')
            catch_prob = 0.0

        unit_cost_real = formulas.calc_unit_cost(cfg, game.gdp, hp.build_ability, game.current_real_decay)
        
        caught_fake_ev = safe_fake_ev = caught_value = fine_value = 0.0
        fake_ev_caught = False

        if 'pending_dice_roll' not in st.session_state:
             st.session_state.pending_dice_roll = {
                 'fake_ev': fake_ev,
                 'catch_prob': catch_prob,
                 'chunk_size': chunk_size,
                 'fine_mult': fine_mult,
                 'unit_cost_real': unit_cost_real,
                 'is_rolled': False
             }
        
        dice_data = st.session_state.pending_dice_roll

        if dice_data['is_rolled']:
            caught_fake_ev, safe_fake_ev, caught_value, fine_value = dice_data['fake_ev_results']
            
            returned_to_r += caught_value
            hp_wealth_penalty += (caught_value + fine_value)
            confiscated_to_budget += fine_value
            fake_ev_caught = (caught_fake_ev > 0)
            
        hp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == hp.name else 0))
        rp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == rp.name else 0))
        
        actual_h_wealth_available = max(0.0, hp.wealth + req_cost - float(ha.get('invest_wealth', 0)) - hp_wealth_penalty + hp_base)
        
        # --- 修正假 EV 的傳遞參數 ---
        eval_fake_ev_safe = safe_fake_ev if dice_data['is_rolled'] else fake_ev
        res_exec = formulas.calc_economy(
            cfg, float(game.gdp), float(game.total_budget), proj_fund, bid_cost, 
            float(hp.build_ability), float(game.current_real_decay), 
            r_pays=r_pays, h_wealth=actual_h_wealth_available, 
            c_net_override=c_net_h, fake_ev_spent=fake_ev, fake_ev_safe=eval_fake_ev_safe
        )
        
        budg = cfg['BASE_TOTAL_BUDGET'] + (res_exec['est_gdp'] * cfg['HEALTH_MULTIPLIER'])
        
        hp_project_net = res_exec['h_project_profit']
        total_bonus_deduction = game.total_budget * ((cfg['BASE_INCOME_RATIO'] * 2) + cfg['RULING_BONUS_RATIO'])
        base_r_surplus = max(0.0, game.total_budget - total_bonus_deduction - proj_fund)
        unspent_proj = proj_fund * (1.0 - res_exec['h_idx'])
        
        rp_project_net = base_r_surplus + unspent_proj - r_pays
        
        hp_inc = hp_base + hp_project_net + req_cost
        rp_inc = rp_base + rp_project_net + returned_to_r
        
        r_censor_alloc = float(ra.get('alloc_inv_censor', 0))
        h_anti_censor_alloc = float(ha.get('alloc_ci_anticen', 0))
        censor_diff = r_censor_alloc - h_anti_censor_alloc

        B = game.boundary_B
        opp_indices = range(B + 1, 201) if hp.name == game.party_A.name else range(1, B + 1)
        censor_successes = 0; censor_failures = 0
        
        for i in opp_indices:
            rig = formulas.get_spin_rigidity(i, game.sanity, getattr(game, 'h_rigidity_buff', {}).get('amount', 0.0), getattr(game, 'h_rigidity_buff', {}).get('party'), B, game.party_A.name)
            if random.random() > rig: censor_successes += 1
            else: censor_failures += 1
        
        censor_weight = max(0.0, censor_diff / 100.0) 
        censor_emotion_add = censor_weight * censor_successes
        censor_rigidity_buff = censor_weight * (censor_successes / (censor_successes + censor_failures)) if (censor_successes + censor_failures) > 0 else 0.0
            
        if censor_diff > 0: game.h_rigidity_buff = {'amount': censor_rigidity_buff, 'duration': 2, 'party': hp.name}
            
        h_media_pwr = float(ha.get('alloc_med_control', 0.0))
        r_media_pwr = float(ra.get('alloc_med_control', 0.0))
        
        raw_p_plan, raw_p_exec, d_a, d_e, d_c = formulas.generate_raw_support(cfg, res_exec['est_gdp'], game.gdp, claimed_decay, bid_cost, res_exec['c_net_total'])
        
        plan_correct, plan_wrong, correct_prob = formulas.apply_sanity_filter(raw_p_plan, game.sanity, game.emotion, is_preview=False)
        exec_correct, exec_wrong, _ = formulas.apply_sanity_filter(raw_p_exec, game.sanity, game.emotion, is_preview=False)
        
        ruling_name = game.ruling_party.name
        ruling_media_pwr = h_media_pwr if ruling_name == hp.name else r_media_pwr
        opp_media_pwr = r_media_pwr if ruling_name == hp.name else h_media_pwr
            
        ruling_spun_plan, opp_spun_plan = formulas.apply_media_spin(plan_wrong, ruling_media_pwr, opp_media_pwr)
        h_spun_exec, r_spun_exec = formulas.apply_media_spin(exec_wrong, h_media_pwr, r_media_pwr)

        perf_A = 0.0; perf_B = 0.0
        spin_A = 0.0; spin_B = 0.0

        if ruling_name == game.party_A.name: 
            perf_A += plan_correct; spin_A += ruling_spun_plan
            spin_B += opp_spun_plan
        else: 
            perf_B += plan_correct; spin_B += ruling_spun_plan
            spin_A += opp_spun_plan

        if hp.name == game.party_A.name: 
            perf_A += exec_correct; spin_A += h_spun_exec
            spin_B += r_spun_exec
        else: 
            perf_B += exec_correct; spin_B += h_spun_exec
            spin_A += r_spun_exec
            
        def get_camp_pwr(alloc, san, emo, edu_stance):
            rote_factor = max(0.0, -edu_stance / 100.0)
            return alloc * max(0.0, (1.0 - (san/100.0) + (emo/100.0) + rote_factor))

        h_camp_pwr = get_camp_pwr(float(ha.get('alloc_med_camp', 0.0)), game.sanity, game.emotion, hp.edu_stance)
        r_camp_pwr = get_camp_pwr(float(ra.get('alloc_med_camp', 0.0)), game.sanity, game.emotion, rp.edu_stance)

        if hp.name == game.party_A.name: spin_A += h_camp_pwr; spin_B += r_camp_pwr
        else: spin_B += h_camp_pwr; spin_A += r_camp_pwr

        net_perf_A = perf_A - perf_B
        net_spin_A = spin_A - spin_B
        old_boundary = game.boundary_B
        
        new_boundary, perf_used, perf_conquered, spin_used, spin_conquered = formulas.run_conquest_split(
            game.boundary_B, net_perf_A, net_spin_A, game.sanity, 
            getattr(game, 'h_rigidity_buff', {}).get('amount', 0.0), getattr(game, 'h_rigidity_buff', {}).get('party'), game.party_A.name
        )
        
        game.boundary_B = new_boundary
        game.party_A.support = new_boundary * 0.5
        game.party_B.support = 100.0 - game.party_A.support
        
        gdp_grw_bonus = ((res_exec['est_gdp'] - game.gdp)/max(1.0, game.gdp)) * 100.0
        
        total_incite_rolls = float(ha.get('alloc_med_incite', 0.0)) + float(ra.get('alloc_med_incite', 0.0))
        incite_points = formulas.calc_incite_success(total_incite_rolls, game.emotion)
        emotion_delta = (incite_points * 0.1) + censor_emotion_add - gdp_grw_bonus - (game.sanity * 0.15)
        new_emotion = max(0.0, min(100.0, game.emotion + emotion_delta))
        
        f_target_san = max(0.0, min(100.0, 50.0 + (ha.get('edu_stance', 0) + ra.get('edu_stance', 0)) * 0.5))
        f_san_move = (f_target_san - game.sanity) * 0.2
        new_sanity = max(0.0, min(100.0, game.sanity - (new_emotion * 0.02) + f_san_move))
        
        game.last_year_report = {
            'old_gdp': game.gdp, 'old_san': game.sanity, 'old_emo': game.emotion, 'old_budg': game.total_budget, 'old_h_fund': game.h_fund,
            'new_san': new_sanity, 'new_emo': new_emotion,
            'h_party_name': hp.name, 'r_party_name': rp.name,
            'raw_p_plan': raw_p_plan, 'raw_p_exec': raw_p_exec,
            'perf_A': perf_A, 'perf_B': perf_B, 'net_perf_A': net_perf_A,
            'spin_A': spin_A, 'spin_B': spin_B, 'net_spin_A': net_spin_A,
            'perf_used': perf_used, 'perf_conquered': perf_conquered,
            'spin_used': spin_used, 'spin_conquered': spin_conquered,
            'old_boundary': old_boundary, 'new_boundary': new_boundary,
            'correct_prob': correct_prob,
            'h_spun_exec': h_spun_exec, 'r_spun_exec': r_spun_exec, 
            'censor_successes': censor_successes, 'censor_failures': censor_failures, 'censor_emotion_add': censor_emotion_add, 'censor_buff': censor_rigidity_buff,
            'h_inc': hp_inc, 'r_inc': rp_inc, 
            'h_base': hp_base, 'r_base': rp_base, 
            'h_project_net': hp_project_net, 'r_project_net': rp_project_net,
            'payout_h': res_exec['payout_h'], 'act_fund': res_exec['act_fund'], 'r_pays': r_pays,
            'r_extra': returned_to_r,
            'caught_fake_ev': caught_fake_ev,
            'caught_value': caught_value,
            'fine_value': fine_value,
            'hp_penalty': hp_wealth_penalty,
            'fake_ev_caught': fake_ev_caught,
            'fake_ev_attempted': fake_ev,
            'chunk_size': chunk_size,
            'fine_mult': fine_mult,
            'proj_fund': proj_fund, 'h_idx': res_exec['h_idx'], 
            'total_bonus_deduction': total_bonus_deduction, 'base_r_surplus': base_r_surplus, 'unspent_proj': unspent_proj,
            'h_invest_wealth': float(ha.get('invest_wealth', 0)), 'r_invest_wealth': float(ra.get('invest_wealth', 0))
        }
        
        game.gdp = res_exec['est_gdp']
        game.sanity = new_sanity
        game.emotion = new_emotion
        game.h_fund = res_exec['payout_h']
        game.total_budget = budg + confiscated_to_budget
        
        hp.wealth += hp_inc - float(ha.get('invest_wealth', 0)) - hp_wealth_penalty
        rp.wealth += rp_inc - float(ra.get('invest_wealth', 0))

        if hasattr(game, 'h_rigidity_buff') and game.h_rigidity_buff['duration'] > 0:
            game.h_rigidity_buff['duration'] -= 1
            if game.h_rigidity_buff['duration'] <= 0:
                game.h_rigidity_buff = {'amount': 0.0, 'duration': 0, 'party': None}

        is_election_end = (game.year % cfg['ELECTION_CYCLE'] == 0)
        if is_election_end:
            winner = game.party_A if game.party_A.support > game.party_B.support else game.party_B
            game.ruling_party = winner

        hp.last_acts = ha.copy(); rp.last_acts = ra.copy()
        game.record_history(is_election=is_election_end)
    
    dice_data = st.session_state.get('pending_dice_roll')
    if dice_data and not dice_data['is_rolled']:
        st.markdown("---")
        st.markdown(f"### 🎲 INITIATE FINANCIAL AUDIT")
        if dice_data['chunk_size'] == float('inf'):
            st.info("The Regulator lacks sufficient ops capacity to initiate an audit. Financial flows obscured successfully.")
            if st.button("⏩ Proceed to Final Resolution", type="primary", use_container_width=True):
                st.session_state.pending_dice_roll['fake_ev_results'] = (0.0, dice_data['fake_ev'], 0.0, 0.0)
                st.session_state.pending_dice_roll['is_rolled'] = True
                st.rerun()
        else:
            st.warning(f"**Target:** `{dice_data['fake_ev']:.1f}` Fake EV | **Catch Probability:** `{dice_data['catch_prob']*100:.1f}%` per `{dice_data['chunk_size']:.2f}` units.")

            if st.button("🎲 EXECUTE AUDIT!", type="primary", use_container_width=True):
                with st.spinner('Investigators are tracking the financial flows...'):
                    import time
                    time.sleep(1.5) 
                    fake_ev_res = formulas.calc_fake_ev_dice(dice_data['fake_ev'], dice_data['catch_prob'], dice_data['fine_mult'], dice_data['chunk_size'], dice_data['unit_cost_real'])
                    st.session_state.pending_dice_roll['fake_ev_results'] = fake_ev_res
                    st.session_state.pending_dice_roll['is_rolled'] = True
                st.rerun() 
        st.stop()

    rep = game.last_year_report
    
    st.markdown("---")
    st.markdown("### 🗞️ **[FRONT PAGE HEADLINE]**")
    if rep.get('caught_fake_ev', 0) > 0:
        st.error(f"**[CORRUPTION SCANDAL] TOFU-DREG PROJECT EXPOSED!**\n\nInvestigators uncovered `{rep['caught_fake_ev']:.1f}` units of fabricated engineering (Fake EV).\n- **{rep['h_party_name']}** forfeits illicit gains of `${rep['caught_value']:.1f}` and is fined `${rep['fine_value']:.1f}`.\n- **{rep['r_party_name']}** receives a full whistleblower bounty of `${rep['caught_value']:.1f}`.\n- Treasury collects `${rep['fine_value']:.1f}` in punitive damages.")
    else:
        if rep.get('chunk_size', float('inf')) == float('inf'):
            st.success(f"**[WHITEWASH] NO IRREGULARITIES FOUND?**\n\nThe Regulator failed to investigate financial flows. All accounts passed 'legally'.")
        elif rep.get('fake_ev_attempted', 0) > 0:
            st.success(f"**[CLEAN GETAWAY] AUDIT PASSED!**\n\nDespite a rigorous investigation, the ruling party's 'special accounts' remained watertight.")
        else:
            st.success(f"**[CLEAN GOV] ZERO FAKE ENGINEERING DETECTED!**\n\nInvestigators turned the ledgers upside down and confirmed all projects are 100% genuine.")
            
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 📊 ECONOMIC METRICS")
        st.write(f"- **GDP:** `{rep['old_gdp']:.1f}` ➔ **`{game.gdp:.1f}`**")
        st.write(f"- **Civic Literacy:** `{rep['old_san']:.1f}` ➔ **`{game.sanity:.1f}`** ({game.sanity - rep['old_san']:+.1f})")
        st.write(f"- **Voter Emotion:** `{rep['old_emo']:.1f}` ➔ **`{game.emotion:.1f}`** ({game.emotion - rep['old_emo']:+.1f})")
        
        st.markdown(f"### 🏛️ FISCAL SUMMARY")
        if rep['fine_value'] > 0:
            st.success(f"Treasury Revenue: +`${rep['fine_value']:.1f}` (Punitive Fines)")
            
        with st.expander(f"💼 {rep['h_party_name']} (Executive) Financials"):
            st.write(f"**Net Project Profit:** `${rep['h_project_net']:.1f}`")
            st.write(f"+ Base Income: `${rep['h_base']:.1f}`")
            if rep['caught_fake_ev'] > 0:
                st.write(f"- Fraud Forfeiture: `-${rep['caught_value']:.1f}`")
                st.write(f"- Punitive Fines: `-${rep['fine_value']:.1f}`")
            st.write(f"- Eng. Costs: `-${rep['h_invest_wealth']:.1f}`")
            net_cash = rep['h_project_net'] + rep['h_base'] - rep.get('hp_penalty', 0) - rep['h_invest_wealth']
            st.write(f"**Final Cash Flow:** `${net_cash:.1f}`")

        with st.expander(f"⚖️ {rep['r_party_name']} (Regulator) Financials"):
            st.write(f"**Base Income:** `${rep['r_base']:.1f}`")
            st.write(f"- Paid R-Subsidy: `-${rep['r_pays']:.1f}`")
            st.write(f"+ Recovered Funds: `${rep['unspent_proj']:.1f}`")
            st.write(f"+ Budget Surplus: `${rep['base_r_surplus']:.1f}`")
            if rep['r_extra'] > 0: 
                st.write(f"+ Fraud Bounty: `${rep['r_extra']:.1f}`")
            st.write(f"- Eng. Costs: `-${rep['r_invest_wealth']:.1f}`")
            net_cash_r = rep['r_base'] - rep['r_pays'] + rep['unspent_proj'] + rep['base_r_surplus'] + rep['r_extra'] - rep['r_invest_wealth']
            st.write(f"**Final Cash Flow:** `${net_cash_r:.1f}`")

    with c2:
        st.markdown(f"### 🗳️ ELECTORAL SHIFT (Support Force)")
        
        net_ammo = rep['net_perf_A'] + rep['net_spin_A']
        atk_party = game.party_A.name if net_ammo > 0 else game.party_B.name
        def_party = game.party_B.name if net_ammo > 0 else game.party_A.name
        
        if abs(net_ammo) < 1.0: 
            st.info("🤝 Support forces are deadlocked. No significant momentum generated.")
        else:
            st.success(f"🔥 **Net Advantage:** `{abs(net_ammo):.1f}`! **{atk_party}** launched an influence wave against **{def_party}**!")

        if st.session_state.get('god_mode'):
            with st.expander("👁️ God Mode: Electoral Mechanics & True Support", expanded=True):
                st.write(f"*(Attribution Rate: `{rep['correct_prob']*100:.1f}%`)*")
                
                st.markdown(f"**Performance (True Damage)**: {game.party_A.name} `{rep['perf_A']:.1f}` | {game.party_B.name} `{rep['perf_B']:.1f}`")
                if abs(rep['net_perf_A']) >= 1.0:
                    atk_p = game.party_A.name if rep['net_perf_A'] > 0 else game.party_B.name
                    st.success(f"⚡ {atk_p} dealt `{rep['perf_used']:.1f}` unblockable impact, conquering **{rep['perf_conquered']}** blocs!")
                    
                st.markdown(f"**Media & Spin (Blockable)**: {game.party_A.name} `{rep['spin_A']:.1f}` | {game.party_B.name} `{rep['spin_B']:.1f}`")
                if abs(rep['net_spin_A']) >= 1.0:
                    atk_s = game.party_A.name if rep['net_spin_A'] > 0 else game.party_B.name
                    blocked = rep['spin_used'] - rep['spin_conquered']
                    st.warning(f"🛡️ Voter Sanity Armor absorbed `{blocked:.1f}` spin impact. {atk_s} conquered **{rep['spin_conquered']}** blocs.")

                old_sup_A = rep['old_boundary'] * 0.5
                new_sup_A = rep['new_boundary'] * 0.5
                old_sup_B = 100.0 - old_sup_A
                new_sup_B = 100.0 - new_sup_A
                
                st.markdown(f"#### 📊 **{game.party_A.name} True Support:** `{old_sup_A:.1f}%` ➔ **`{new_sup_A:.1f}%`** ({new_sup_A - old_sup_A:+.1f}%)")
                st.markdown(f"#### 📊 **{game.party_B.name} True Support:** `{old_sup_B:.1f}%` ➔ **`{new_sup_B:.1f}%`** ({new_sup_B - old_sup_B:+.1f}%)")
        else:
            st.caption("*(True support percentages are hidden. Conduct Polls to reveal current standing.)*")

    st.markdown("---")
    if st.button("⏩ Next Year", type="primary", use_container_width=True):
        if 'pending_dice_roll' in st.session_state: del st.session_state.pending_dice_roll
        
        is_election_end = (game.year % cfg['ELECTION_CYCLE'] == 0)
        game.year += 1
        
        if game.year > cfg['END_YEAR']: game.phase = 4
        else:
            game.phase = 1; game.p1_step = 'draft_r'
            game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
            
            if is_election_end:
                game.r_role_party = game.ruling_party
                game.h_role_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A
            
            game.proposing_party = game.r_role_party
            game.last_year_report = None
            
            for k in list(st.session_state.keys()):
                if k.endswith('_acts') or k.startswith('up_'): del st.session_state[k]
            if 'turn_initialized' in st.session_state: del st.session_state.turn_initialized
        st.rerun()
