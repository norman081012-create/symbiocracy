# ==========================================
# phase3.py
# ==========================================
import streamlit as st
import random
import formulas
import engine
import i18n
t = i18n.t

def render(game, cfg):
    st.header(t("Symbiocracy Times - Annual Report"))
    
    # ⚠️ 提早抓取政黨，避免後續 UnboundLocalError
    rp = game.r_role_party
    hp = game.h_role_party
    
    if not game.last_year_report:
        ra = st.session_state.get(f"{rp.name}_acts", {})
        ha = st.session_state.get(f"{hp.name}_acts", {})
        d = st.session_state.get('turn_data', {})
        
        fine_mult = float(d.get('fine_mult', 0.3)) 
        
        fake_ev = float(ha.get('fake_ev') or 0.0)
        allocations = ha.get('allocations', {})
        
        r_inv_fin = float(ra.get('alloc_inv_fin', 0))
        h_ci_fin = float(ha.get('alloc_ci_hidefin', 0))
        net_fin_ev = r_inv_fin - h_ci_fin
        
        if net_fin_ev > 0:
            chunk_size = max(0.01, 10.0 / net_fin_ev)
            catch_prob = min(1.0, cfg.get('FAKE_EV_CATCH_BASE_RATE', 0.05) * max(1.0, net_fin_ev * 0.1))
        else:
            chunk_size = float('inf')
            catch_prob = 0.0

        unit_cost_real = formulas.calc_unit_cost(cfg, game.gdp, hp.build_ability, game.current_real_decay)
        
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

        if not dice_data['is_rolled']:
            st.markdown("---")
            st.markdown(t("### 🎲 Initiate Financial Audit"))
            if dice_data['chunk_size'] == float('inf'):
                st.info(t("Regulator lacks operational capacity to audit. Cash flow hidden."))
                if st.button(t("⏩ Confirm Report & Next Year"), type="primary", use_container_width=True):
                    st.session_state.pending_dice_roll['fake_ev_results'] = (0.0, dice_data['fake_ev'], 0.0, 0.0)
                    st.session_state.pending_dice_roll['is_rolled'] = True
                    st.rerun()
            else:
                st.warning(f"**Target:** `{dice_data['fake_ev']:.1f}` Fake EV | **Catch Prob:** `{dice_data['catch_prob']*100:.1f}%` per `{dice_data['chunk_size']:.2f}` block.")

                if st.button(t("Execute Audit!"), type="primary", use_container_width=True):
                    with st.spinner('Investigators tracing funds...'):
                        import time
                        time.sleep(1.5) 
                        fake_ev_res = formulas.calc_fake_ev_dice(dice_data['fake_ev'], dice_data['catch_prob'], dice_data['fine_mult'], dice_data['chunk_size'], dice_data['unit_cost_real'])
                        st.session_state.pending_dice_roll['fake_ev_results'] = fake_ev_res
                        st.session_state.pending_dice_roll['is_rolled'] = True
                    st.rerun() 
            st.stop()

        caught_fake_ev, safe_fake_ev, caught_value, fine_value = dice_data['fake_ev_results']
        fake_ev_caught = (caught_fake_ev > 0)
        
        returned_to_r = caught_value
        confiscated_to_budget = fine_value
        hp_wealth_penalty = (caught_value + fine_value)
        
        for k in ['t_pre', 't_inv', 't_med', 't_bld', 'edu_stance']:
            if k in ra: setattr(rp, 'predict_ability' if k == 't_pre' else 'investigate_ability' if k == 't_inv' else 'media_ability' if k == 't_med' else 'build_ability' if k == 't_bld' else 'edu_stance', float(ra[k]))
            if k in ha: setattr(hp, 'predict_ability' if k == 't_pre' else 'investigate_ability' if k == 't_inv' else 'media_ability' if k == 't_med' else 'build_ability' if k == 't_bld' else 'edu_stance', float(ha[k]))

        req_cost = float(d.get('req_cost', 0.0))
        proj_fund = float(d.get('proj_fund') or 0.0)
        bid_cost = float(d.get('bid_cost') or 1.0)
        claimed_decay = float(d.get('claimed_decay') or 0.0)
        r_pays = float(d.get('r_pays') or 0.0)
        
        hp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == hp.name else 0))
        rp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == rp.name else 0))
        
        actual_h_wealth_available = max(0.0, hp.wealth + req_cost - float(ha.get('invest_wealth', 0)) - hp_wealth_penalty + hp_base)
        
        res_exec = formulas.calc_economy(
            cfg=cfg, gdp=float(game.gdp), budget_t=float(game.total_budget), 
            proj_fund=proj_fund, total_bid_cost=bid_cost, 
            build_abi=float(hp.build_ability), real_decay=float(game.current_real_decay), 
            override_unit_cost=None, r_pays=r_pays, h_wealth=actual_h_wealth_available, 
            allocations=allocations, 
            fake_ev_caught=caught_fake_ev, current_year=game.year, active_projects=game.active_projects
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
            rig = formulas.get_spin_rigidity(i, game.sanity, game.emotion, hp.edu_stance, getattr(game, 'h_rigidity_buff', {}).get('amount', 0.0), getattr(game, 'h_rigidity_buff', {}).get('party'), B, game.party_A.name)
            if random.random() > rig: censor_successes += 1
            else: censor_failures += 1
        
        censor_weight = max(0.0, censor_diff / 100.0) 
        censor_emotion_add = censor_weight * censor_successes
        censor_rigidity_buff = censor_weight * (censor_successes / (censor_successes + censor_failures)) if (censor_successes + censor_failures) > 0 else 0.0
            
        if censor_diff > 0: game.h_rigidity_buff = {'amount': censor_rigidity_buff, 'duration': 2, 'party': hp.name}
        
        # 接收新增的 p_opp
        p_ruling, p_opp, _, _, d_a, d_e = formulas.generate_raw_support(cfg, game.gdp, claimed_decay, res_exec['completed_projects'], float(game.current_real_decay), game.year)
        
        # ⚠️ 政績歷史庫結算與折舊 (6年線性)
        ruling_party = game.party_A if game.ruling_party.name == game.party_A.name else game.party_B
        opp_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A
        
        if p_ruling > 0:
            ruling_party.perf_history['ruling'].append({'year': game.year, 'amount': p_ruling})
        if p_opp > 0:
            opp_party.perf_history['ruling'].append({'year': game.year, 'amount': p_opp})

        inflation_corr = 5000.0 / max(1.0, game.gdp)
        for p_obj in res_exec['completed_projects']:
            depreciated_ev = 0.0
            for inv in p_obj.get('investments', []):
                age = game.year - inv['year']
                retention = max(0.1, 1.0 - float(game.current_real_decay)) ** age
                depreciated_ev += inv['amount'] * retention
                
            base_perf = (depreciated_ev * p_obj['exec_mult'] * inflation_corr) / 20.0
            hp.perf_history['exec'].append({'year': game.year, 'amount': base_perf})
            
            author = p_obj.get('author', 'System')
            for p in [game.party_A, game.party_B]:
                if p.name == author:
                    p.perf_history['prop'].append({'year': game.year, 'amount': base_perf})

        # 取出折舊後的總和
        r_p_a = formulas.get_depreciated_perf(game.party_A, 'ruling', game.year)
        r_p_b = formulas.get_depreciated_perf(game.party_B, 'ruling', game.year)
        e_p_a = formulas.get_depreciated_perf(game.party_A, 'exec', game.year)
        e_p_b = formulas.get_depreciated_perf(game.party_B, 'exec', game.year)
        pr_p_a = formulas.get_depreciated_perf(game.party_A, 'prop', game.year)
        pr_p_b = formulas.get_depreciated_perf(game.party_B, 'prop', game.year)
        
        # 相減淨值機制
        perf_A = r_p_a + e_p_a + pr_p_a
        perf_B = r_p_b + e_p_b + pr_p_b

        spin_A = 0.0; spin_B = 0.0
        h_spin_pwr = float(ha.get('alloc_med_control', 0.0)) + float(ha.get('alloc_med_camp', 0.0))
        r_spin_pwr = float(ra.get('alloc_med_control', 0.0)) + float(ra.get('alloc_med_camp', 0.0))
        
        if hp.name == game.party_A.name: 
            spin_A += h_spin_pwr; spin_B += r_spin_pwr
        else: 
            spin_B += h_spin_pwr; spin_A += r_spin_pwr

        net_perf_A = perf_A - perf_B
        net_spin_A = spin_A - spin_B
        old_boundary = game.boundary_B
        
        c_pen_a = censor_weight if rp.name == game.party_B.name else 0.0
        c_pen_b = censor_weight if rp.name == game.party_A.name else 0.0

        new_boundary, perf_used, perf_conquered, spin_used, spin_conquered = formulas.run_conquest_split(
            game.boundary_B, net_perf_A, net_spin_A, game.sanity, game.emotion, c_pen_a, c_pen_b,
            getattr(game, 'h_rigidity_buff', {}).get('amount', 0.0), getattr(game, 'h_rigidity_buff', {}).get('party'), game.party_A.name
        )
        
        game.active_projects = res_exec['ongoing_projects']
        
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
        
        ha_t_opt = float(ha.get('alloc_tt_opt', 0.0))
        ra_t_opt = float(ra.get('alloc_tt_opt', 0.0))
       
        game.last_year_report = {
            'old_gdp': game.gdp, 'old_san': game.sanity, 'old_emo': game.emotion, 'old_budg': game.total_budget, 'old_h_fund': game.h_fund,
            'new_san': new_sanity, 'new_emo': new_emotion,
            'h_party_name': hp.name, 'r_party_name': rp.name,
            'r_p_a': r_p_a, 'r_p_b': r_p_b, 'e_p_a': e_p_a, 'e_p_b': e_p_b, 'pr_p_a': pr_p_a, 'pr_p_b': pr_p_b,
            'perf_A': perf_A, 'perf_B': perf_B, 'net_perf_A': net_perf_A,
            'spin_A': spin_A, 'spin_B': spin_B, 'net_spin_A': net_spin_A,
            'perf_used': perf_used, 'perf_conquered': perf_conquered,
            'spin_used': spin_used, 'spin_conquered': spin_conquered,
            'old_boundary': old_boundary, 'new_boundary': new_boundary,
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
            'fake_ev_attempted': res_exec.get('total_fake_spent', 0.0),
            'chunk_size': chunk_size,
            'fine_mult': fine_mult,
            'proj_fund': proj_fund, 'h_idx': res_exec['h_idx'], 
            'total_bonus_deduction': total_bonus_deduction, 'base_r_surplus': base_r_surplus, 'unspent_proj': unspent_proj,
            'h_invest_wealth': float(ha.get('invest_wealth', 0)), 'r_invest_wealth': float(ra.get('invest_wealth', 0)),
            'completed_projects': res_exec['completed_projects'], 'failed_projects': res_exec['failed_projects'],
            'ha_t_opt': ha_t_opt, 'ra_t_opt': ra_t_opt,
            'cost_real_ev': res_exec.get('cost_real_ev', 0.0), 'cost_fake_ev': res_exec.get('cost_fake_ev', 0.0)
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
    
    rep = game.last_year_report
    
    st.markdown("---")
    st.markdown(t("### 🗞️ **[Front Page]**"))
    if rep.get('caught_fake_ev', 0) > 0:
        st.error(t(f"**[Corruption Scandal] Shoddy Projects Exposed!**\n\nInvestigators uncovered `{rep['caught_fake_ev']:.1f}` units of fake EV.\n- **{rep['h_party_name']}** was fined `${rep['caught_value']:.1f}` and penalized `${rep['fine_value']:.1f}`.\n- **{rep['r_party_name']}** received `${rep['caught_value']:.1f}` as whistleblower reward.\n- National treasury collected `${rep['fine_value']:.1f}`.\n- 📉 **Project completion rate dropped due to removed fake EV!**"))
    else:
        if rep.get('chunk_size', float('inf')) == float('inf'):
            st.success(t(f"**[Whitewashed] Nothing to See Here?**\n\nAudit failed. All books appear perfectly legal on paper."))
        elif rep.get('fake_ev_attempted', 0) > 0:
            st.success(t(f"**[Clean Getaway] Passed the Audit!**\n\nDespite strict investigation, special funds remain hidden."))
        else:
            st.success(t(f"**[Clean Gov] Zero Fake EV!**\n\nInvestigators confirm all projects are 100% genuine."))
            
    if rep.get('completed_projects'):
        st.info(f"🎉 **{t('Completed')} Projects:** " + ", ".join([p['name'] for p in rep['completed_projects']]))
    if rep.get('failed_projects'):
        st.warning(f"💀 **{t('Failed')} Projects:** " + ", ".join([p['name'] for p in rep['failed_projects']]))
            
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(t(f"### 📊 Economic Indicators"))
        st.write(f"- **GDP:** `{rep['old_gdp']:.1f}` ➔ **`{game.gdp:.1f}`**")
        st.write(f"- **{t('Civic Literacy')}:** `{rep['old_san']:.1f}` ➔ **`{game.sanity:.1f}`** ({game.sanity - rep['old_san']:+.1f})")
        st.write(f"- **{t('Voter Emotion')}:** `{rep['old_emo']:.1f}` ➔ **`{game.emotion:.1f}`** ({game.emotion - rep['old_emo']:+.1f})")
        
        st.markdown(t(f"### 🏛️ Financial Summary"))
        if rep.get('fine_value', 0) > 0:
            st.success(t(f"Treasury Income: +`${rep['fine_value']:.1f}`"))
        
        with st.expander(f"💼 {rep['h_party_name']} (Executive) Financials"):
            st.write(f"**Project Net Profit:** `${rep['h_project_net']:.1f}`")
            # 🛡️ 防呆：使用 .get() 確保向下相容舊存檔
            cost_real_ev = rep.get('cost_real_ev', 0.0)
            cost_fake_ev = rep.get('cost_fake_ev', 0.0)
            st.caption(f"*(Reward `${rep.get('payout_h', 0.0):.1f}` - Real Cost `${cost_real_ev:.1f}` - Fake Cost `${cost_fake_ev:.1f}`)*")
            st.write(f"+ Base Income: `${rep.get('h_base', 0.0):.1f}`")
            if rep.get('caught_fake_ev', 0) > 0:
                st.write(f"- Confiscated: `-${rep.get('caught_value', 0.0):.1f}`")
                st.write(f"- Penalty Fine: `-${rep.get('fine_value', 0.0):.1f}`")
            st.write(f"- Upgrade Costs: `-${rep.get('h_invest_wealth', 0.0):.1f}`")
            net_cash = rep.get('h_project_net', 0.0) + rep.get('h_base', 0.0) - rep.get('hp_penalty', 0.0) - rep.get('h_invest_wealth', 0.0)
            st.write(f"**Final Cash Flow:** `${net_cash:.1f}`")

        with st.expander(f"⚖️ {rep['r_party_name']} (Regulator) Financials"):
            st.write(f"**Base Income:** `${rep.get('r_base', 0.0):.1f}`")
            st.write(f"- Paid Executive: `-${rep.get('r_pays', 0.0):.1f}`")
            st.write(f"+ Unspent Recovery: `${rep.get('unspent_proj', 0.0):.1f}`")
            st.write(f"+ Budget Surplus: `${rep.get('base_r_surplus', 0.0):.1f}`")
            if rep.get('r_extra', 0) > 0: 
                st.write(f"+ Whistleblower Bonus: `${rep.get('r_extra', 0.0):.1f}`")
            st.write(f"- Upgrade Costs: `-${rep.get('r_invest_wealth', 0.0):.1f}`")
            net_cash_r = rep.get('r_base', 0.0) - rep.get('r_pays', 0.0) + rep.get('unspent_proj', 0.0) + rep.get('base_r_surplus', 0.0) + rep.get('r_extra', 0.0) - rep.get('r_invest_wealth', 0.0)
            st.write(f"**Final Cash Flow:** `${net_cash_r:.1f}`")

    with c2:
        st.markdown(t(f"### 🗳️ Electoral Shift"))
        
        net_ammo = rep.get('net_perf_A', 0) + rep.get('net_spin_A', 0)
        atk_party = game.party_A.name if net_ammo > 0 else game.party_B.name
        def_party = game.party_B.name if net_ammo > 0 else game.party_A.name
        
        if abs(net_ammo) < 1.0: 
            st.info(t("🤝 Stalemate. No significant shifts."))
        else:
            st.success(t(f"🔥 **Net Advantage:** `{abs(net_ammo):.1f}`！**{atk_party}** launched an offensive against **{def_party}**!"))

        is_god_mode = st.session_state.get('god_mode', False)
        with st.expander(t("👁️ God Mode: Electoral Mechanics"), expanded=is_god_mode):
            if is_god_mode:
                san_acc = formulas.get_sanity_accuracy(rep.get('old_san', 50), rep.get('old_emo', 30))
                st.write(f"*(Global Modifiers: Sanity `{rep.get('old_san', 50):.0f}`, Emotion `{rep.get('old_emo', 30):.0f}`)*")
                st.caption(f"*💡 Sanity Accuracy (Anti-Spin Armor): `{san_acc*100:.1f}%`*")
                
                r_p_a = rep.get('r_p_a', 0.0)
                r_p_b = rep.get('r_p_b', 0.0)
                e_p_a = rep.get('e_p_a', 0.0)
                e_p_b = rep.get('e_p_b', 0.0)
                pr_p_a = rep.get('pr_p_a', 0.0)
                pr_p_b = rep.get('pr_p_b', 0.0)
                
                st.markdown(f"**{t('Ruling Perf.')}**: {game.party_A.name} `{r_p_a:+.1f}` | {game.party_B.name} `{r_p_b:+.1f}` ➔ **Net: `{r_p_a - r_p_b:+.1f}`**")
                st.markdown(f"**{t('Exec Perf.')}**: {game.party_A.name} `{e_p_a:+.1f}` | {game.party_B.name} `{e_p_b:+.1f}` ➔ **Net: `{e_p_a - e_p_b:+.1f}`**")
                st.markdown(f"**{t('Prop Perf.')}**: {game.party_A.name} `{pr_p_a:+.1f}` | {game.party_B.name} `{pr_p_b:+.1f}` ➔ **Net: `{pr_p_a - pr_p_b:+.1f}`**")
                
                if abs(rep.get('net_perf_A', 0)) >= 1.0:
                    atk_p = game.party_A.name if rep['net_perf_A'] > 0 else game.party_B.name
                    perf_blocked = rep.get('perf_used', 0) - rep.get('perf_conquered', 0)
                    st.success(f"⚡ **Fact Penetration**: {atk_p} exerted `{rep.get('perf_used', 0):.1f}` impact. Ignorant/Emotional armor blocked `{perf_blocked:.1f}`, conquering **{rep.get('perf_conquered', 0)}** blocks!")
                    
                st.markdown(f"**Media & Spin Offense**: {game.party_A.name} `{rep.get('spin_A', 0):.1f}` | {game.party_B.name} `{rep.get('spin_B', 0):.1f}`")
                if abs(rep.get('net_spin_A', 0)) >= 1.0:
                    atk_s = game.party_A.name if rep['net_spin_A'] > 0 else game.party_B.name
                    blocked = rep.get('spin_used', 0) - rep.get('spin_conquered', 0)
                    st.warning(f"🛡️ **Brainwash Defense**: Rational sanity armor absorbed `{blocked:.1f}` spin impact. {atk_s} conquered **{rep.get('spin_conquered', 0)}** blocks.")

                old_sup_A = rep.get('old_boundary', 100) * 0.5
                new_sup_A = rep.get('new_boundary', 100) * 0.5
                old_sup_B = 100.0 - old_sup_A
                new_sup_B = 100.0 - new_sup_A
                
                st.markdown(f"#### 📊 **{game.party_A.name} True Support:** `{old_sup_A:.1f}%` ➔ **`{new_sup_A:.1f}%`** ({new_sup_A - old_sup_A:+.1f}%)")
                st.markdown(f"#### 📊 **{game.party_B.name} True Support:** `{old_sup_B:.1f}%` ➔ **`{new_sup_B:.1f}%`** ({new_sup_B - old_sup_B:+.1f}%)")
            else:
                st.warning(t("*(True support hidden. Conduct polls to reveal.)*"))

    st.markdown("---")
    if st.button(t("Next Year"), type="primary", use_container_width=True):
        if 'pending_dice_roll' in st.session_state: del st.session_state.pending_dice_roll
        
        is_election_end = (game.year % cfg['ELECTION_CYCLE'] == 0)
        game.year += 1
        
        if game.year > cfg['END_YEAR']: game.phase = 4
        else:
            game.phase = 1; game.p1_step = 'draft_r'
            game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
            
            # 🔴 修正：每年年初，角色自動校正回歸。當權派一定優先擔任 R (Regulator)
            game.r_role_party = game.ruling_party
            game.h_role_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A
            
            game.proposing_party = game.r_role_party
            
            # 從剛剛存好的 rep 裡面讀取雙方智庫優化的值來生成新專案
            hp_ep = rep.get('ha_t_opt', 0.0) if hp.name == game.party_A.name else rep.get('ra_t_opt', 0.0)
            rp_ep = rep.get('ha_t_opt', 0.0) if rp.name == game.party_A.name else rep.get('ra_t_opt', 0.0)
            
            hp.projects = engine.generate_projects(hp_ep, hp.name)
            rp.projects = engine.generate_projects(rp_ep, rp.name)
            
            game.last_year_report = None
            
            for k in list(st.session_state.keys()):
                if k.endswith('_acts') or k.startswith('up_'): del st.session_state[k]
            if 'turn_initialized' in st.session_state: del st.session_state.turn_initialized
        st.rerun()
