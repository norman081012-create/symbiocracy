# ==========================================
# ui_core.py
# Handles Shared UI Rendering, Charts, Standardized Components
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
        st.markdown(f"**{t('Civic Literacy')}:** `{config.get_civic_index_text(disp_san)}` <span style='color:{c_color}'>*({san_chg:+.1f})*</span>", unsafe_allow_html=True)
        
        emo_chg = disp_emo - rep['old_emo'] if rep else 0
        e_color = "red" if emo_chg > 0 else "green" if emo_chg < 0 else "gray"
        st.markdown(f"**{t('Voter Emotion')}:** `{config.get_emotion_text(disp_emo)}` <span style='color:{e_color}'>*({emo_chg:+.1f})*</span>", unsafe_allow_html=True)
        
        gdp_base = rep['old_gdp'] if rep else game.gdp
        gdp_diff = disp_gdp - gdp_base
        gdp_pct = (gdp_diff / max(1.0, gdp_base)) * 100.0
        g_color = "green" if gdp_diff > 0 else "red" if gdp_diff < 0 else "gray"
        label_gdp = t("Expected GDP") if is_preview else t("Current GDP")
        st.markdown(f"**{label_gdp}:** `{disp_gdp:.1f}` <span style='color:{g_color}'>*({gdp_diff:+.1f}, {gdp_pct:+.2f}%)*</span>", unsafe_allow_html=True)

    with c2:
        st.markdown(t("### 💰 Executive Resources"))
        if game.year == 1 and not is_preview: st.info("Reorganizing for the first year, rewards not yet distributed.")
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
        st.markdown(f"### 🕵️ {t('Think Tank')} {t('Intelligence Forecast')} (Accuracy: {acc}%)")
        
        conv_rate = cfg.get('GDP_CONVERSION_RATE', 0.2)
        gdp_loss = game.gdp * (fc * cfg['DECAY_WEIGHT_MULT'] + cfg['BASE_DECAY_RATE'])
        req_infra_to_balance = gdp_loss / conv_rate
        
        st.write(f"Est. Decay: `{fc:.3f}`")
        eval_scenario = config.get_economic_forecast_text(fc * 100)
        st.info(eval_scenario)
        
        if rep:
            my_is_h = view_party.name == rep['h_party_name']
            past_forecast = rep.get('h_forecast') if my_is_h else rep.get('r_forecast')
            if past_forecast is not None:
                diff = abs(past_forecast - rep['real_decay'])
                eval_txt = config.get_thinktank_eval(view_party.predict_ability, diff)
                st.write(f"({cfg['CALENDAR_NAME']} {game.year-1} Internal Review: **{eval_txt}**)")
        else:
            st.write("(No historical data from last year for review)")

    with c4:
        if game.phase == 1:
            st.markdown(t("### 📊 Financial Report"))
            total_maint = (
                formulas.get_ability_maintenance(view_party.predict_ability, cfg, False, view_party.build_ability) +
                formulas.get_ability_maintenance(view_party.investigate_ability, cfg, False, view_party.build_ability) +
                formulas.get_ability_maintenance(view_party.media_ability, cfg, False, view_party.build_ability) +
                formulas.get_ability_maintenance(view_party.stealth_ability, cfg, False, view_party.build_ability) +
                formulas.get_ability_maintenance(view_party.build_ability, cfg, True, view_party.build_ability)
            )
            if game.year == 1:
                st.write(f"{t('Available Net Assets')}: **{view_party.wealth:.1f}** ({view_party.wealth:.1f} - 0.0)")
            else:
                st.write(f"{t('Available Net Assets')}: **{view_party.wealth:.1f}** ({(view_party.wealth + total_maint):.1f} - {total_maint:.1f})")
                
            if rep:
                my_is_h = view_party.name == rep['h_party_name']
                real_inc = rep['h_inc'] if my_is_h else rep['r_inc']
                est_inc = rep.get('est_h_inc', 0.0) if my_is_h else rep.get('est_r_inc', 0.0)
                st.write(f"{t('Net Profit')}: {t('Real')}:**{real_inc:.1f}** ({t('Last Est.')}:{est_inc:.1f})")
        else:
            if is_preview:
                my_is_h = view_party.name == game.h_role_party.name
                my_net = preview_data['h_inc'] if my_is_h else preview_data['r_inc']
                opp_net = preview_data['r_inc'] if my_is_h else preview_data['h_inc']
                
                st.markdown(t("### 📊 Think Tank Report"))
                st.markdown(f"{t('Our Est Profit')}: **{my_net:.1f}**")
                st.markdown(f"{t('Opp Est Profit')}: **{opp_net:.1f}**")
                
                my_perf = preview_data['my_perf_gdp'] + preview_data['my_perf_proj']
                opp_perf = preview_data['opp_perf_gdp'] + preview_data['opp_perf_proj']
                st.markdown(f"{t('Est Support Points')}: Us **{my_perf:+.1f}** / Opp **{opp_perf:+.1f}**")
                
    st.markdown("---")

def render_message_board(game):
    if st.session_state.get('news_flash'):
        st.warning(st.session_state.news_flash)
        st.session_state.news_flash = None
        
    if game.phase == 1:
        if game.year == 1: st.info("📢 **[Annual Notice]** A new year begins. The country needs rebuilding. Please start budget and target negotiations ASAP.")
        elif game.last_year_report: st.info("📢 **[Annual Notice]** A new year begins. Please start budget and target negotiations ASAP.")
    elif game.phase == 2:
        st.info("📢 **[Annual Notice]** The bill has passed. Please allocate party funds for internal upgrades, campaign rallies, and media operations.")

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
                disp_sup = f"{party.support:.1f}% 🏆(Elected!)" if is_winner else f"{party.support:.1f}% 💀(Defeated)"
            else:
                if party.latest_poll is not None:
                    best_type = None
                    for pt in ['Large', 'Medium', 'Small']:
                        if len(party.poll_history[pt]) > 0: best_type = pt; break
                    if best_type:
                        avg = sum(party.poll_history[best_type]) / len(party.poll_history[best_type])
                        count = len(party.poll_history[best_type])
                        disp_sup = f"{party.latest_poll:.1f}%(Latest Poll) ({count}x{best_type} Avg: {avg:.1f}%)"
                    else: disp_sup = f"{party.latest_poll:.1f}%(Latest Poll)"
                else:
                    disp_sup = "??? (Needs Poll)"
            
            st.markdown(f"### 📊 Support: **{disp_sup}**")
            
            if party.name == view_party.name and not is_election_year:
                b1, b2, b3 = st.columns(3)
                if b1.button(t("Small Poll ($5)"), key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5); st.rerun()
                if b2.button(t("Med Poll ($10)"), key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10); st.rerun()
                if b3.button(t("Big Poll ($20)", "Big Poll ($20)"), key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20); st.rerun()

def get_observed_abilities(viewer, target, game, cfg):
    if viewer.name == target.name or st.session_state.get('god_mode'):
        return {
            'predict': target.predict_ability,
            'investigate': target.investigate_ability,
            'media': target.media_ability,
            'stealth': target.stealth_ability,
            'build': target.build_ability
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
        'build': get_obs(target.build_ability)
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
    
    st.progress(acc / 100.0, text=f"{t('Accuracy')}: {acc}%")
    
    obs_abis = get_observed_abilities(view_party, opp, game, cfg)
    
    st.write(f"{t('Think Tank')}: {obs_abis['predict']*10:.1f}% | {t('Intelligence')}: {obs_abis['investigate']*10:.1f}%")
    st.write(f"{t('Media Dept')}: {obs_abis['media']*10:.1f}% | {t('Counter-Intel')}: {obs_abis['stealth']*10:.1f}%")
    
    # 🚀 Catching corruption ignores observation weight, uses real ability
    my_inv_raw_pct = view_party.investigate_ability / 10.0
    r_bonus = cfg['R_INV_BONUS'] if view_party.name == game.r_role_party.name else 1.0
    obs_stl_pct = obs_abis['stealth'] / 10.0
    
    catch_mult = max(0.1, (my_inv_raw_pct * r_bonus) - obs_stl_pct + 1.0)
    
    def get_catch_prob(c_pct, base_rate):
        rolls = c_pct * catch_mult
        return (1.0 - (1.0 - base_rate)**rolls) * 100.0
        
    catch_10 = get_catch_prob(10.0, cfg['CATCH_RATE_PER_PERCENT'])
    catch_30 = get_catch_prob(30.0, cfg['CATCH_RATE_PER_PERCENT'])
    
    st.write(f"**{t('Anti-Corruption Estimate')}**: Detection Roll Multiplier `{catch_mult:.2f}x`")
    st.caption(f"*(If Opponent corrupts 10% $\\rightarrow$ Catch Rate ~ `{catch_10:.1f}%` | 30% $\\rightarrow$ `{catch_30:.1f}%`)*")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.write(f"{t('Engineering')}: {obs_abis['build']*10:.1f}%")
    
    est_unit_cost = formulas.calc_unit_cost(cfg, game.gdp, obs_abis['build'], view_party.current_forecast)
    eval_txt = config.get_intel_market_eval(est_unit_cost)
    
    inflation_rate = max(0.0, (game.gdp - cfg.get('CURRENT_GDP', 5000.0)) / cfg.get('GDP_INFLATION_DIVISOR', 10000.0)) * 100.0
    
    st.write(f"**{t('Construction Valuation')}**: {eval_txt}")
    st.write(f"*(Est. Unit Cost: `{est_unit_cost:.2f}` / Including Current Inflation `{inflation_rate:.1f}%`)*")

    st.markdown("---")
    st.title(t("🧾 Audit - Internal Dept. Investments"))
    st.write(f"**Current Inflation Index:** `{inflation_rate:.1f}%`")
    total_maint = (
        formulas.get_ability_maintenance(view_party.predict_ability, cfg, False, view_party.build_ability) +
        formulas.get_ability_maintenance(view_party.investigate_ability, cfg, False, view_party.build_ability) +
        formulas.get_ability_maintenance(view_party.media_ability, cfg, False, view_party.build_ability) +
        formulas.get_ability_maintenance(view_party.stealth_ability, cfg, False, view_party.build_ability) +
        formulas.get_ability_maintenance(view_party.build_ability, cfg, True, view_party.build_ability)
    )
    st.write(f"{t('Think Tank')}: {view_party.predict_ability*10:.1f}% | {t('Intelligence')}: {view_party.investigate_ability*10:.1f}%")
    st.write(f"{t('Media Dept')}: {view_party.media_ability*10:.1f}% | {t('Counter-Intel')}: {view_party.stealth_ability*10:.1f}%")
    st.write(f"{t('Engineering')}: {view_party.build_ability*10:.1f}%")
    st.write(f"**(Based on current dept investments, est. maintenance next year: -${total_maint:.1f})**")

def ability_slider(label, key, current_val, wealth, cfg, build_ability=0.0, is_build=False):
    current_pct = current_val * 10.0
    
    # 🚀 Higher Engineering unlocks faster upgrade limits and massive cost reduction
    max_upgrade = cfg.get('MAX_UPGRADE_SPEED', 20.0) * (1.0 + build_ability / 5.0)
    
    min_pct = max(0.0, current_pct - 20.0)
    max_pct = min(100.0, current_pct + max_upgrade)
    
    t_pct = st.slider(f"{label}", float(min_pct), float(max_pct), float(current_pct), 0.1, key=key)
    
    cost_mult = cfg.get('UPGRADE_COST_MULT', 0.15)
    discount = 1.0 + build_ability / 5.0
    
    if t_pct > current_pct: 
        cost = ((t_pct**2 - current_pct**2) * cost_mult) / discount
        st.caption(f"📈 <span style='color:orange'>**{t('Upgrade Investment', 'Upgrade Investment')}**: ${cost:.1f} (Discounted by Engineering)</span>", unsafe_allow_html=True)
    elif t_pct < current_pct: 
        refund = ((current_pct**2 - t_pct**2) * cost_mult * 0.5) 
        cost = -refund
        st.caption(f"📉 <span style='color:blue'>**{t('Downgrade Refund', 'Downgrade Refund')}**: +${abs(cost):.1f}</span>", unsafe_allow_html=True)
    else: 
        cost = 0.0
        st.caption(f"🛡️ {t('Stable', 'Stable')}")
        
    return t_pct / 10.0, cost
