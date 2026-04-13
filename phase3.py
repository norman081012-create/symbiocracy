# ==========================================
# phase3.py
# ==========================================
import streamlit as st
import formulas

def render(game, cfg):
    st.header("⚖️ Phase 3: 年度實體結算與收益分配")
    
    hp, rp = game.h_role_party, game.r_role_party
    ha, ra = st.session_state[f"{hp.name}_acts"], st.session_state[f"{rp.name}_acts"]
    d = st.session_state.turn_data
    
    # 計算真實產出與 GDP
    real_gdp, real_h_inc, real_r_inc, h_idx, c_net = formulas.calc_economic_preview(
        cfg, game.current_real_decay, game.gdp, game.current_budget_pool, 
        d['proj_fund'], d['strictness'], hp.depts['build'].eff
    )

    new_san, new_emo = formulas.calculate_civic_shifts(
        cfg, game.sanity, game.emotion, ((real_gdp - game.gdp)/game.gdp)*100, 
        ha['edu_up']+ra['edu_up'], 0, 0, 
        hp.depts['edu'].eff + rp.depts['edu'].eff, hp.depts['media'].eff + rp.depts['media'].eff
    )
    
    st.success(f"📈 **GDP 結算:** {game.gdp:.0f} ➔ {real_gdp:.0f}")
    st.info(f"💰 **跨年發放預定 (將於明年初入帳):**\n- {hp.name}(執行): +${real_h_inc:.0f}\n- {rp.name}(監管): +${real_r_inc:.0f} (含殘值)")
    
    if st.button("⏩ 確認財報並進入下一年", type="primary", use_container_width=True):
        game.gdp, game.sanity, game.emotion = real_gdp, new_san, new_emo
        
        # 將收益存入 pending_payouts，明年第一回合初始化時發放
        game.pending_payouts['A'] = real_h_inc if hp.name == game.party_A.name else real_r_inc
        game.pending_payouts['B'] = real_h_inc if hp.name == game.party_B.name else real_r_inc
        
        # 扣除花費與處理升級
        for p, acts in [(hp, ha), (rp, ra)]:
            p.wealth -= (acts['camp'] + acts['edu_up'])
            u = acts['upgrades']
            for dept_key, ui_key in [('investigate', 'inv'), ('predict', 'pre'), ('edu', 'edu'), ('build', 'bld')]:
                target_eff, invested = u[ui_key]
                dept = p.depts[dept_key]
                _, refund = formulas.calc_upgrade(dept, target_eff, invested, cfg)
                p.wealth -= invested 
                p.wealth += refund   
            p.wealth -= sum([formulas.get_ability_maintenance(dept, cfg) for dept in p.depts.values()])
            
        if game.year % cfg['ELECTION_CYCLE'] == 1:
            winner = hp if hp.support > rp.support else rp
            st.session_state.news_flash = f"🎉 **【大選結果】** {winner.name} 贏得民心，成為當權！"
            game.ruling_party = winner

        game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
        game.year += 1; game.phase = 1; game.p1_step = 'draft_r'
        game.proposing_party = game.r_role_party
        
        for k in list(st.session_state.keys()):
            if k.endswith('_acts'): del st.session_state[k]
        del st.session_state.turn_initialized; st.rerun()
