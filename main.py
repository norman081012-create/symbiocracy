# ==========================================
# main.py
# 主程式：負責狀態轉移、UI 拼裝與即時數值分發
# ==========================================
import streamlit as st
import random

st.set_page_config(page_title="Symbiocracy Simulator v2.9.5", layout="wide")

import content
import formulas
import interface

if 'cfg' not in st.session_state: st.session_state.cfg = content.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = formulas.GameEngine(cfg)
    st.session_state.turn_data = {
        'r_value': 1.0, 'target_h_fund': 600.0, 'target_gdp_growth': 0.0,
        'r_pays': 0, 'total_funds': 0, 'agreed': False, 'target_gdp': 5000.0, 'h_ratio': 1.0
    }
    st.session_state.news_flash = "🗞️ **首長就職：** 歡迎來到共生內閣的第一年！"

game = st.session_state.game

if game.year > cfg['END_YEAR']:
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = cfg['PREDICT_DIFF'] / max(0.1, p.predict_ability)
        forecast = game.current_real_decay + random.uniform(-error_margin, error_margin)
        p.current_forecast = max(0.0, round(forecast, 2))
    game.proposal_count = 0
    game.p1_state = 'drafting'
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A
is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)

with st.sidebar:
    interface.render_global_settings(cfg)
    god_mode = st.toggle("👁️ 上帝視角", False)
    if st.button("🔄 重新開始遊戲", use_container_width=True): st.session_state.clear(); st.rerun()

st.title("🏛️ Symbiocracy 共生民主模擬器 v2.9.5")

# 置頂智庫提示
acc_percent = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
interface.render_think_tank_toast(view_party, acc_percent, view_party.current_forecast)

if st.session_state.news_flash: 
    st.info(st.session_state.news_flash); st.session_state.news_flash = None 

interface.render_party_cards(game, view_party, god_mode, is_election_year, cfg)
interface.render_status_bar(game, cfg)

rt_req_funds=0; rt_h_ratio=1.0; rt_r_pays=0; rt_h_pays=0; rt_r_val=1.0; rt_t_h=600; rt_t_gdp=5000; rt_net_inc=0; rt_opp_inc=0; rt_my_sup=0; rt_opp_sup=0

def handle_trust_breakdown():
    game.party_A.wealth -= 100.0; game.party_B.wealth -= 100.0
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True
    st.session_state.news_flash = "🚨 **談判破裂！** 觸發換位，雙方各扣 100 資金！"
    game.phase = 2

if not hasattr(game, 'p1_proposals'):
    game.p1_proposals = {'R': None, 'H': None, 'Neutral': None}
    game.p1_selected_plan = None; game.p1_step = 'draft_r' 

if game.phase == 1:
    st.subheader(f"🤝 Phase 1: 目標與預算協商 (輪數: {game.proposal_count})")
    
    if view_party.name == game.ruling_party.name and game.p1_step != 'ultimatum':
        c1, c2 = st.columns(2)
        if c1.button("🚨 1. 下達最後通牒", use_container_width=True, type="primary"):
            if game.p1_selected_plan: game.p1_step = 'ultimatum'; game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()
        if c2.button("⚡ 2. 強行通過調節者方案並換位", use_container_width=True, type="primary"):
            if game.p1_proposals.get('R'):
                st.session_state.turn_data.update(game.p1_proposals['R'])
                game.party_A.wealth -= 50; game.party_B.wealth -= 50
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()

    if game.p1_step in ['draft_r', 'draft_h']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H'
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手擬定草案...")
        else:
            col_l, col_r = st.columns(2)
            with col_l:
                strategy = st.radio("🤖 策略", ["自訂", "🤝 友善", "⚖️ 公平", "🔥 極限"], horizontal=True)
                r_ratio = 0.5; def_r = 1.0
                if strategy == "🤝 友善": r_ratio = 0.7 if active_role == 'R' else 0.3; def_r = 0.8 if active_role == 'R' else 1.2
                elif strategy == "🔥 極限": r_ratio = 0.3 if active_role == 'R' else 0.7; def_r = 1.8 if active_role == 'R' else 0.5
                
                claimed_decay = st.number_input("公告預估衰退值 (高估可索更多預算)", value=float(view_party.current_forecast), step=0.05)
                t_h_fund = st.slider("目標執行獎勵基金 (外包業務量)", 0.0, 5000.0, float(game.h_fund), 10.0)
                t_gdp_growth = st.slider("目標 GDP 成長率 (%)", -5.0, 15.0, 0.0, 0.5)
                r_val = st.slider("績效達成嚴格度 (平方級影響)", 0.5, 3.0, float(def_r), 0.1)
                
                t_gdp = game.gdp * (1 + (t_gdp_growth / 100.0))
                req_funds, h_ratio = formulas.calculate_required_funds(cfg, t_h_fund, t_gdp, game.h_fund, game.gdp, r_val, claimed_decay, game.h_role_party.build_ability)
                r_pays = int(req_funds * r_ratio); h_pays = req_funds - r_pays
                st.success(f"**必需總資金:** `{req_funds}` (調節者出 `{r_pays}` / 執行者出 `{h_pays}`)")

            with col_r:
                gdp_pct, h_g, h_n, r_g, r_n, h_sup, r_sup, est_gdp, est_h_fund, h_roi, r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, claimed_decay, game.h_role_party.build_ability, r_pays, h_pays)
                my_is_h = (active_role == 'H')
                my_net, my_sup, my_roi = (h_n, h_sup, h_roi) if my_is_h else (r_n, r_sup, r_roi)
                opp_net, opp_sup, opp_roi = (r_n, r_sup, r_roi) if my_is_h else (h_n, h_sup, h_roi)
                
                # 更新 RT 變數供除錯
                rt_req_funds=req_funds; rt_h_ratio=h_ratio; rt_r_pays=r_pays; rt_h_pays=h_pays; rt_r_val=r_val; rt_t_h=t_h_fund; rt_t_gdp=t_gdp
                rt_net_inc=my_net; rt_opp_inc=opp_net; rt_my_sup=my_sup; rt_opp_sup=opp_sup

                st.success(f"🟢 **公告收益:** `{my_net:.0f}` (ROI: {my_roi:.1f}%) | **預期民調:** `{my_sup:+.2f}%`")
                st.error(f"🔴 **對手收益:** `{opp_net:.0f}` (ROI: {opp_roi:.1f}%) | **預期民調:** `{opp_sup:+.2f}%`")

                if st.button("📤 送出草案", use_container_width=True):
                    game.p1_proposals[active_role] = {
                        'r_value': r_val, 'target_h_fund': t_h_fund, 'target_gdp_growth': t_gdp_growth, 
                        'target_gdp': t_gdp, 'r_pays': r_pays, 'claimed_decay': claimed_decay,
                        'total_funds': req_funds, 'h_pays': h_pays, 'h_ratio': h_ratio, 'author': active_role,
                        'h_roi': h_roi, 'r_roi': r_roi
                    }
                    if game.p1_step == 'draft_r': game.p1_step = 'draft_h'; game.proposing_party = game.h_role_party
                    else: game.p1_step = 'voting_pick'; game.proposing_party = game.ruling_party
                    st.rerun()

    elif game.p1_step == 'voting_pick':
        st.markdown(f"### 🗳️ 執政黨定奪 ({game.ruling_party.name})")
        cols = st.columns(2)
        for idx, key in enumerate(['R', 'H']):
            plan = game.p1_proposals[key]
            with cols[idx]:
                st.markdown(f"#### {'⚖️ 調節者草案' if key=='R' else '🛡️ 執行者草案'}")
                st.write(f"**調節者 ROI:** `{plan['r_roi']:.1f}%` | **執行者 ROI:** `{plan['h_roi']:.1f}%`")
                if view_party.name == game.ruling_party.name:
                    if st.button(f"✅ 選擇此方案", key=f"pick_{key}", use_container_width=True):
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            c1, c2 = st.columns(2)
            if c1.button("✅ 同意法案", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button("❌ 拒絕並重談", use_container_width=True):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()

elif game.phase == 2:
    d = st.session_state.turn_data
    is_h = (view_party.name == game.h_role_party.name)
    req_pay = d.get('h_pays', 0) if is_h else d.get('r_pays', 0)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📣 政策與媒體")
        media_ctrl = st.number_input("媒體操控 (搶功勞/推卸責任)", 0, int(view_party.wealth), 100)
        incite_emo = st.number_input("煽動情緒 (暫時降低社會理智)", 0, int(view_party.wealth), 0)
        h_corr = st.slider("秘密貪污 (%)", 0, 100, 0) if is_h else 0
        edu = st.number_input("推行教育 (提升理智)", 0, int(view_party.wealth), 0)
        
    with c2:
        st.markdown("#### 🔒 內部升級")
        priv_inv = st.slider("提升調查", 0, int(view_party.wealth), 0)
        priv_pre = st.slider("提升智庫", 0, int(view_party.wealth), 0)
        priv_media = st.slider("提升媒體操控力", 0, int(view_party.wealth), 0)
        h_build_up = st.slider("提升建設能力", 0, int(view_party.wealth), 0) if is_h else 0

    tot = req_pay + media_ctrl + incite_emo + edu + priv_inv + priv_pre + priv_media + h_build_up
    st.write(f"**總花費:** `{tot}` / `{int(view_party.wealth)}`")
    
    if tot <= view_party.wealth and st.button("確認行動/結算", use_container_width=True):
        st.session_state[f"{view_party.name}_acts"] = {
            'media': media_ctrl, 'incite': incite_emo, 'edu': edu, 'corr': h_corr,
            'p_inv': priv_inv, 'p_pre': priv_pre, 'p_media': priv_media, 'p_bld': h_build_up
        }
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            rp, hp = game.r_role_party, game.h_role_party
            ra, ha = st.session_state[f"{rp.name}_acts"], st.session_state[f"{hp.name}_acts"]
            
            # 安全獲取 confis，避免 NameError
            confiscated = 0.0; caught = False; fine = 0.0
            corr_amt = d.get('h_pays',0) * (ha['corr'] / 100.0)
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
            
            # 情緒與理智度連動邏輯
            gdp_grw_bonus = ((new_gdp - game.gdp)/game.gdp) * 50 if game.gdp > 0 else 0
            game.emotion = max(0.0, min(100.0, game.emotion + (ha['incite'] + ra['incite']) * 0.1 - gdp_grw_bonus - (game.sanity * 10)))
            game.sanity = max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + (ha['edu'] + ra['edu']) * 0.005))
            
            game.last_year_report = {
                'old_gdp': game.gdp, 'target_gdp': d.get('target_gdp'), 'target_gdp_growth': d.get('target_gdp_growth'),
                'target_h_fund': d.get('target_h_fund'), 'h_party_name': hp.name, 'h_perf': shift['h_perf'], 'r_perf': shift['r_perf'],
                'h_blame_saved': shift['h_blame_saved'], 'r_blame_saved': shift['r_blame_saved'], 'real_decay': game.current_real_decay,
                'view_party_forecast': view_party.current_forecast, 'caught_corruption': caught
            }

            hp.support, rp.support = hp_sup_new, 100.0 - hp_sup_new
            game.h_fund, game.gdp = new_h_fund, new_gdp
            game.total_budget = budg + confiscated
            hp.wealth += hp_inc; rp.wealth += rp_inc

            game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
            game.year += 1; game.phase = 1; game.p1_state = 'drafting'
            st.session_state.pop(f"{rp.name}_acts", None); st.session_state.pop(f"{hp.name}_acts", None)
            del st.session_state.turn_initialized; st.rerun()

if game.phase == 1 and game.p1_step in ['draft_r', 'draft_h'] and view_party.name == (game.r_role_party.name if game.p1_step == 'draft_r' else game.h_role_party.name):
    interface.render_real_time_formulas(rt_req_funds, rt_h_ratio, rt_r_pays, rt_h_pays, rt_r_val, rt_t_h, rt_t_gdp, game.h_fund, game.gdp, rt_net_inc, rt_opp_inc, rt_my_sup, rt_opp_sup, (game.p1_step == 'draft_h'))
