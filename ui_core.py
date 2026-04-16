# ==========================================
# ui_core.py
# ==========================================
import streamlit as st
import random
import math
import config
import formulas
import engine
import i18n
t = i18n.t

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_global_settings(cfg, game):
    st.sidebar.title(t("🎛️ Control Panel"))
    lang = st.session_state.get('lang', 'EN')
    btn_text = "🌐 Switch to Chinese" if lang == 'EN' else "🌐 Switch to English"
    if st.sidebar.button(btn_text, use_container_width=True):
        st.session_state.lang = 'ZH' if lang == 'EN' else 'EN'
        st.rerun()

    with st.sidebar.expander(t("📝 Live Parameters"), expanded=False):
        trans = config.get_config_translations()
        for key, default_val in config.DEFAULT_CONFIG.items():
            label = trans.get(key, key)
            if 'COLOR' in key: cfg[key] = st.color_picker(label, value=cfg[key], key=f"cfg_{key}")
            elif isinstance(default_val, float): cfg[key] = st.number_input(label, value=float(cfg[key]), step=0.1, format="%.2f", key=f"cfg_{key}")
            elif isinstance(default_val, int): cfg[key] = st.number_input(label, value=int(cfg[key]), step=1, key=f"cfg_{key}")
            elif isinstance(default_val, str): cfg[key] = st.text_input(label, value=str(cfg[key]), key=f"cfg_{key}")
    sync_party_names(game, cfg)

def render_dashboard(game, view_party, cfg, is_preview=False, preview_data=None):
    rep = game.last_year_report
    st.markdown("---")
    
    disp_gdp = preview_data['gdp'] if is_preview else game.gdp
    disp_san = preview_data['san'] if is_preview else game.sanity
    disp_emo = preview_data['emo'] if is_preview else game.emotion
    disp_h_fund = preview_data['h_fund'] if is_preview else game.h_fund
    disp_budg = preview_data['budg'] if is_preview else game.total_budget
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(t("### 🌐 National Status"))
        san_chg = (disp_san - rep['old_san']) if rep else 0
        c_color = "green" if san_chg > 0 else "red" if san_chg < 0 else "gray"
        
        emo_chg = disp_emo - rep['old_emo'] if rep else 0
        e_color = "red" if emo_chg > 0 else "green" if emo_chg < 0 else "gray"
        
        st.markdown(f"**{t('Civic Literacy')}:** {config.get_civic_index_text(disp_san)} <span style='color:{c_color}'>*({san_chg:+.1f})*</span> &nbsp;&nbsp; **{t('Voter Emotion')}:** {config.get_emotion_text(disp_emo)} <span style='color:{e_color}'>*({emo_chg:+.1f})*</span>", unsafe_allow_html=True)
        
        crit_think = disp_san / 100.0
        emo_val = disp_emo / 100.0
        prob = max(0.05, min(0.95, crit_think * (1.0 - emo_val * 0.5)))
        st.markdown(f"**Rational Attribution Rate:** `{prob*100:.1f}%`")
        
        gdp_base = rep['old_gdp'] if rep else game.gdp
        gdp_diff = disp_gdp - gdp_base
        gdp_pct = (gdp_diff / max(1.0, gdp_base)) * 100.0
        g_color = "green" if gdp_diff > 0 else "red" if gdp_diff < 0 else "gray"
        label_gdp = t("Est. GDP") if is_preview else t("Current GDP")
        st.markdown(f"**{label_gdp}:** `{disp_gdp:.1f}` <span style='color:{g_color}'>*({gdp_diff:+.1f}, {gdp_pct:+.2f}%)*</span>", unsafe_allow_html=True)

    with c2:
        st.markdown(t("### 💰 Executive Resources"))
        if game.year == 1 and not is_preview: st.info("First year reorganization, rewards pending.")
        else:
            current_h_ratio = (disp_h_fund / disp_budg) * 100 if disp_budg > 0 else 50
            budg_chg = disp_budg - rep['old_budg'] if rep else 0
            b_color = "green" if budg_chg > 0 else "red" if budg_chg < 0 else "gray"
            st.markdown(f"**{t('Total Budget Pool')}:** `{disp_budg:.1f}` <span style='color:{b_color}'>*({budg_chg:+.1f})*</span>", unsafe_allow_html=True)
            st.markdown(f"**{t('Reward Fund')}:** `{disp_h_fund:.1f}` *({t('Share')}: {current_h_ratio:.1f}%)*")

    with c3:
        fc = view_party.current_forecast
        p_acc_weight = cfg.get('PREDICT_ACCURACY_WEIGHT', 0.8)
        acc = int(((view_party.predict_ability / 10.0) * p_acc_weight) * 100)
        st.markdown(f"### 🕵️ {t('Think Tank Intel')} (Acc: {acc}%)")
        
        st.write(f"Est. Decay: `{fc:.3f}`")
        eval_scenario = config.get_economic_forecast_text(fc * 100)
        st.info(eval_scenario)
        
        if rep:
            my_is_h = view_party.name == rep['h_party_name']
            past_forecast = rep.get('h_forecast') if my_is_h else rep.get('r_forecast')
            if past_forecast is not None:
                diff = abs(past_forecast - rep['real_decay'])
                eval_txt = config.get_thinktank_eval(view_party.predict_ability, diff)
                st.write(f"({cfg['CALENDAR_NAME']} {game.year-1} Internal Audit: **{eval_txt}**)")

    with c4:
        if game.phase == 1:
            st.markdown(t("### 📊 Financial Report"))
            if game.year == 1:
                st.write(f"{t('Available Net Assets')}: **{view_party.wealth:.1f}**")
            else:
                st.write(f"{t('Available Net Assets')}: **{view_party.wealth:.1f}**")
                
            if rep:
                my_is_h = view_party.name == rep['h_party_name']
                base = rep['h_base'] if my_is_h else rep['r_base']
                proj = rep['h_project_net'] if my_is_h else rep['r_project_net']
                extra = rep['h_extra'] if my_is_h else rep['r_extra']
                penalty = rep.get('hp_penalty', 0.0) if my_is_h else 0.0
                inv_w = rep['h_invest_wealth'] if my_is_h else rep['r_invest_wealth']
                
                real_inc_gross = base + proj + extra
                expenses = inv_w + penalty
                real_inc_net = real_inc_gross - expenses
                
                st.markdown(f"**Last Yr Net Flow: `{real_inc_net:+.1f}`**")
                st.caption(f"*(➕ Base `{base:.1f}` | Proj `{proj:.1f}` | Extra `{extra:.1f}`)*")
                st.caption(f"*(➖ Invested `{inv_w:.1f}` | Fine `{penalty:.1f}`)*")
        else:
            if is_preview:
                my_net = preview_data['h_inc'] if (view_party.name == game.h_role_party.name) else preview_data['r_inc']
                opp_net = preview_data['r_inc'] if (view_party.name == game.h_role_party.name) else preview_data['h_inc']
                
                st.markdown(t("### 📊 Think Tank Report"))
                def fmt_roi(val): return "∞%" if val == float('inf') else f"{val:+.1f}%"
                
                st.markdown(f"{t('Our Est. Net Profit')}: **{my_net:.1f}** (Project ROI: {fmt_roi(preview_data.get('my_roi', 0))})")
                st.markdown(f"{t('Opp. Est. Net Profit')}: **{opp_net:.1f}** (Project ROI: {fmt_roi(preview_data.get('opp_roi', 0))})")
                
                my_gdp_perf = preview_data['my_perf_gdp']
                my_proj_perf = preview_data['my_perf_proj']
                my_total_perf = my_gdp_perf + my_proj_perf

                opp_gdp_perf = preview_data['opp_perf_gdp']
                opp_proj_perf = preview_data['opp_perf_proj']
                opp_total_perf = opp_gdp_perf + opp_proj_perf

                st.markdown(f"{t('Total Expected Support')}:")
                st.markdown(f"&nbsp;&nbsp;🔹 **Our Total: `{my_total_perf:+.1f}`** *(Base: {my_gdp_perf:+.1f} | Proj: {my_proj_perf:+.1f})*")
                st.markdown(f"&nbsp;&nbsp;🔸 **Opp. Total: `{opp_total_perf:+.1f}`** *(Base: {opp_gdp_perf:+.1f} | Proj: {opp_proj_perf:+.1f})*")
                
    st.markdown("---")

def render_message_board(game):
    if st.session_state.get('news_flash'):
        st.warning(st.session_state.news_flash)
        st.session_state.news_flash = None
        
    if game.phase == 1:
        if game.year == 1: st.info("📢 **[ANNUAL NOTICE]** A new year begins. The nation awaits rebuilding; initiate budget negotiations immediately.")
        elif game.last_year_report: st.info("📢 **[ANNUAL NOTICE]** A new year begins. Initiate budget negotiations.")
    elif game.phase == 2:
        st.info("📢 **[ANNUAL NOTICE]** Bill passed. Allocate party funds for internal upgrades, campaigns, and media warfare.")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    st.header(t("👤 Party Overview"))
    c1, c2 = st.columns(2)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    
    st.markdown(f"""
    <style>
    div[data-testid="column"]:nth-child(1) {{ background-color: {cfg['PARTY_A_COLOR']}1A; padding: 15px; border-radius: 10px; border-left: 5px solid {cfg['PARTY_A_COLOR']}; }}
    div[data-testid="column"]:nth-child(2) {{ background-color: {cfg['PARTY_B_COLOR']}1A; padding: 15px; border-radius: 10px; border-left: 5px solid {cfg['PARTY_B_COLOR']}; }}
    </style>
    """, unsafe_allow_html=True)

    for col, party in zip([c1, c2], [view_party, opp]):
        with col:
            is_h = (game.h_role_party.name == party.name)
            role_badge = t("🛡️ [H-System]") if is_h else t("⚖️ [R-System]")
            is_winner = (game.ruling_party.name == party.name)
            crown_str = cfg.get('CROWN_WINNER', t('👑 Ruling')) if is_winner else cfg.get('CROWN_LOSER', t('🎯 Candidate'))
            logo = config.get_party_logo(party.name)
            
            eye = "👁️ " if party.name == view_party.name else ""
            st.markdown(f"## {eye}{logo} {party.name} {crown_str}")
            st.markdown(f"#### {role_badge}")

            if party.name == view_party.name:
                st.markdown(f"### 💰 **{t('Party Wealth')}:** `${party.wealth:.1f}`")
            else:
                rng = random.Random(f"wealth_{party.name}_{game.year}")
                opp_stl = party.stealth_ability / 10.0
                my_inv_raw = view_party.investigate_ability / 10.0
                err_margin = max(0.0, 1.0 + opp_stl - my_inv_raw) * cfg.get('OBS_ERR_BASE', 0.7)
                blur = err_margin if not god_mode else 0.0
                est_wealth = party.wealth * (1 + rng.uniform(-blur, blur))
                st.markdown(f"### 💰 **{t('Party Wealth')}:** `${est_wealth:.1f}` *({t('Est.')})*")

            if is_election_year or god_mode: 
                disp_sup = f"{party.support:.1f}% 🏆(Won!)" if is_winner else f"{party.support:.1f}% 💀(Lost)"
            else:
                if party.latest_poll is not None:
                    best_type = None
                    for pt in ['Large', 'Medium', 'Small']:
                        if len(party.poll_history[pt]) > 0: best_type = pt; break
                    if best_type:
                        avg = sum(party.poll_history[best_type]) / len(party.poll_history[best_type])
                        count = len(party.poll_history[best_type])
                        disp_sup = f"{party.latest_poll:.1f}% (Latest) ({count}x {best_type} Avg: {avg:.1f}%)"
                    else: disp_sup = f"{party.latest_poll:.1f}% (Latest)"
                else:
                    disp_sup = "??? (Requires Poll)"
            
            st.markdown(f"### 📊 Support: **{disp_sup}**")
            
            if party.name == view_party.name and not is_election_year:
                b1, b2, b3 = st.columns(3)
                if b1.button(t("Small Poll ($5)"), key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5); st.rerun()
                if b2.button(t("Med Poll ($10)"), key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10); st.rerun()
                if b3.button(t("Big Poll ($20)"), key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20); st.rerun()

def get_observed_abilities(viewer, target, game, cfg):
    if viewer.name == target.name or st.session_state.get('god_mode'):
        return {
            'predict': target.predict_ability,
            'investigate': target.investigate_ability,
            'media': target.media_ability,
            'stealth': target.stealth_ability,
            'build': target.build_ability,
            'edu': getattr(target, 'edu_ability', cfg.get('EDU_ABILITY_DEFAULT', 3.0))
        }
    
    opp_stl = target.stealth_ability / 10.0
    i_acc_weight = cfg.get('INVESTIGATE_ACCURACY_WEIGHT', 0.8)
    my_inv = (viewer.investigate_ability / 10.0) * i_acc_weight
    
    err_margin = max(0.0, 1.0 + opp_stl - my_inv) * cfg.get('OBS_ERR_BASE', 0.7)
    
    rng = random.Random(f"intel_{target.name}_{game.year}")
    def get_obs(v):
        if err_margin == 0.0: return v
        true_cost = (2**v - 1) * 50
        obs_cost = max(0.0, true_cost * (1 + rng.uniform(-err_margin, err_margin)))
        return math.log2(obs_cost / 50.0 + 1)
        
    return {
        'predict': get_obs(target.predict_ability),
        'investigate': get_obs(target.investigate_ability),
        'media': get_obs(target.media_ability),
        'stealth': get_obs(target.stealth_ability),
        'build': get_obs(target.build_ability),
        'edu': get_obs(getattr(target, 'edu_ability', cfg.get('EDU_ABILITY_DEFAULT', 3.0)))
    }

def render_sidebar_intel_audit(game, view_party, cfg):
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    st.markdown("---")
    st.title(t("🕵️ Intelligence - Opponent Stats"))
    
    opp_stl = opp.stealth_ability / 10.0
    i_acc_weight = cfg.get('INVESTIGATE_ACCURACY_WEIGHT', 0.8)
    my_inv = (view_party.investigate_ability / 10.0) * i_acc_weight
    
    err_margin = max(0.0, 1.0 + opp_stl - my_inv) * cfg.get('OBS_ERR_BASE', 0.7)
    acc = max(0, min(100, int((1.0 - err_margin) * 100)))
    
    st.progress(acc / 100.0, text=f"{t('Observation Accuracy')}: {acc}%")
    
    obs_abis = get_observed_abilities(view_party, opp, game, cfg)
    
    st.write(f"{t('Think Tank')}: {obs_abis['predict']*10:.1f}% | {t('Intelligence')}: {obs_abis['investigate']*10:.1f}%")
    st.write(f"{t('Media Dept')}: {obs_abis['media']*10:.1f}% | {t('Counter-Intel')}: {obs_abis['stealth']*10:.1f}%")
    st.write(f"{t('Engineering')}: {obs_abis['build']*10:.1f}% | {t('Edu Dept')}: {obs_abis['edu']*10:.1f}%")
    
    est_unit_cost = formulas.calc_unit_cost(cfg, game.gdp, obs_abis['build'], view_party.current_forecast)
    eval_txt = config.get_intel_market_eval(est_unit_cost)
    
    inflation_rate = max(0.0, (game.gdp - cfg.get('CURRENT_GDP', 5000.0)) / cfg.get('GDP_INFLATION_DIVISOR', 10000.0)) * 100.0
    
    st.write(f"**{t('Construction Valuation')}**: {eval_txt}")
    st.write(f"*(Est. Unit Output Cost: `{est_unit_cost:.2f}` )*")

    st.markdown("---")
    st.title(t("🧾 Audit - Internal Dept."))
    st.write(f"**Current Inflation Index:** `{inflation_rate:.1f}%`")
    total_maint = (view_party.predict_ability + view_party.investigate_ability + view_party.media_ability + view_party.stealth_ability + view_party.build_ability + view_party.edu_ability) * 1.5
    
    st.write(f"{t('Think Tank')}: {view_party.predict_ability*10:.0f} | {t('Intelligence')}: {view_party.investigate_ability*10:.0f}")
    st.write(f"{t('Media Dept')}: {view_party.media_ability*10:.0f} | {t('Counter-Intel')}: {view_party.stealth_ability*10:.0f}")
    st.write(f"{t('Engineering')}: {view_party.build_ability*10:.0f} | {t('Edu Dept')}: {view_party.edu_ability*10:.0f}")
    st.write(f"**(Next Year's Maint. Est. EV: -{total_maint:.1f} EV)**")

