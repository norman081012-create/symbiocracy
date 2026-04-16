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
        
        crony_base = float(ha.get('crony_amt') or 0.0)
        c_net_h = float(ha.get('c_net', 0))
        
        r_inv_fin = float(ra.get('alloc_inv_fin', 0))
        h_ci_fin = float(ha.get('alloc_ci_hidefin', 0))
        net_fin_ev = r_inv_fin - h_ci_fin
        
        if net_fin_ev > 0:
            chunk_size = max(0.01, 10.0 / net_fin_ev)
            catch_prob = min(1.0, cfg.get('CRONY_CATCH_RATE_DOLLAR', 0.05) * max(1.0, net_fin_ev * 0.1))
        else:
            chunk_size = float('inf')
            catch_prob = 0.0
            
        crony_profit_rate = cfg.get('CRONY_PROFIT_RATE', 0.20)
        crony_income = crony_base * crony_profit_rate

        caught_crony = safe_crony = fine_crony = 0.0
        crony_caught = False

        if 'pending_dice_roll' not in st.session_state:
             st.session_state.pending_dice_roll = {
                 'crony_income': crony_income,
                 'crony_catch_rate': catch_prob,
                 'chunk_size': chunk_size,
                 'fine_mult': fine_mult,
                 'is_rolled': False
             }
        
        dice_data = st.session_state.pending_dice_roll

        if dice_data['is_rolled']:
            caught_crony, safe_crony, fine_crony = dice_data['crony_results']
            
            returned_to_r += caught_crony
            hp_wealth_penalty += fine_crony
            confiscated_to_budget += fine_crony
            crony_caught = (caught_crony > 0)
            
        hp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == hp.name else 0))
        rp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == rp.name else 0))
        
        actual_h_wealth_available = max(0.0, hp.wealth + req_cost - float(ha.get('invest_wealth', 0)) - hp_wealth_penalty + hp_base)
        
        res_exec = formulas.calc_economy(cfg, float(game.gdp), float(game.total_budget), proj_fund, bid_cost, float(hp.build_ability), float(game.current_real_decay), r_pays=r_pays, h_wealth=actual_h_wealth_available, c_net_override=c_net_h)
        budg = cfg['BASE_TOTAL_BUDGET'] + (res_exec['est_gdp'] * cfg['HEALTH_MULTIPLIER'])
        
        hp_project_net = res_exec['h_project_profit']
        total_bonus_deduction = game.total_budget * ((cfg['BASE_INCOME_RATIO'] * 2) + cfg['RULING_BONUS_RATIO'])
        base_r_surplus = max(0.0, game.total_budget - total_bonus_deduction - proj_fund)
        unspent_proj = proj_fund * (1.0 - res_exec['h_idx'])
        
        rp_project_net = base_r_surplus + unspent_proj - r_pays
        
        hp_inc = hp_base + hp_project_net + safe_crony + req_cost
        rp_inc = rp_base + rp_project_net + returned_to_r
        
        r_censor_alloc = float(ra.get('alloc_inv_censor', 0))
        h_anti_censor_alloc = float(ha.get('alloc_ci_anticen', 0))
        censor_diff = r_censor_alloc - h_anti_censor_alloc

        B = game.boundary_B
        opp_indices = range(B + 1, 201) if hp.name == game.party_A.name else range(1, B + 1)
        censor_successes = 0; censor_failures = 0
        
        for i in opp_indices:
            rig = formulas.get_rigidity(i, game.sanity, getattr(game, 'h_rigidity_buff', {}).get('amount', 0.0), getattr(game, 'h_rigidity_buff', {}).get('party'), B, game.party_A.name)
            if random.random() > rig: censor_successes += 1
            else: censor_failures += 1
        
        censor_weight = max(0.0, censor_diff / 100.0) 
        censor_emotion_add = censor_weight * censor_successes
        censor_rigidity_buff = censor_weight * (censor_successes / (censor_successes + censor_failures)) if (censor_successes + censor_failures) > 0 else 0.0
            
        if censor_diff > 0: game.h_rigidity_buff = {'amount': censor_rigidity_buff, 'duration': 2, 'party': hp.name}
            
        h_media_pwr = float(ha.get('alloc_med_control', 0.0))
        r_media_pwr = float(ra.get('alloc_med_control', 0.0))
        
        raw_p_plan, raw_p_exec, d_a, d_e, d_c = formulas.generate_raw_support(cfg, res_exec['est_gdp'], game.gdp, claimed_decay, bid_cost, res_exec['c_net'])
        
        plan_correct, plan_wrong, correct_prob = formulas.apply_sanity_filter(raw_p_plan, game.sanity, game.emotion, is_preview=False)
        exec_correct, exec_wrong, _ = formulas.apply_sanity_filter(raw_p_exec, game.sanity, game.emotion, is_preview=False)
        
        ruling_name = game.ruling_party.name
        ruling_media_pwr = h_media_pwr if ruling_name == hp.name else r_media_pwr
        opp_media_pwr = r_media_pwr if ruling_name == hp.name else h_media_pwr
            
        ruling_spun_plan, opp_spun_plan = formulas.apply_media_spin(plan_wrong, ruling_media_pwr, opp_media_pwr)
        h_spun_exec, r_spun_exec = formulas.apply_media_spin(exec_wrong, h_media_pwr, r_media_pwr)

        ammo_A = 0.0; ammo_B = 0.0

        if ruling_name == game.party_A.name: ammo_A += plan_correct + ruling_spun_plan; ammo_B += opp_spun_plan
        else: ammo_B += plan_correct + ruling_spun_plan; ammo_A += opp_spun_plan

        if hp.name == game.party_A.name: ammo_A += exec_correct + h_spun_exec; ammo_B += r_spun_exec
        else: ammo_B += exec_correct + h_spun_exec; ammo_A += r_spun_exec
            
        def get_camp_pwr(alloc, san, emo, edu_stance):
            rote_factor = max(0.0, -edu_stance / 100.0)
            return alloc * max(0.0, (1.0 - (san/100.0) + (emo/100.0) + rote_factor))

        h_camp_pwr = get_camp_pwr(float(ha.get('alloc_med_camp', 0.0)), game.sanity, game.emotion, hp.edu_stance)
        r_camp_pwr = get_camp_pwr(float(ra.get('alloc_med_camp', 0.0)), game.sanity, game.emotion, rp.edu_stance)

        if hp.name == game.party_A.name: ammo_A += h_camp_pwr; ammo_B += r_camp_pwr
        else: ammo_B += h_camp_pwr; ammo_A += r_camp_pwr

        net_ammo_A = ammo_A - ammo_B
        old_boundary = game.boundary_B
        
        new_boundary, used_ammo, conquered = formulas.run_conquest(game.boundary_B, net_ammo_A, game.sanity, getattr(game, 'h_rigidity_buff', {}).get('amount', 0.0), getattr(game, 'h_rigidity_buff', {}).get('party'), game.party_A.name)
        
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
            'ammo_A': ammo_A, 'ammo_B': ammo_B, 'net_ammo_A': net_ammo_A,
            'old_boundary': old_boundary, 'new_boundary': new_boundary, 'used_ammo': used_ammo, 'conquered': conquered,
            'correct_prob': correct_prob,
            'h_spun_exec': h_spun_exec, 'r_spun_exec': r_spun_exec, 
            'censor_successes': censor_successes, 'censor_failures': censor_failures, 'censor_emotion_add': censor_emotion_add, 'censor_buff': censor_rigidity_buff,
            'h_inc': hp_inc, 'r_inc': rp_inc, 
            'h_base': hp_base, 'r_base': rp_base, 
            'h_project_net': hp_project_net, 'r_project_net': rp_project_net,
            'payout_h': res_exec['payout_h'], 'act_fund': res_exec['act_fund'], 'r_pays': r_pays,
            'h_extra': safe_crony, 'r_extra': returned_to_r,
            'caught_crony': caught_crony,
            'fine_crony': fine_crony,
            'hp_penalty': hp_wealth_penalty,
            'crony_caught': crony_caught,
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
        if dice_data['crony_income'] > 0:
            st.markdown("---")
            st.markdown(f"### 🎲 {t('btn_roll_dice')} (監管單位介入調查)")
            if dice_data['crony_income'] > 0:
                if dice_data['chunk_size'] == float('inf'):
                    st.success(f"🛡️ **金流隱蔽成功**: 調查單位無功而返，未發現不當利得 ${dice_data['crony_income']:.1f}。")
                    if st.button("⏩ 確認並進入結算", type="primary", use_container_width=True):
                        st.session_state.pending_dice_roll['crony_results'] = (0.0, dice_data['crony_income'], 0.0)
                        st.session_state.pending_dice_roll['is_rolled'] = True
                        st.rerun()
                else:
                    st.warning(f"⚠️ **圖利調查**: 追查不當利得 ${dice_data['crony_income']:.1f} | 單次查獲率: `{dice_data['crony_catch_rate']*100:.1f}%` (每 `{dice_data['chunk_size']:.2f}` 元判定一次)")

                    if st.button("🎲 擲骰進行年度監管判定！", type="primary", use_container_width=True):
                        with st.spinner('監管單位正在進行全面搜查...'):
                            import time
                            time.sleep(1.5) 
                            crony_res = formulas.calc_corruption_dice(dice_data['crony_income'], dice_data['crony_catch_rate'], dice_data['fine_mult'], dice_data['chunk_size'])
                            st.session_state.pending_dice_roll['crony_results'] = crony_res
                            st.session_state.pending_dice_roll['is_rolled'] = True
                        st.rerun() 
            st.stop()

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
            if rep['h_extra'] > 0: st.write(f"- {t('safe_amount')} (Evaded Detection): `${rep['h_extra']:.1f}`")
            if rep.get('hp_penalty', 0) > 0: st.write(f"- 🚨 {t('fine_paid')} ({rep['fine_mult']}x Multiplier): `-${rep['hp_penalty']:.1f}`")
            st.write(f"- Eng. Invested Wealth: `-${rep['h_invest_wealth']:.1f}`")
            
            net_cash = rep['h_project_net'] + rep['h_base'] + rep['h_extra'] - rep.get('hp_penalty', 0) - rep['h_invest_wealth']
            st.write(f"**💰 Final Net Cash Flow: `${net_cash:.1f}`**")

        with st.expander(f"📊 {rep['r_party_name']} ({t('role_reg')}) Surplus & Profit Breakdown"):
            st.write(f"- Base Income (inc. Ruling Bonus): `${rep['r_base']:.1f}`")
            st.write(f"- 📤 Paid R-Subsidy: `-${rep['r_pays']:.1f}`")
            st.write(f"- 📥 Unspent Project Funds Recovered: `${rep['unspent_proj']:.1f}`")
            st.write(f"- 📥 Regulatory Budget Surplus: `${rep['base_r_surplus']:.1f}`")
            if rep['r_extra'] > 0: st.write(f"- 🏆 {t('caught_amount')} (From Opponent): `${rep['r_extra']:.1f}`")
            st.write(f"- Eng. Invested Wealth: `-${rep['r_invest_wealth']:.1f}`")
            
            net_cash_r = rep['r_base'] - rep['r_pays'] + rep['unspent_proj'] + rep['base_r_surplus'] + rep['r_extra'] - rep['r_invest_wealth']
            st.write(f"**💰 Final Net Cash Flow: `${net_cash_r:.1f}`**")

        if rep.get('crony_caught'): st.error(f"🚨 Cronyism Controversy! Regulator seized `{rep['caught_crony']:.1f}`. Fines (`{rep['fine_crony']:.1f}`) applied to Treasury.")

    with c2:
        st.markdown(f"### 🧠 {t('Society & Opinion')}")
        s_move = game.sanity - rep['old_san']
        e_move = game.emotion - rep['old_emo']
        
        st.write(f"**{t('Civic Literacy')}:** `{rep['old_san']:.1f}` ➔ `{game.sanity:.1f}` ({s_move:+.1f})")
        st.write(f"**{t('Voter Emotion')}:** `{rep['old_emo']:.1f}` ➔ `{game.emotion:.1f}` ({e_move:+.1f})")
        
        st.markdown("---")
        st.markdown(f"### ⚔️ Support Shift Resolution")
        st.caption(f"*(📡 This Year's Rational Attribution Rate: `{rep['correct_prob']*100:.1f}%`)*")
        
        if rep['h_spun_exec'] != 0 or rep['r_spun_exec'] != 0:
            st.info(f"📺 **Media Spin Output:** Executive media altered `{rep['h_spun_exec']:+.1f}` support points; Regulator media altered `{rep['r_spun_exec']:+.1f}` points!")
            
        if rep.get('censor_buff', 0) > 0:
            st.warning(f"⚖️ **Censorship Backlash:** Regulator's forced media suppression enraged `{rep['censor_successes']}` opponent units! Executive's voter rigidity drastically increased by `+{rep['censor_buff']:.3f}` for the next 2 years!")

        st.write(f"**{game.party_A.name} Total Support Force:** `{rep['ammo_A']:.1f}` | **{game.party_B.name} Total Support Force:** `{rep['ammo_B']:.1f}`")
        
        net_ammo = rep['net_ammo_A']
        atk_party = game.party_A.name if net_ammo > 0 else game.party_B.name
        def_party = game.party_B.name if net_ammo > 0 else game.party_A.name
        
        if abs(net_ammo) < 1.0: st.info("🤝 Support forces are deadlocked. No change in the political landscape.")
        else:
            st.success(f"**Net Support Advantage:** `{abs(net_ammo):.1f}` points! **{atk_party}** launched an influence wave against **{def_party}**!")
            old_sup = rep['old_boundary'] * 0.5; new_sup = rep['new_boundary'] * 0.5
            st.write(f"📊 👁️ **{game.party_A.name} New Support:** `{old_sup:.1f}%` ➔ `{new_sup:.1f}%`")

    st.markdown("---")
    if st.button(t("⏩ Confirm Report & Next Year"), type="primary", use_container_width=True):
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

