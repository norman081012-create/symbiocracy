# ==========================================
# phase3.py
# ==========================================
import streamlit as st
import random
import formulas
import i18n
t = i18n.t

def render(game, cfg):
    st.header(t("⚖️ Phase 3: Annual Resolution Report"))
    
    if not game.last_year_report:
        rp, hp = game.r_role_party, game.h_role_party
        ra = st.session_state.get(f"{rp.name}_acts", {})
        ha = st.session_state.get(f"{hp.name}_acts", {})
        d = st.session_state.get('turn_data', {})
        
        fine_mult = float(d.get('fine_mult', 0.3)) 
        
        if 't_pre' in ra: rp.predict_ability = float(ra['t_pre'])
        if 't_inv' in ra: rp.investigate_ability = float(ra['t_inv'])
        if 't_med' in ra: rp.media_ability = float(ra['t_med'])
        if 't_stl' in ra: rp.stealth_ability = float(ra['t_stl'])
        if 't_bld' in ra: rp.build_ability = float(ra['t_bld'])
        if 'edu_stance' in ra: rp.edu_stance = float(ra['edu_stance'])
        
        if 't_pre' in ha: hp.predict_ability = float(ha['t_pre'])
        if 't_inv' in ha: hp.investigate_ability = float(ha['t_inv'])
        if 't_med' in ha: hp.media_ability = float(ha['t_med'])
        if 't_stl' in ha: hp.stealth_ability = float(ha['t_stl'])
        if 't_bld' in ha: hp.build_ability = float(ha['t_bld'])
        if 'edu_stance' in ha: hp.edu_stance = float(ha['edu_stance'])
        
        returned_to_r = 0.0
        confiscated_to_budget = 0.0
        hp_wealth_penalty = 0.0
        
        proj_fund = float(d.get('proj_fund') or 0.0)
        bid_cost = float(d.get('bid_cost') or 1.0)
        claimed_decay = float(d.get('claimed_decay') or 0.0)
        r_pays = float(d.get('r_pays') or 0.0)
        
        h_tot_action = float(ha.get('tot_action') or 0)
        r_tot_action = float(ra.get('tot_action') or 0)
        h_tot_maint = float(ha.get('tot_maint') or 0)
        r_tot_maint = float(ra.get('tot_maint') or 0)
        h_refund = float(ha.get('refund_action') or 0)
        r_refund = float(ra.get('refund_action') or 0)
        
        corr_amt = float(ha.get('corr_amt') or 0.0)
        crony_base = float(ha.get('crony_amt') or 0.0)
        
        rp_inv_pct = rp.investigate_ability / 10.0
        hp_stl_pct = hp.stealth_ability / 10.0
        actual_catch_mult = max(0.1, (rp_inv_pct * cfg.get('R_INV_BONUS', 1.2)) - hp_stl_pct + 1.0)
        
        inflation = max(0.0, (game.gdp - cfg.get('CURRENT_GDP', 5000.0)) / cfg.get('GDP_INFLATION_DIVISOR', 10000.0))
        
        # 🚀 1. 貪污結算 (套用新骰子邏輯)
        catch_rate_per_dollar = cfg.get('CATCH_RATE_PER_DOLLAR', 0.10) * actual_catch_mult
        caught_corr, safe_corr, fine_corr = formulas.calc_corruption_dice(corr_amt, catch_rate_per_dollar, fine_mult)
        
        returned_to_r += caught_corr
        hp_wealth_penalty += fine_corr
        confiscated_to_budget += fine_corr
        corr_caught = (caught_corr > 0)

        # 🚀 2. 圖利結算 (套用新骰子邏輯)
        crony_profit_rate = cfg.get('CRONY_PROFIT_RATE', 0.20)
        crony_income = crony_base * crony_profit_rate
        crony_catch_rate_dollar = cfg.get('CRONY_CATCH_RATE_DOLLAR', 0.05) * actual_catch_mult
        
        caught_crony, safe_crony, fine_crony = formulas.calc_corruption_dice(crony_income, crony_catch_rate_dollar, fine_mult)
        
        returned_to_r += caught_crony
        hp_wealth_penalty += fine_crony
        confiscated_to_budget += fine_crony
        crony_caught = (caught_crony > 0)
            
        hp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == hp.name else 0))
        rp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == rp.name else 0))
        
        actual_h_wealth_available = max(0.0, hp.wealth - h_tot_action - h_tot_maint + h_refund - hp_wealth_penalty + hp_base)
        res_exec = formulas.calc_economy(cfg, float(game.gdp), float(game.total_budget), proj_fund, bid_cost, float(hp.build_ability), float(game.current_real_decay), corr_amt=corr_amt, r_pays=r_pays, h_wealth=actual_h_wealth_available)
        budg = cfg['BASE_TOTAL_BUDGET'] + (res_exec['est_gdp'] * cfg['HEALTH_MULTIPLIER'])
        
        hp_project_net = res_exec['h_project_profit']
        
        total_bonus_deduction = game.total_budget * ((cfg['BASE_INCOME_RATIO'] * 2) + cfg['RULING_BONUS_RATIO'])
        base_r_surplus = max(0.0, game.total_budget - total_bonus_deduction - proj_fund)
        unspent_proj = proj_fund * (1.0 - res_exec['h_idx'])
        
        rp_project_net = base_r_surplus + unspent_proj - r_pays
        
        # 🚀 執行方最終獲得的額外收入是「安全過關」的錢
        hp_inc = hp_base + hp_project_net + safe_corr + safe_crony
        rp_inc = rp_base + rp_project_net + returned_to_r
        
        s_val = max(0.0, (game.sanity - 50.0) / 50.0) 
        c_val = max(0.0, (50.0 - game.sanity) / 50.0) 
        censor_factor = 1.0 + s_val - c_val            
        
        media_multiplier = max(0.1, 1.0 - s_val + c_val + (game.emotion / 100.0))
        judicial_lvl = float(ra.get('judicial_lvl', 0.0))
        
        B = game.boundary_B
        opp_indices = range(B + 1, 201) if hp.name == game.party_A.name else range(1, B + 1)
        censor_successes = 0
        censor_failures = 0
        
        for i in opp_indices:
            rig = formulas.get_rigidity(i, game.sanity, getattr(game, 'h_rigidity_buff', {}).get('amount', 0.0), getattr(game, 'h_rigidity_buff', {}).get('party'), B, game.party_A.name)
            if random.random() > rig:
                censor_successes += 1
            else:
                censor_failures += 1
        
        censor_weight = judicial_lvl / 100.0 
        censor_emotion_add = censor_weight * censor_successes * censor_factor
        
        if (censor_successes + censor_failures) > 0:
            censor_rigidity_buff = censor_weight * (censor_successes / (censor_successes + censor_failures)) * censor_factor
        else:
            censor_rigidity_buff = 0.0
            
        if judicial_lvl > 0:
            game.h_rigidity_buff = {'amount': censor_rigidity_buff, 'duration': 2, 'party': hp.name}
            
        h_censor_penalty = max(0.1, 1.0 - censor_weight) 
        
        pr_mult = cfg.get('PR_EFFICIENCY_MULT', 3.0)
        h_media_pwr = float(ha.get('media', 0.0)) * pr_mult * (hp.media_ability / 10.0) * cfg.get('H_MEDIA_BONUS', 1.2) * media_multiplier * h_censor_penalty
        r_media_pwr = float(ra.get('media', 0.0)) * pr_mult * (rp.media_ability / 10.0) * media_multiplier
        
        raw_p_plan, raw_p_exec, d_a, d_e, d_c = formulas.generate_raw_support(cfg, res_exec['est_gdp'], game.gdp, claimed_decay, bid_cost, res_exec['c_net'])
        
        plan_correct, plan_wrong, correct_prob = formulas.apply_sanity_filter(raw_p_plan, game.sanity, game.emotion, is_preview=False)
        exec_correct, exec_wrong, _ = formulas.apply_sanity_filter(raw_p_exec, game.sanity, game.emotion, is_preview=False)
        
        ruling_name = game.ruling_party.name
        if ruling_name == hp.name:
            ruling_media_pwr = h_media_pwr; opp_media_pwr = r_media_pwr
        else:
            ruling_media_pwr = r_media_pwr; opp_media_pwr = h_media_pwr
            
        ruling_spun_plan, opp_spun_plan = formulas.apply_media_spin(plan_wrong, ruling_media_pwr, opp_media_pwr)
        h_spun_exec, r_spun_exec = formulas.apply_media_spin(exec_wrong, h_media_pwr, r_media_pwr)

        ammo_A = 0.0; ammo_B = 0.0

        if ruling_name == game.party_A.name:
            ammo_A += plan_correct + ruling_spun_plan; ammo_B += opp_spun_plan
        else:
            ammo_B += plan_correct + ruling_spun_plan; ammo_A += opp_spun_plan

        if hp.name == game.party_A.name:
            ammo_A += exec_correct + h_spun_exec; ammo_B += r_spun_exec
        else:
            ammo_B += exec_correct + h_spun_exec; ammo_A += r_spun_exec
            
        h_camp_pwr = float(ha.get('camp', 0.0)) * pr_mult * (hp.media_ability / 10.0) * media_multiplier * h_censor_penalty * 0.5
        r_camp_pwr = float(ra.get('camp', 0.0)) * pr_mult * (rp.media_ability / 10.0) * media_multiplier * 0.5

        if hp.name == game.party_A.name: ammo_A += h_camp_pwr; ammo_B += r_camp_pwr
        else: ammo_B += h_camp_pwr; ammo_A += r_camp_pwr

        net_ammo_A = ammo_A - ammo_B
        old_boundary = game.boundary_B
        
        buff_amt = getattr(game, 'h_rigidity_buff', {}).get('amount', 0.0)
        buff_party = getattr(game, 'h_rigidity_buff', {}).get('party')
        new_boundary, used_ammo, conquered = formulas.run_conquest(game.boundary_B, net_ammo_A, game.sanity, buff_amt, buff_party, game.party_A.name)
        
        game.boundary_B = new_boundary
        game.party_A.support = new_boundary * 0.5
        game.party_B.support = 100.0 - game.party_A.support
        
        gdp_grw_bonus = ((res_exec['est_gdp'] - game.gdp)/max(1.0, game.gdp)) * 100.0
        
        h_incite_rolls = float(ha.get('incite', 0.0)) * pr_mult * media_multiplier * h_censor_penalty
        r_incite_rolls = float(ra.get('incite', 0.0)) * pr_mult * media_multiplier
        total_incite_rolls = h_incite_rolls + r_incite_rolls
        
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
            'ammo_A': ammo_A, 'ammo_B': ammo_B, 'net_ammo_A': net_ammo_A,
            'old_boundary': old_boundary, 'new_boundary': new_boundary, 'used_ammo': used_ammo, 'conquered': conquered,
            'correct_prob': correct_prob,
            'h_spun_exec': h_spun_exec, 'r_spun_exec': r_spun_exec, 
            'censor_successes': censor_successes, 'censor_failures': censor_failures, 'censor_emotion_add': censor_emotion_add, 'censor_buff': censor_rigidity_buff,
            'h_inc': hp_inc, 'r_inc': rp_inc, 
            'h_base': hp_base, 'r_base': rp_base, 
            'h_project_net': hp_project_net, 'r_project_net': rp_project_net,
            'payout_h': res_exec['payout_h'], 'act_fund': res_exec['act_fund'], 'r_pays': r_pays,
            
            # 🚀 記錄圖利結算結果
            'h_extra': safe_corr + safe_crony, 'r_extra': returned_to_r,
            'caught_corr': caught_corr, 'caught_crony': caught_crony,
            'fine_corr': fine_corr, 'fine_crony': fine_crony,
            
            'h_pol_cost': h_tot_action, 'r_pol_cost': r_tot_action,
            'h_maint': h_tot_maint, 'r_maint': r_tot_maint,
            'h_refund': h_refund, 'r_refund': r_refund,
            'hp_penalty': hp_wealth_penalty,
            'corr_caught': corr_caught, 'crony_caught': crony_caught,
            'fine_mult': fine_mult,
            'proj_fund': proj_fund, 'h_idx': res_exec['h_idx'], 
            'total_bonus_deduction': total_bonus_deduction, 'base_r_surplus': base_r_surplus, 'unspent_proj': unspent_proj
        }
        
        game.gdp = res_exec['est_gdp']
        game.sanity = new_sanity
        game.emotion = new_emotion
        game.h_fund = res_exec['payout_h']
        game.total_budget = budg + confiscated_to_budget
        
        hp.wealth += hp_inc - h_tot_action - h_tot_maint + h_refund - hp_wealth_penalty
        rp.wealth += rp_inc - r_tot_action - r_tot_maint + r_refund

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
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 💰 {t('Economy & Finance')}")
        st.write(f"**GDP:** `{rep['old_gdp']:.1f}` ➔ `{game.gdp:.1f}`")
        
        with st.expander(f"📊 {rep['h_party_name']} ({t('role_exec')}) Project & Profit Breakdown"):
            st.write(f"- 📥 Received Project Reward: `${rep['payout_h']:.1f}`")
            st.write(f"- 📥 Received R-Subsidy: `${rep['r_pays']:.1f}`")
            st.write(f"- 📤 Actual Engineering Cost: `-${rep['act_fund']:.1f}`")
            st.write(f"**= Net Project Profit: `${rep['h_project_net']:.1f}`**")
            st.markdown("---")
            st.write(f"- Base Income (inc. Ruling Bonus): `${rep['h_base']:.1f}`")
            if rep['h_extra'] > 0:
                st.write(f"- {t('safe_amount')} (Evaded Detection): `${rep['h_extra']:.1f}`")
            if rep.get('hp_penalty', 0) > 0:
                st.write(f"- 🚨 {t('fine_paid')} ({rep['fine_mult']}x Multiplier): `-${rep['hp_penalty']:.1f}`")
            st.write(f"- PR, Operations & Shift Costs: `-${rep['h_pol_cost']:.1f}`")
            st.write(f"- Dept & Policy Maintenance: `-${rep['h_maint']:.1f}`")
            if rep['h_refund'] > 0: st.write(f"- Downgrade Refunds: `+${rep['h_refund']:.1f}`")
            net_cash = rep['h_inc'] - rep['h_pol_cost'] - rep['h_maint'] + rep['h_refund'] - rep.get('hp_penalty', 0)
            st.write(f"**💰 Final Net Cash Flow: `${net_cash:.1f}`**")

        with st.expander(f"📊 {rep['r_party_name']} ({t('role_reg')}) Surplus & Profit Breakdown"):
            st.write(f"- Base Income (inc. Ruling Bonus): `${rep['r_base']:.1f}`")
            st.write(f"- 📤 Paid R-Subsidy: `-${rep['r_pays']:.1f}`")
            st.write(f"- 📥 Unspent Project Funds Recovered: `${rep['unspent_proj']:.1f}`")
            st.write(f"- 📥 Regulatory Budget Surplus: `${rep['base_r_surplus']:.1f}`")
            if rep['r_extra'] > 0:
                st.write(f"- 🏆 {t('caught_amount')} (From Opponent): `${rep['r_extra']:.1f}`")
            st.write(f"- PR, Operations & Shift Costs: `-${rep['r_pol_cost']:.1f}`")
            st.write(f"- Dept & Policy Maintenance: `-${rep['r_maint']:.1f}`")
            if rep['r_refund'] > 0: st.write(f"- Downgrade Refunds: `+${rep['r_refund']:.1f}`")
            net_cash_r = rep['r_inc'] - rep['r_pol_cost'] - rep['r_maint'] + rep['r_refund']
            st.write(f"**💰 Final Net Cash Flow: `${net_cash_r:.1f}`**")

        if rep.get('corr_caught'): st.error(f"🚨 Corruption Scandal! Regulator seized `{rep['caught_corr']:.1f}`. Fines (`{rep['fine_corr']:.1f}`) applied to Treasury.")
        if rep.get('crony_caught'): st.error(f"🚨 Cronyism Controversy! Regulator seized `{rep['caught_crony']:.1f}`. Fines (`{rep['fine_crony']:.1f}`) applied to Treasury.")

    with c2:
        st.markdown(f"### 🧠 {t('Society & Opinion')}")
        s_move = game.sanity - rep['old_san']
        e_move = game.emotion - rep['old_emo']
        
        st.write(f"**{t('Civic Literacy')}:** `{rep['old_san']:.1f}` ➔ `{game.sanity:.1f}` ({s_move:+.1f})")
        st.write(f"**{t('Voter Emotion')}:** `{rep['old_emo']:.1f}` ➔ `{game.emotion:.1f}` ({e_move:+.1f})")
        
        st.markdown("---")
        st.markdown(f"### ⚔️ Support Shift Resolution")
        
        if st.session_state.get('god_mode'):
            st.caption(f"*(👁️ God Mode | Env. Plan Support: `{rep['raw_p_plan']/cfg['AMMO_MULTIPLIER']:+.2f}` | Proj Exec Support: `{rep['raw_p_exec']/cfg['AMMO_MULTIPLIER']:+.2f}`)*")
        
        st.caption(f"*(📡 This Year's Rational Attribution Rate: `{rep['correct_prob']*100:.1f}%`)*")
        
        if rep['h_spun_exec'] != 0 or rep['r_spun_exec'] != 0:
            st.info(f"📺 **Media Spin Output:** Executive media altered `{rep['h_spun_exec']:+.1f}` support points; Regulator media altered `{rep['r_spun_exec']:+.1f}` points!")
            
        if rep.get('censor_buff', 0) > 0:
            st.warning(f"⚖️ **Censorship Backlash:** Regulator's forced media suppression enraged `{rep['censor_successes']}` opponent units! Executive's voter rigidity drastically increased by `+{rep['censor_buff']:.3f}` for the next 2 years!")

        st.write(f"**{game.party_A.name} Total Support Force:** `{rep['ammo_A']:.1f}` | **{game.party_B.name} Total Support Force:** `{rep['ammo_B']:.1f}`")
        
        net_ammo = rep['net_ammo_A']
        atk_party = game.party_A.name if net_ammo > 0 else game.party_B.name
        def_party = game.party_B.name if net_ammo > 0 else game.party_A.name
        
        if abs(net_ammo) < 1.0:
            st.info("🤝 Support forces are deadlocked. No change in the political landscape.")
        else:
            st.success(f"**Net Support Advantage:** `{abs(net_ammo):.1f}` points! **{atk_party}** launched an influence wave against **{def_party}**!")
            
            if st.session_state.get('god_mode'):
                st.write(f"👁️ *(God Mode)* After armor rigidity checks, `{rep['used_ammo']:.1f}` support points were consumed to conquer **{rep['conquered']}** opponent blocs (0.5% each)!")
                old_sup = rep['old_boundary'] * 0.5; new_sup = rep['new_boundary'] * 0.5
                st.write(f"📊 👁️ **{game.party_A.name} New Support:** `{old_sup:.1f}%` ➔ `{new_sup:.1f}%`")

    st.markdown("---")
    if st.button(t("⏩ Confirm Report & Next Year"), type="primary", use_container_width=True):
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
