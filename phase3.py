# ==========================================
# phase3.py
# ==========================================
import streamlit as st
import formulas
import random

def render(game, cfg):
    st.header("⚖️ Phase 3: 年度總結算")
    
    rp, hp = game.r_role_party, game.h_role_party
    ra, ha = st.session_state[f"{rp.name}_acts"], st.session_state[f"{hp.name}_acts"]
    d = st.session_state.turn_data
    
    corr_amt = d.get('total_funds', 0) * (ha['corr'] / 100.0)
    crony_base = d.get('total_funds', 0) * (ha['crony'] / 100.0)
    suspicious_total = corr_amt + crony_base
    act_build = d.get('total_funds', 0) - corr_amt
    
    caught = False; fine = 0.0
    if suspicious_total > 0:
        eff_inv = (rp.depts['investigate'].eff * cfg['R_INV_BONUS']) + (ra['inv_corr'] * 0.5)
        catch_prob = min(1.0, (eff_inv / max(0.1, hp.depts['stealth'].eff)) * (suspicious_total / max(1.0, hp.wealth)) * 5.0)
        if random.random() < catch_prob:
            caught = True; fine = suspicious_total * cfg['CORRUPTION_PENALTY']; corr_amt = 0
            st.error(f"🚨 **弊案爆發！** 執行系統被查獲不法資金，重罰 ${fine:.0f}")

    h_bst = (act_build * d.get('h_ratio', 1.0) * (hp.depts['build'].eff/100.0)) / max(0.1, d.get('r_value', 1.0)**2)
    new_h_fund = max(0.0, game.h_fund + h_bst - (game.current_real_decay * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
    
    gdp_bst = (act_build * (hp.depts['build'].eff/100.0)) / cfg['BUILD_DIFF']
    new_gdp = max(0.0, game.gdp + gdp_bst - (game.current_real_decay * 1000))
    gdp_growth_pct = ((new_gdp - game.gdp) / max(1.0, game.gdp)) * 100.0

    new_san, new_emo = formulas.calculate_civic_shifts(
        cfg, game.sanity, game.emotion, gdp_growth_pct, 
        ha['edu_up']+ra['edu_up'], ha['edu_down']+ra['edu_down'], 
        ha['incite']+ra['incite'], hp.depts['edu'].eff + rp.depts['edu'].eff, 
        hp.depts['media'].eff + rp.depts['media'].eff
    )
    
    shift = formulas.calc_support_shift(cfg, hp, rp, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha, ra)
    if caught: shift['actual_shift'] -= 10.0 
    hp_sup_new = max(0.0, min(100.0, hp.support + shift['actual_shift']))
    
    st.success(f"📈 **GDP 結算:** {game.gdp:.0f} ➔ {new_gdp:.0f} ({gdp_growth_pct:+.2f}%)")
    st.info(f"🧠 **社會狀態:** 辨識度 {new_san*100:.1f} / 情緒值 {new_emo:.1f}")
    
    if st.button("⏩ 確認財報並進入下一年", type="primary", use_container_width=True):
        hp.support, rp.support = hp_sup_new, 100.0 - hp_sup_new
        game.gdp, game.sanity, game.emotion, game.h_fund = new_gdp, new_san, new_emo, new_h_fund
        
        # 扣除花費、升級部門與結算退款
        for p, acts in [(hp, ha), (rp, ra)]:
            # 1. 扣除政策基礎開銷
            p.wealth -= (acts['legal'] + acts['media'] + acts['camp'] + acts['incite'] + acts['edu_up'] + acts['edu_down'] + acts['inv_corr'])
            
            # 2. 部門資金結算 (扣除投資，若達標溢出則退款)
            u = acts['upgrades']
            for dept_key, ui_key in [('investigate', 'inv'), ('stealth', 'stl'), ('predict', 'pre'), ('media', 'med'), ('edu', 'edu'), ('build', 'bld')]:
                target_eff = u[ui_key][0]
                invested = u[ui_key][1]
                dept = p.depts[dept_key]
                _, refund = formulas.calc_upgrade(dept, target_eff, invested, cfg)
                p.wealth -= invested # 扣除這回合投資的錢
                p.wealth += refund   # 若達標溢出，退回溢出金額
            
            # 3. 扣除部門維護費 (依照「目標」計算)
            maint_cost = sum([formulas.get_ability_maintenance(dept, cfg) for dept in p.depts.values()])
            p.wealth -= maint_cost
            
        if game.year % cfg['ELECTION_CYCLE'] == 1:
            winner = hp if hp.support > rp.support else rp
            st.session_state.news_flash = f"🎉 **【大選結果】** {winner.name} 贏得民心，成為當權派！"
            game.ruling_party = winner

        game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
        game.year += 1; game.phase = 1; game.p1_step = 'draft_r'
        game.p1_proposals = {'R': None, 'H': None}; game.proposing_party = game.r_role_party
        
        for k in list(st.session_state.keys()):
            if k.endswith('_acts'): del st.session_state[k]
        del st.session_state.turn_initialized; st.rerun()
