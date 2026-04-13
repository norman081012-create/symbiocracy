# ==========================================
# phase2.py
# 負責 第二階段 (政策執行與結算) 的 UI 與邏輯
# ==========================================
import streamlit as st
import random
import config
import formulas
import ui_core
import i18n
t = i18n.t

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    h_label = t('🛡️ 執行系統', '🛡️ H-System')
    r_label = t('⚖️ 監管系統', '⚖️ R-System')
    st.subheader(t(f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name} ({h_label if is_h else r_label})", f"🛠️ Phase 2: Execution - Turn: {view_party.name} ({h_label if is_h else r_label})"))
    
    d = st.session_state.turn_data
    req_pay = d.get('h_pays', 0) if is_h else d.get('r_pays', 0)
    cw = max(0, int(view_party.wealth))
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(t("#### 📣 政策與媒體", "#### 📣 Policy & Media"))
        if is_h: st.caption(t("💡 **執行系統特性**: 媒體操控值 1.2 倍加成", "💡 **H-System Perk**: Media Control x1.2 Bonus"))
        else: st.caption(t("💡 **監管系統特性**: 調查能力值 1.2 倍加成", "💡 **R-System Perk**: Investigate x1.2 Bonus"))
        
        h_corr_pct = st.slider(t("💸 秘密貪污 (%)", "💸 Secret Corruption (%)"), 0, 100, 0) if is_h else 0
        h_crony_pct = st.slider(t("🏢 圖利自身廠商 (%)", "🏢 Cronyism (%)"), 0, max(0, 100 - h_corr_pct), 0) if is_h else 0
        
        judicial_amt = st.slider(t("⚖️ 司法審查 (投入資金)", "⚖️ Judicial Review (Funds)"), 0, cw, 0) if not is_h else 0
        media_ctrl = st.slider(t("📺 媒體操控 (投入資金)", "📺 Media Control (Funds)"), 0, cw, 0)
        
        edu_policy_amt = st.slider(t("🎓 教育方針 (左:填鴨 右:思辨, 投入資金)", "🎓 Education Policy (Left: Canned, Right: Critical)"), -cw, cw, 0) if not is_h else 0
        target_san = max(0.0, min(100.0, 50.0 + (edu_policy_amt / 500.0) * 50.0))
        san_move = (target_san - game.sanity) * 0.2
        new_san_preview = game.sanity + san_move
        if not is_h:
            st.caption(t(f"資訊辨識: {config.get_civic_index_text(game.sanity)} -> {config.get_civic_index_text(new_san_preview)} (變動: {san_move:+.1f}/年)", f"Civic Lit: {config.get_civic_index_text(game.sanity)} -> {config.get_civic_index_text(new_san_preview)} (Chg: {san_move:+.1f}/yr)"))
            
        camp_amt = st.slider(t("🎉 舉辦競選 (投入資金)", "🎉 Campaign (Funds)"), 0, cw, 0)
        incite_emo = st.slider(t("🔥 煽動情緒 (投入資金)", "🔥 Incite Emotion (Funds)"), 0, cw, 0)
        
    with c2:
        st.markdown(t("#### 🔒 內部部門投資", "#### 🔒 Dept. Investment"))
        t_pre, c_pre = ui_core.ability_slider(t("智庫", "Think Tank"), f"up_pre", view_party.predict_ability, cw, cfg)
        t_inv, c_inv = ui_core.ability_slider(t("情報處", "Intelligence"), f"up_inv", view_party.investigate_ability, cw, cfg)
        t_med, c_med = ui_core.ability_slider(t("黨媒", "Media Dept."), f"up_med", view_party.media_ability, cw, cfg)
        t_stl, c_stl = ui_core.ability_slider(t("反情報處", "Counter-Intel"), f"up_stl", view_party.stealth_ability, cw, cfg)
        t_bld, c_bld = ui_core.ability_slider(t("工程處", "Engineering"), f"up_bld", view_party.build_ability, cw, cfg) if is_h else (view_party.build_ability, 0)

    tot_action = media_ctrl + camp_amt + incite_emo + abs(edu_policy_amt) + judicial_amt
    tot_maint = c_inv + c_pre + c_med + c_stl + c_bld
    tot = req_pay + tot_action + tot_maint
    
    st.write(t(f"**法定專案款:** `{int(req_pay)}` / **政策與媒體:** `{int(tot_action)}` / **內部部門投資:** `{int(tot_maint)}` / **剩餘可用淨值:** `{int(cw - tot)}`", f"**Legal Pay:** `{int(req_pay)}` / **Policy:** `{int(tot_action)}` / **Invest:** `{int(tot_maint)}` / **Remaining:** `{int(cw - tot)}`"))
    
    if tot > cw:
        st.error(t(f"🚨 資金不足！當前行動預算已超支 {int(tot - cw)} 元，請降低投入資金。", f"🚨 Insufficient Funds! Over budget by {int(tot - cw)}. Reduce spending."))
    
    ra, ha = {}, {}
    if f"{opponent_party.name}_acts" in st.session_state:
        opp_acts = st.session_state[f"{opponent_party.name}_acts"]
        ra = opp_acts if is_h else {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt}
        ha = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt} if is_h else opp_acts
    else:
        ra = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt} if not is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_amt': 0, 'corr': 0, 'crony': 0, 'judicial': 0}
        ha = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt} if is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_amt': 0, 'corr': 0, 'crony': 0, 'judicial': 0}

    corr_amt = d.get('total_funds', 0) * (ha.get('corr', 0) / 100.0)
    crony_base = d.get('total_funds', 0) * (ha.get('crony', 0) / 100.0)
    crony_income = crony_base * 0.1 * d.get('r_value', 1.0)
    act_build = d.get('total_funds', 0) - corr_amt
    
    h_bst = (act_build * d.get('h_ratio', 1.0) * game.h_role_party.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
    new_h_fund = max(0.0, game.h_fund + h_bst - (view_party.current_forecast * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
    gdp_bst = (act_build * game.h_role_party.build_ability) / cfg['BUILD_DIFF']
    new_gdp = max(0.0, game.gdp + gdp_bst - (view_party.current_forecast * 1000))
    budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
    h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
    
    hp_inc_est = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.h_role_party.name else 0) + (budg * h_shr) - d.get('h_pays',0) + corr_amt + crony_income
    rp_inc_est = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == game.r_role_party.name else 0) + (budg * (1 - h_shr)) - d.get('r_pays',0)

    shift_preview = formulas.calc_support_shift(cfg, game.h_role_party, game.r_role_party, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha, ra)
    
    t_san_preview = max(0.0, min(100.0, 50.0 + (ra.get('edu_amt', 0) / 500.0) * 50.0))
    s_move_preview = (t_san_preview - game.sanity) * 0.2
    
    preview_data = {
        'gdp': new_gdp, 'budg': budg, 'h_fund': new_h_fund,
        'san': max(0.0, min(100.0, game.sanity - (game.emotion * 0.02) + s_move_preview)),
        'emo': max(0.0, min(100.0, game.emotion + (ha['incite'] + ra['incite']) * 0.1 - (((new_gdp - game.gdp)/max(1.0, game.gdp))*100) - (game.sanity * 0.20))),
        'h_inc': hp_inc_est, 'r_inc': rp_inc_est,
        'h_roi': (hp_inc_est / max(1.0, float(d.get('h_pays',0)))) * 100.0 if d.get('h_pays',0) > 0 else float('inf'),
        'r_roi': (rp_inc_est / max(1.0, float(d.get('r_pays',0)))) * 100.0 if d.get('r_pays',0) > 0 else float('inf'),
        'my_sup_shift': shift_preview['actual_shift'] if is_h else -shift_preview['actual_shift'],
        'opp_sup_shift': -shift_preview['actual_shift'] if is_h else shift_preview['actual_shift']
    }
    
    ui_core.render_dashboard(game, view_party, cfg, is_preview=True, preview_data=preview_data)
    
    if tot <= cw and st.button(t("確認行動/結算", "Confirm & Execute"), use_container_width=True, type="primary"):
        st.session_state[f"{view_party.name}_acts"] = {
            'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_amt': edu_policy_amt, 
            'corr': h_corr_pct, 'crony': h_crony_pct, 'judicial': judicial_amt,
            't_inv': t_inv, 't_pre': t_pre, 't_med': t_med, 't_edu': view_party.edu_ability, 't_stl': t_stl, 't_bld': t_bld,
            'legal': req_pay
        }
        
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            rp, hp = game.r_role_party, game.h_role_party
            ra, ha = st.session_state[f"{rp.name}_acts"], st.session_state[f"{hp.name}_acts"]
            
            hp.last_acts = {'policy': ha['media']+ha['camp']+ha['incite']+abs(ha['edu_amt'])+ha['judicial'], 'legal': ha['legal']}
            rp.last_acts = {'policy': ra['media']+ra['camp']+ra['incite']+abs(ra['edu_amt'])+ra['judicial'], 'legal': ra['legal']}

            confiscated = 0.0; caught = False; fine = 0.0
            corr_amt = d.get('total_funds', 0) * (ha['corr'] / 100.0)
            crony_base = d.get('total_funds', 0) * (ha['crony'] / 100.0)
            crony_income = crony_base * 0.1 * d.get('r_value', 1.0)
            suspicious_total = corr_amt + crony_base
            act_build = d.get('total_funds', 0) - corr_amt
            
            if suspicious_total > 0:
                eff_inv = (rp.investigate_ability * cfg['R_INV_BONUS'])
                catch_prob = min(1.0, (eff_inv / max(0.1, hp.stealth_ability)) * (suspicious_total / max(1.0, hp.wealth)) * 5.0)
                if random.random() < catch_prob:
                    caught = True; fine = suspicious_total * cfg['CORRUPTION_PENALTY']; confiscated = suspicious_total; corr_amt = 0; crony_income = 0
            
            h_bst = (act_build * d.get('h_ratio', 1.0) * hp.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
            new_h_fund = max(0.0, game.h_fund + h_bst - (game.current_real_decay * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
            
            gdp_bst = (act_build * hp.build_ability) / cfg['BUILD_DIFF']
            new_gdp = max(0.0, game.gdp + gdp_bst - (game.current_real_decay * 1000))
            budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
            h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
            
            hp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == hp.name else 0) + (budg * h_shr) - d.get('h_pays',0) + corr_amt + crony_income - fine
            rp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == rp.name else 0) + (budg * (1 - h_shr)) - d.get('r_pays',0)
            
            shift = formulas.calc_support_shift(cfg, hp, rp, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha, ra)
            if caught: shift['actual_shift'] -= 5.0
            hp_sup_new = max(0.0, min(100.0, hp.support + shift['actual_shift']))
            
            gdp_grw_bonus = ((new_gdp - game.gdp)/max(1.0, game.gdp)) * 100.0
            emotion_delta = (ha['incite'] + ra['incite']) * 0.1 - gdp_grw_bonus - (game.sanity * 0.20)
            game.emotion = max(0.0, min(100.0, game.emotion + emotion_delta))
            
            f_target_san = max(0.0, min(100.0, 50.0 + (ra.get('edu_amt', 0) / 500.0) * 50.0))
            f_san_move = (f_target_san - game.sanity) * 0.2
            game.sanity = max(0.0, min(100.0, game.sanity - (game.emotion * 0.02) + f_san_move))
            
            game.last_year_report = {
                'old_gdp': game.gdp, 'old_san': game.sanity, 'old_emo': game.emotion, 'old_budg': game.total_budget, 'old_h_fund': game.h_fund,
                'h_party_name': hp.name, 'h_perf': shift['h_perf'], 'r_perf': shift['r_perf'],
                'h_inc': hp_inc, 'r_inc': rp_inc, 'est_h_inc': preview_data['h_inc'], 'est_r_inc': preview_data['r_inc'],
                'real_decay': game.current_real_decay, 'view_party_forecast': view_party.current_forecast
            }

            hp.support, rp.support = hp_sup_new, 100.0 - hp_sup_new
            
            if game.year % cfg['ELECTION_CYCLE'] == 1:
                winner = hp if hp.support > rp.support else rp
                st.session_state.news_flash = t(f"🎉 **【大選結果】** {winner.name} 取勝，成為當權派！", f"🎉 **[ELECTION]** {winner.name} won and became ruling party!")
                st.session_state.anim = 'balloons'
                game.ruling_party = winner

            game.h_fund, game.gdp = new_h_fund, new_gdp
            game.total_budget = budg + confiscated
            hp.wealth += hp_inc; rp.wealth += rp_inc

            rp.investigate_ability = ra['t_inv']; rp.predict_ability = ra['t_pre']; rp.media_ability = ra['t_med']; rp.stealth_ability = ra['t_stl']
            hp.investigate_ability = ha['t_inv']; hp.predict_ability = ha['t_pre']; hp.media_ability = ha['t_med']; hp.stealth_ability = ha['t_stl']; hp.build_ability = ha['t_bld']

            game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
            
            game.year += 1; game.phase = 1; game.p1_step = 'draft_r'
            game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
            game.proposing_party = game.r_role_party
            for k in list(st.session_state.keys()):
                if k.startswith('ui_decay_') or k.endswith('_acts'): del st.session_state[k]
            del st.session_state.turn_initialized; st.rerun()
