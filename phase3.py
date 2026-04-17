# ==========================================
# phase3.py
# ==========================================
import streamlit as st
import random
import formulas
import i18n
t = i18n.t

def render(game, cfg):
    st.header("共生體制時報 - 年度結算報告")
    
    if not game.last_year_report:
        rp, hp = game.r_role_party, game.h_role_party
        ra = st.session_state.get(f"{rp.name}_acts", {})
        ha = st.session_state.get(f"{hp.name}_acts", {})
        d = st.session_state.get('turn_data', {})
        
        fine_mult = float(d.get('fine_mult', 0.3)) 
        
        # --- Fix 1: 優先處理假 EV 查核與擲骰 UI ---
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

        # 🚨 阻斷點：如果還沒擲骰，顯示 UI 並停止後續所有結算！
        if not dice_data['is_rolled']:
            st.markdown("---")
            st.markdown(f"### 🎲 啟動財務查核")
            if dice_data['chunk_size'] == float('inf'):
                st.info("監管系統缺乏足夠的操作量能來啟動查核。金流成功隱蔽。")
                if st.button("⏩ 進入最終結算", type="primary", use_container_width=True):
                    st.session_state.pending_dice_roll['fake_ev_results'] = (0.0, dice_data['fake_ev'], 0.0, 0.0)
                    st.session_state.pending_dice_roll['is_rolled'] = True
                    st.rerun()
            else:
                st.warning(f"**目標：** `{dice_data['fake_ev']:.1f}` 假 EV | **抓包機率：** 每 `{dice_data['chunk_size']:.2f}` 單位有 `{dice_data['catch_prob']*100:.1f}%` 機率。")

                if st.button("🎲 執行財務查核！", type="primary", use_container_width=True):
                    with st.spinner('調查員正在追蹤金流...'):
                        import time
                        time.sleep(1.5) 
                        fake_ev_res = formulas.calc_fake_ev_dice(dice_data['fake_ev'], dice_data['catch_prob'], dice_data['fine_mult'], dice_data['chunk_size'], dice_data['unit_cost_real'])
                        st.session_state.pending_dice_roll['fake_ev_results'] = fake_ev_res
                        st.session_state.pending_dice_roll['is_rolled'] = True
                    st.rerun() 
            st.stop() # ⚠️ 關鍵：在這裡停下，等待重新渲染

        # --- 擲骰完成，提取結果 ---
        caught_fake_ev, safe_fake_ev, caught_value, fine_value = dice_data['fake_ev_results']
        fake_ev_caught = (caught_fake_ev > 0)
        
        returned_to_r = caught_value
        confiscated_to_budget = fine_value
        hp_wealth_penalty = (caught_value + fine_value)
        
        # --- 寫回部門能力 ---
        for k in ['t_pre', 't_inv', 't_med', 't_stl', 't_bld', 't_edu', 'edu_stance']:
            if k in ra: setattr(rp, 'predict_ability' if k == 't_pre' else 'investigate_ability' if k == 't_inv' else 'media_ability' if k == 't_med' else 'stealth_ability' if k == 't_stl' else 'build_ability' if k == 't_bld' else 'edu_ability' if k == 't_edu' else 'edu_stance', float(ra[k]))
            if k in ha: setattr(hp, 'predict_ability' if k == 't_pre' else 'investigate_ability' if k == 't_inv' else 'media_ability' if k == 't_med' else 'stealth_ability' if k == 't_stl' else 'build_ability' if k == 't_bld' else 'edu_ability' if k == 't_edu' else 'edu_stance', float(ha[k]))

        req_cost = float(d.get('req_cost', 0.0))
        proj_fund = float(d.get('proj_fund') or 0.0)
        bid_cost = float(d.get('bid_cost') or 1.0)
        claimed_decay = float(d.get('claimed_decay') or 0.0)
        r_pays = float(d.get('r_pays') or 0.0)
        
        hp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == hp.name else 0))
        rp_base = game.total_budget * (cfg['BASE_INCOME_RATIO'] + (cfg['RULING_BONUS_RATIO'] if game.ruling_party.name == rp.name else 0))
        
        actual_h_wealth_available = max(0.0, hp.wealth + req_cost - float(ha.get('invest_wealth', 0)) - hp_wealth_penalty + hp_base)
        
        eval_fake_ev_safe = safe_fake_ev
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
    
    rep = game.last_year_report
    
    st.markdown("---")
    st.markdown("### 🗞️ **[頭版頭條]**")
    if rep.get('caught_fake_ev', 0) > 0:
        st.error(f"**[貪腐醜聞] 豆腐渣工程曝光！**\n\n調查員揭發了 `{rep['caught_fake_ev']:.1f}` 單位的造假工程 (假 EV)。\n- **{rep['h_party_name']}** 遭沒收非法所得 `${rep['caught_value']:.1f}` 並裁罰 `${rep['fine_value']:.1f}`。\n- **{rep['r_party_name']}** 獲得全額吹哨者獎金 `${rep['caught_value']:.1f}`。\n- 國庫收取 `${rep['fine_value']:.1f}` 的懲罰性罰金。")
    else:
        if rep.get('chunk_size', float('inf')) == float('inf'):
            st.success(f"**[粉飾太平] 查無不法？**\n\n監管系統未能徹底調查金流。所有帳目在「字面上」皆合法過關。")
        elif rep.get('fake_ev_attempted', 0) > 0:
            st.success(f"**[全身而退] 查核過關！**\n\n儘管進行了嚴格調查，執政黨的「特別帳戶」依然滴水不漏。")
        else:
            st.success(f"**[廉能政府] 零造假工程！**\n\n調查員翻遍了帳冊，確認所有專案皆為 100% 真材實料。")
            
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 📊 經濟指標")
        st.write(f"- **GDP:** `{rep['old_gdp']:.1f}` ➔ **`{game.gdp:.1f}`**")
        st.write(f"- **公民素養:** `{rep['old_san']:.1f}` ➔ **`{game.sanity:.1f}`** ({game.sanity - rep['old_san']:+.1f})")
        st.write(f"- **選民情緒:** `{rep['old_emo']:.1f}` ➔ **`{game.emotion:.1f}`** ({game.emotion - rep['old_emo']:+.1f})")
        
        st.markdown(f"### 🏛️ 財政總結")
        if rep['fine_value'] > 0:
            st.success(f"國庫收入: +`${rep['fine_value']:.1f}` (懲罰性罰金)")
        
        with st.expander(f"💼 {rep['h_party_name']} (執行方) 財務報表"):
            st.write(f"**專案淨利潤:** `${rep['h_project_net']:.1f}`")
            st.write(f"+ 基本收入: `${rep['h_base']:.1f}`")
            if rep['caught_fake_ev'] > 0:
                st.write(f"- 沒收不法所得: `-${rep['caught_value']:.1f}`")
                st.write(f"- 懲罰性罰金: `-${rep['fine_value']:.1f}`")
            st.write(f"- 工程/部門升級成本: `-${rep['h_invest_wealth']:.1f}`")
            net_cash = rep['h_project_net'] + rep['h_base'] - rep.get('hp_penalty', 0) - rep['h_invest_wealth']
            st.write(f"**最終現金流:** `${net_cash:.1f}`")

        with st.expander(f"⚖️ {rep['r_party_name']} (監管方) 財務報表"):
            st.write(f"**基本收入:** `${rep['r_base']:.1f}`")
            st.write(f"- 支付監管墊付款: `-${rep['r_pays']:.1f}`")
            st.write(f"+ 追回未執行資金: `${rep['unspent_proj']:.1f}`")
            st.write(f"+ 預算結餘: `${rep['base_r_surplus']:.1f}`")
            if rep['r_extra'] > 0: 
                st.write(f"+ 吹哨者獎金: `${rep['r_extra']:.1f}`")
            st.write(f"- 部門升級成本: `-${rep['r_invest_wealth']:.1f}`")
            net_cash_r = rep['r_base'] - rep['r_pays'] + rep['unspent_proj'] + rep['base_r_surplus'] + rep['r_extra'] - rep['r_invest_wealth']
            st.write(f"**最終現金流:** `${net_cash_r:.1f}`")

    with c2:
        st.markdown(f"### 🗳️ 選舉板塊位移 (支持度)")
        
        net_ammo = rep['net_perf_A'] + rep['net_spin_A']
        atk_party = game.party_A.name if net_ammo > 0 else game.party_B.name
        def_party = game.party_B.name if net_ammo > 0 else game.party_A.name
        
        if abs(net_ammo) < 1.0: 
            st.info("🤝 雙方支持度僵持不下，未產生顯著的板塊位移。")
        else:
            st.success(f"🔥 **淨優勢:** `{abs(net_ammo):.1f}`！**{atk_party}** 對 **{def_party}** 發動了影響力攻勢！")

        if st.session_state.get('god_mode'):
            with st.expander("👁️ 上帝模式：選舉機制與真實支持度", expanded=True):
                st.write(f"*(理性歸因率: `{rep['correct_prob']*100:.1f}%`)*")
                
                # --- Fix 2: 修復政績表現 UI ---
                st.markdown(f"**政績表現 (真實傷害)**: {game.party_A.name} `{rep['perf_A']:.1f}` | {game.party_B.name} `{rep['perf_B']:.1f}`")
                if abs(rep['net_perf_A']) >= 1.0:
                    atk_p = game.party_A.name if rep['net_perf_A'] > 0 else game.party_B.name
                    perf_blocked = rep['perf_used'] - rep['perf_conquered']
                    st.success(f"⚡ **政績與大環境影響**: {atk_p} 發動了 `{rep['perf_used']:.1f}` 點影響。政黨基本盤固著度抵擋了 `{perf_blocked:.1f}` 點影響，最終征服了 **{rep['perf_conquered']}** 個票倉！")
                    
                st.markdown(f"**媒體與公關 (可防禦)**: {game.party_A.name} `{rep['spin_A']:.1f}` | {game.party_B.name} `{rep['spin_B']:.1f}`")
                if abs(rep['net_spin_A']) >= 1.0:
                    atk_s = game.party_A.name if rep['net_spin_A'] > 0 else game.party_B.name
                    blocked = rep['spin_used'] - rep['spin_conquered']
                    st.warning(f"🛡️ 選民理性護甲吸收了 `{blocked:.1f}` 點公關影響。{atk_s} 征服了 **{rep['spin_conquered']}** 個票倉。")

                old_sup_A = rep['old_boundary'] * 0.5
                new_sup_A = rep['new_boundary'] * 0.5
                old_sup_B = 100.0 - old_sup_A
                new_sup_B = 100.0 - new_sup_A
                
                st.markdown(f"#### 📊 **{game.party_A.name} 真實支持度:** `{old_sup_A:.1f}%` ➔ **`{new_sup_A:.1f}%`** ({new_sup_A - old_sup_A:+.1f}%)")
                st.markdown(f"#### 📊 **{game.party_B.name} 真實支持度:** `{old_sup_B:.1f}%` ➔ **`{new_sup_B:.1f}%`** ({new_sup_B - old_sup_B:+.1f}%)")
        else:
            st.caption("*(真實支持度百分比已隱藏。請進行民調以揭露當前局勢。)*")

    st.markdown("---")
    if st.button("⏩ 進入下一年", type="primary", use_container_width=True):
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
