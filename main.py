# ==========================================
# main.py
# 主程式：負責狀態轉移、UI 拼裝與即時數值分發
# ==========================================
import streamlit as st
import random
import content
import formulas
import interface

st.set_page_config(page_title="Symbiocracy 共生民主模擬器 v3.0.0", layout="wide")
st.components.v1.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)

if 'cfg' not in st.session_state: st.session_state.cfg = content.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = formulas.GameEngine(cfg)
    st.session_state.turn_data = {
        'r_value': 1.0, 'target_h_fund': 600.0, 'target_gdp_growth': 0.0,
        'r_pays': 0, 'total_funds': 0, 'agreed': False, 'target_gdp': 5000.0, 'h_ratio': 1.0
    }

game = st.session_state.game

if game.year > cfg['END_YEAR']:
    interface.render_endgame_charts(game.history, cfg)
    if st.button("🔄 重新開始全新遊戲", use_container_width=True): st.session_state.clear(); st.rerun()
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = cfg['PREDICT_DIFF'] / max(0.1, p.predict_ability)
        p.current_forecast = max(0.0, round(game.current_real_decay + random.uniform(-error_margin, error_margin), 2))
    
    if not hasattr(game, 'p1_step'):
        game.p1_step = 'draft_r'
        game.p1_proposals = {'R': None, 'H': None}
        game.p1_selected_plan = None

    for k in list(st.session_state.keys()):
        if k.startswith('ui_decay_') or k.endswith('_acts'): del st.session_state[k]
    
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

with st.sidebar:
    interface.render_global_settings(cfg, game)
    god_mode = st.toggle("👁️ 上帝視角", False)
    if st.button("🔄 重新開始遊戲", use_container_width=True): st.session_state.clear(); st.rerun()
    
    st.markdown("---")
    elec_status = "🗳️ 【大選年】" if is_election_year else f"⏳ 距大選 {cfg['ELECTION_CYCLE'] - (game.year % cfg['ELECTION_CYCLE'])} 年"
    st.write(f"**年份:** {game.year} / {cfg['END_YEAR']} ({elec_status})")
    if god_mode: st.error(f"👁️ **上帝視角：**\n真實衰退率為 **{game.current_real_decay:.2f}**")

st.title("🏛️ Symbiocracy 共生民主模擬器 v3.0.0")

if game.year == 1: st.info("🗞️ 歡迎來到共生內閣的第一年！請雙方展開預算與目標協商。")
else: interface.render_yearly_review_banner(game)

acc_percent = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
interface.render_think_tank_toast(view_party, acc_percent, view_party.current_forecast)

if st.session_state.get('news_flash'): 
    st.info(st.session_state.news_flash); st.session_state.news_flash = None 

interface.render_party_cards(game, view_party, god_mode, is_election_year, cfg)
interface.render_status_bar(game, view_party, cfg)

rt_req_funds=0; rt_h_ratio=1.0; rt_r_pays=0; rt_h_pays=0; rt_r_val=1.0; rt_t_h=600; rt_t_gdp=5000; rt_net_inc=0; rt_opp_inc=0; rt_my_sup=0; rt_opp_sup=0

if game.phase == 1:
    st.subheader(f"🤝 Phase 1: 目標與預算協商 (輪數: {game.proposal_count})")
    
    if view_party.name == game.ruling_party.name and game.p1_step != 'ultimatum':
        c1, c2 = st.columns(2)
        if c1.button("🚨 1. 下達最後通牒", use_container_width=True, type="primary"):
            if game.p1_selected_plan: game.p1_step = 'ultimatum'; game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()
            else: st.error("⚠️ 需先完成一次表決！")
        if c2.button("⚡ 2. 強行通過調節者方案並換位", use_container_width=True, type="primary"):
            if game.p1_proposals.get('R'):
                st.session_state.turn_data.update(game.p1_proposals['R'])
                penalty = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
                game.party_A.wealth -= penalty; game.party_B.wealth -= penalty
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.swap_triggered_this_year = True
                game.emotion = min(100.0, game.emotion + 20.0)
                st.session_state.news_flash = f"🗞️ **【快訊】執政黨強行闖關！** 執政黨強行通過草案並啟動倒閣！\n💸 雙方遭社會唾棄，被罰捐 {penalty} 資金！"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            else: st.error("⚠️ 調節者尚未提案！")

    if game.p1_step in ['draft_r', 'draft_h']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H'
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手擬定草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({'調節者' if active_role == 'R' else '執行者'}黨) 草案擬定室")
            col_l, col_r = st.columns(2)
            with col_l:
                opp_role = 'H' if active_role == 'R' else 'R'
                opp_plan = game.p1_proposals.get(opp_role)
                opp_claimed = opp_plan['claimed_decay'] if opp_plan else None
                
                my_plan = game.p1_proposals.get(active_role)
                my_last_claimed = my_plan['claimed_decay'] if my_plan else view_party.current_forecast
                
                c_decay, c_gdp = st.columns(2)
                input_key = f"ui_decay_val_{game.year}_{active_role}"
                if input_key not in st.session_state: st.session_state[input_key] = float(my_last_claimed)
                
                with c_decay:
                    opp_txt = f" (對手: {opp_claimed:.2f})" if opp_claimed is not None else " (等待對手)"
                    st.markdown(f"**公告衰退值**{opp_txt} *(當前: {my_last_claimed:.2f})*")
                    claimed_decay = st.number_input("公告衰退值", value=float(st.session_state[input_key]), step=0.01, key=f"num_{input_key}", label_visibility="collapsed")
                    
                    if opp_claimed is not None:
                        b1, b2, b3 = st.columns(3)
                        b1.button("平均", on_click=lambda: st.session_state.update({input_key: round((my_last_claimed + opp_claimed)/2, 2)}))
                        b2.button("偏我", on_click=lambda: st.session_state.update({input_key: round(my_last_claimed*0.75 + opp_claimed*0.25, 2)}))
                        b3.button("偏他", on_click=lambda: st.session_state.update({input_key: round(my_last_claimed*0.25 + opp_claimed*0.75, 2)}))
                    st.session_state[input_key] = claimed_decay
                    
                with c_gdp:
                    st.markdown("**目標 GDP 成長率 (%)**")
                    t_gdp_growth = st.number_input("GDP成長", value=0.0, step=0.5, label_visibility="collapsed")

                max_h = max(10.0, float(game.total_budget))
                t_h_fund = st.slider("目標執行獎勵基金 (外包業務量)", 0.0, max_h, float(min(game.h_fund, max_h)), 10.0)
                r_val = st.slider("績效達成嚴格度 (平方級影響)", 0.5, 3.0, 1.0, 0.1)
                
                t_gdp = game.gdp * (1 + (t_gdp_growth / 100.0))
                req_funds, h_ratio = formulas.calculate_required_funds(cfg, t_h_fund, t_gdp, game.h_fund, game.gdp, r_val, claimed_decay, game.h_role_party.build_ability)
                
                safe_req = max(1, int(req_funds))
                r_pays = st.slider(f"💰 調節者出資金額 (總需 {req_funds})", 0, safe_req, int(safe_req * 0.5))
                h_pays = req_funds - r_pays
                
                o_gdp_pct, o_h_g, o_h_n, o_r_g, o_r_n, o_h_sup, o_r_sup, o_est_gdp, o_est_h_fund, o_h_roi, o_r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, view_party.current_forecast, game.h_role_party.build_ability, r_pays, h_pays)
                c_gdp_pct, c_h_g, c_h_n, c_r_g, c_r_n, c_h_sup, c_r_sup, c_est_gdp, c_est_h_fund, c_h_roi, c_r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, claimed_decay, game.h_role_party.build_ability, r_pays, h_pays)

                rt_req_funds=req_funds; rt_h_ratio=h_ratio; rt_r_pays=r_pays; rt_h_pays=h_pays; rt_r_val=r_val; rt_t_h=t_h_fund; rt_t_gdp=t_gdp
                my_is_h = (active_role == 'H')
                rt_net_inc, rt_my_sup = (o_h_n, o_h_sup) if my_is_h else (o_r_n, o_r_sup)
                rt_opp_inc, rt_opp_sup = (o_r_n, o_r_sup) if my_is_h else (o_h_n, o_h_sup)

                if st.button("📤 送出草案", use_container_width=True, type="primary"):
                    game.p1_proposals[active_role] = {
                        'r_value': r_val, 'target_h_fund': t_h_fund, 'target_gdp_growth': t_gdp_growth, 
                        'target_gdp': t_gdp, 'r_pays': r_pays, 'claimed_decay': claimed_decay,
                        'total_funds': req_funds, 'h_pays': h_pays, 'h_ratio': h_ratio, 'author': active_role,
                        'h_roi': c_h_roi, 'r_roi': c_r_roi
                    }
                    if game.p1_step == 'draft_r': game.p1_step = 'draft_h'; game.proposing_party = game.h_role_party
                    else: game.p1_step = 'voting_pick'; game.proposing_party = game.ruling_party
                    st.rerun()

            with col_r:
                def draw_preview(title, decay, gdp_pct, h_n, r_n, h_sup, r_sup, est_gdp, h_roi, r_roi):
                    my_net, my_sup, my_roi = (h_n, h_sup, h_roi) if my_is_h else (r_n, r_sup, r_roi)
                    opp_net, opp_sup, opp_roi = (r_n, r_sup, r_roi) if my_is_h else (h_n, h_sup, h_roi)
                    st.markdown(f"**{title}** *(衰退估算: -{decay:.2f})*")
                    st.success(f"🟢 **我方預期收益:** `{my_net:.0f}` (ROI: {my_roi:.1f}%) | **支持度變化:** `{my_sup:+.2f}%`")
                    st.error(f"🔴 **對手預期收益:** `{opp_net:.0f}` (ROI: {opp_roi:.1f}%) | **支持度變化:** `{opp_sup:+.2f}%`")
                    st.info(f"📈 **預期 GDP:** `{game.gdp:.0f} ➔ {est_gdp:.0f}` ({gdp_pct:+.2f}%)")
                    st.markdown("---")

                st.markdown("#### 📊 方案雙盲視角推演")
                draw_preview("🛡️ 依據自己智庫估算", view_party.current_forecast, o_gdp_pct, o_h_n, o_r_n, o_h_sup, o_r_sup, o_est_gdp, o_h_roi, o_r_roi)
                draw_preview("📢 依據方案公告估算", claimed_decay, c_gdp_pct, c_h_n, c_r_n, c_h_sup, c_r_sup, c_est_gdp, c_h_roi, c_r_roi)

    elif game.p1_step == 'voting_pick':
        st.markdown(f"### 🗳️ 執政黨定奪 ({game.ruling_party.name})")
        if view_party.name != game.ruling_party.name:
            st.warning("⏳ 等待執政黨定奪...")
        else:
            cols = st.columns(2)
            for idx, key in enumerate(['R', 'H']):
                plan = game.p1_proposals.get(key)
                with cols[idx]:
                    if plan is None: st.info("等待對方發布草案..."); continue
                    interface.render_proposal_component('⚖️ 調節者草案' if key=='R' else '🛡️ 執行者草案', plan, game, view_party, cfg)
                    if st.button(f"✅ 選擇此方案", key=f"pick_{key}", use_container_width=True):
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            interface.render_proposal_component('📜 待覆議草案內容', game.p1_selected_plan, game, view_party, cfg)
            c1, c2 = st.columns(2)
            if c1.button("✅ 同意法案", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **【快訊】預算案三讀通過！** 歷經 {game.proposal_count} 輪黨團協商，雙方正式簽署法案。"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button("❌ 拒絕並重談", use_container_width=True):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()

    elif game.p1_step == 'ultimatum':
        st.markdown("### 🚨 最後通牒 (Ultimatum)")
        opp_ruling = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A
        if view_party.name != opp_ruling.name: st.warning(f"⏳ 等待 {opp_ruling.name} 回應...")
        else:
            interface.render_proposal_component('📜 通牒底線方案', game.p1_selected_plan, game, view_party, cfg)
            c1, c2 = st.columns(2)
            if c1.button("✅ 忍辱負重 (接受通牒)", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **【快訊】通牒生效！** 歷經 {game.proposal_count} 輪談判，在野黨妥協吞下底線方案。"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button("💥 寧死不屈 (倒閣換位)", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                penalty = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
                game.party_A.wealth -= penalty; game.party_B.wealth -= penalty
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.swap_triggered_this_year = True
                game.emotion = min(100.0, game.emotion + 30.0) 
                st.session_state.news_flash = f"🗞️ **【快訊】政局動盪！** 通牒破局觸發倒閣，雙方各遭重罰 {penalty} 資金！"
                game.phase = 2; game.proposing_party = game.r_role_party; st.rerun()

elif game.phase == 2:
    st.subheader(f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name}")
    d = st.session_state.turn_data
    is_h = (view_party.name == game.h_role_party.name)
    req_pay = d.get('h_pays', 0) if is_h else d.get('r_pays', 0)
    current_wealth = int(view_party.wealth)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📣 政策與媒體")
        st.info(f"📜 **法定專案款 (不可動用):** `${req_pay}`")
        if is_h: st.caption("💡 **執行者特性**: 媒體操控值 1.2 倍加成")
        else: st.caption("💡 **調節者特性**: 調查能力值 1.2 倍加成")
        
        media_ctrl = st.number_input("媒體操控 (搶功勞/推卸責任)", 0, current_wealth, 100)
        incite_emo = st.number_input("煽動情緒 (短期降理智)", 0, current_wealth, 0)
        edu_up = st.number_input("推行教育 (提升理智)", 0, current_wealth, 0) if not is_h else 0
        edu_down = st.number_input("推行降智 (降低理智)", 0, current_wealth, 0) if not is_h else 0
        
        if is_h:
            h_corr_pct = st.slider("秘密貪污 (%)", 0, 100, 0)
            c_amt, c_prob, s_safe, s_caught, sup_safe, sup_caught = formulas.calculate_corruption_preview(cfg, game, d, h_corr_pct, 0, media_ctrl)
            st.caption(f"↳ 預計落袋: `${c_amt:.0f}` | 遭逮機率(依智庫): `{c_prob*100:.1f}%`")
            if c_amt > 0:
                expected_gain = c_amt * (1 - c_prob) - (c_amt * cfg['CORRUPTION_PENALTY']) * c_prob
                st.write(f"📊 **貪污預期淨利**: `${expected_gain:.0f}` | 遭逮民調懲罰: `-5.0%`")
        else: h_corr_pct = 0
        
    with c2:
        st.markdown("#### 🔒 內部升級與維護")
        priv_inv = interface.ability_slider("🔍 調查能力", f"up_inv_{view_party.name}", view_party.investigate_ability, current_wealth, cfg)
        priv_pre = interface.ability_slider("🕵️ 預測能力", f"up_pre_{view_party.name}", view_party.predict_ability, current_wealth, cfg)
        priv_media = interface.ability_slider("📺 媒體操控力", f"up_med_{view_party.name}", view_party.media_ability, current_wealth, cfg)
        priv_edu = interface.ability_slider("🎓 教育能力", f"up_edu_{view_party.name}", view_party.edu_ability, current_wealth, cfg)
        h_build_up = interface.ability_slider("🏗️ 建設能力", f"up_bld_{view_party.name}", view_party.build_ability, current_wealth, cfg) if is_h else 0

    tot = req_pay + media_ctrl + incite_emo + edu_up + edu_down + priv_inv + priv_pre + priv_media + priv_edu + h_build_up
    st.write(f"**總花費:** `{tot}` / `{current_wealth}`")
    
    if tot <= current_wealth and st.button("確認行動/結算", use_container_width=True, type="primary"):
        st.session_state[f"{view_party.name}_acts"] = {
            'media': media_ctrl, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct,
            'p_inv': priv_inv, 'p_pre': priv_pre, 'p_media': priv_media, 'p_edu': priv_edu, 'p_bld': h_build_up
        }
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            rp, hp = game.r_role_party, game.h_role_party
            ra, ha = st.session_state[f"{rp.name}_acts"], st.session_state[f"{hp.name}_acts"]
            
            confiscated = 0.0; caught = False; fine = 0.0
            corr_amt = d.get('total_funds', 0) * (ha['corr'] / 100.0)
            act_build = d.get('total_funds', 0) - corr_amt
            
            if ha['corr'] > 0:
                eff_inv = rp.investigate_ability * cfg['R_INV_BONUS']
                catch_prob = min(1.0, (eff_inv / cfg['MAX_ABILITY']) * (corr_amt / max(1.0, hp.wealth)) * 10.0)
                if random.random() < catch_prob:
                    caught = True; fine = corr_amt * cfg['CORRUPTION_PENALTY']; confiscated = corr_amt; corr_amt = 0 
            
            h_bst = (act_build * d.get('h_ratio', 1.0) * hp.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
            new_h_fund = max(0.0, game.h_fund + h_bst - (game.current_real_decay * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
            
            gdp_bst = (act_build * hp.build_ability) / cfg['BUILD_DIFF']
            new_gdp = max(0.0, game.gdp + gdp_bst - (game.current_real_decay * 1000))
            budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
            h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
            
            hp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == hp.name else 0) + (budg * h_shr) - d.get('h_pays',0) + corr_amt - fine
            rp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == rp.name else 0) + (budg * (1 - h_shr)) - d.get('r_pays',0)
            
            shift = formulas.calc_support_shift(cfg, hp, rp, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha['media'], ra['media'])
            if caught: shift['actual_shift'] -= 5.0
            hp_sup_new = max(0.0, min(100.0, hp.support + shift['actual_shift']))
            
            gdp_grw_bonus = ((new_gdp - game.gdp)/max(1.0, game.gdp)) * 100.0
            emotion_decay = game.sanity * 20.0
            emotion_delta = (ha['incite'] + ra['incite']) * 0.1 - gdp_grw_bonus - emotion_decay
            game.emotion = max(0.0, min(100.0, game.emotion + emotion_delta))
            
            edu_t, red_t = ra['edu_up'] + ha['edu_up'], ra['edu_down'] + ha['edu_down']
            game.sanity = max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + (edu_t * 0.005) - (red_t * 0.005)))
            
            game.last_year_report = {
                'old_gdp': game.gdp, 'target_gdp': d.get('target_gdp'), 'target_gdp_growth': d.get('target_gdp_growth'),
                'target_h_fund': d.get('target_h_fund'), 'h_party_name': hp.name, 'h_perf': shift['h_perf'], 'r_perf': shift['r_perf'],
                'h_blame_saved_pct': shift['h_blame_saved_pct'], 'r_blame_saved_pct': shift['r_blame_saved_pct'], 'real_decay': game.current_real_decay,
                'view_party_forecast': view_party.current_forecast, 'caught_corruption': caught
            }

            hp.support, rp.support = hp_sup_new, 100.0 - hp_sup_new
            
            if game.year % cfg['ELECTION_CYCLE'] == 1:
                if hp.support > rp.support: game.ruling_party = hp
                elif rp.support > hp.support: game.ruling_party = rp

            game.h_fund, game.gdp = new_h_fund, new_gdp
            game.total_budget = budg + confiscated
            hp.wealth += hp_inc; rp.wealth += rp_inc

            rp.investigate_ability, _ = formulas.get_ability_preview(rp.investigate_ability, ra['p_inv'], cfg)
            rp.predict_ability, _ = formulas.get_ability_preview(rp.predict_ability, ra['p_pre'], cfg)
            rp.media_ability, _ = formulas.get_ability_preview(rp.media_ability, ra['p_media'], cfg)
            rp.edu_ability, _ = formulas.get_ability_preview(rp.edu_ability, ra['p_edu'], cfg)
            
            hp.investigate_ability, _ = formulas.get_ability_preview(hp.investigate_ability, ha['p_inv'], cfg)
            hp.predict_ability, _ = formulas.get_ability_preview(hp.predict_ability, ha['p_pre'], cfg)
            hp.media_ability, _ = formulas.get_ability_preview(hp.media_ability, ha['p_media'], cfg)
            hp.edu_ability, _ = formulas.get_ability_preview(hp.edu_ability, ha['p_edu'], cfg)
            hp.build_ability, _ = formulas.get_ability_preview(hp.build_ability, ha['p_bld'], cfg)

            game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
            
            game.year += 1; game.phase = 1; game.p1_step = 'draft_r'
            game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
            game.poll_done_this_year = False
            game.proposing_party = game.r_role_party
            for k in list(st.session_state.keys()):
                if k.startswith('ui_decay_') or k.endswith('_acts'): del st.session_state[k]
            del st.session_state.turn_initialized; st.rerun()

if game.phase == 1 and game.p1_step in ['draft_r', 'draft_h'] and view_party.name == (game.r_role_party.name if game.p1_step == 'draft_r' else game.h_role_party.name):
    interface.render_real_time_formulas(rt_req_funds, rt_h_ratio, rt_r_pays, rt_h_pays, rt_r_val, rt_t_h, rt_t_gdp, game.h_fund, game.gdp, rt_net_inc, rt_opp_inc, rt_my_sup, rt_opp_sup, (game.p1_step == 'draft_h'))
