# ==========================================
# main.py
# 主程式：負責狀態轉移與 UI 拼裝
# ==========================================
import streamlit as st
import random

st.set_page_config(page_title="Symbiocracy Simulator v2.9", layout="wide")

import content
import formulas
import interface

# ==========================================
# 1. 遊戲初始化
# ==========================================
if 'cfg' not in st.session_state:
    st.session_state.cfg = content.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = formulas.GameEngine(cfg)
    st.session_state.turn_data = {
        'r_value': 1.0, 'target_h_fund': 600.0, 'target_gdp_growth': 0.0,
        'r_pay_ratio': 50, 'total_funds': 0, 'agreed': False,
        'target_gdp': 5000.0, 'h_ratio': 1.0
    }
    st.session_state.news_flash = "🗞️ **首長就職：** 歡迎來到共生內閣的第一年！請雙方展開預算與目標協商。"

game = st.session_state.game

# 終局判定
if game.year > cfg['END_YEAR']:
    interface.render_endgame_charts(game.history, cfg)
    if st.button("🔄 重新開始全新遊戲", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error_margin = cfg['PREDICT_DIFF'] / max(0.1, p.predict_ability)
        forecast = game.current_real_decay + random.uniform(-error_margin, error_margin)
        p.current_forecast = max(0.0, round(forecast, 2))
    game.proposal_count = 0
    game.p1_state = 'drafting'
    st.session_state.turn_data['agreed'] = False
    st.session_state.turn_initialized = True

view_party = game.proposing_party
opponent_party = game.party_B if view_party.name == game.party_A.name else game.party_A

# ==========================================
# 2. 側邊欄與上帝視角
# ==========================================
with st.sidebar:
    interface.render_global_settings(cfg)
    god_mode = st.toggle("👁️ 上帝視角 (God Mode)", False)
    
    if st.button("🔄 重新開始遊戲", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.markdown("---")
    is_election_year = (game.year % cfg['ELECTION_CYCLE'] == 1)
    elec_status = "🗳️ 【大選年】" if is_election_year else f"⏳ 距大選 {cfg['ELECTION_CYCLE'] - (game.year % cfg['ELECTION_CYCLE'])} 年"
    
    st.write(f"**年份:** {game.year} / {cfg['END_YEAR']} ({elec_status})")
    st.write(f"**執政黨:** {game.ruling_party.name} 👑")
    st.write(f"**目前總預算:** {game.total_budget:.0f}")
    st.write(f"**GDP (總體經濟):** {game.gdp:.1f} | **理智度:** {game.sanity:.2f}")
    
    current_h_ratio = (game.h_fund / game.total_budget) * 100 if game.total_budget > 0 else 50
    st.info(f"**行政獎勵基金:** {game.h_fund:.0f} (H Index 佔比: {current_h_ratio:.1f}%)")

    if god_mode:
        st.error(f"👁️ **上帝視角揭露：**\n\n本期【真實衰退率】為 **{game.current_real_decay:.2f}**")

    st.subheader("🕵️ 智庫報告")
    fc_val = view_party.current_forecast
    acc_percent = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
    forecast_text = content.get_economic_forecast_text(fc_val)
    st.success(f"**[{view_party.name} 視角]**\n\n**經濟前景預估:** {forecast_text}\n*(預估衰退參數: -{fc_val:.2f})*\n\n🎯 報告準確度: **{acc_percent}%**")
    
    if game.year > 1:
        st.markdown("---")
        st.subheader("📊 去年檢討報告")
        rd = game.last_real_decay
        diff = abs(view_party.last_forecast - rd)
        st.write(f"**真實衰退:** `-{rd:.2f}` (我方預估 `-{view_party.last_forecast:.2f}`)")
        if diff <= 0.05: st.info("✅ **智庫神準！**")
        elif diff <= 0.15: st.warning("🟡 **些微誤差**")
        else: st.error("🚨 **嚴重誤判！**")

# ==========================================
# 3. 主畫面狀態列
# ==========================================
st.title("🏛️ Symbiocracy 共生民主模擬器 v2.9")
if st.session_state.news_flash: 
    st.info(st.session_state.news_flash)
    st.session_state.news_flash = None 

col1, col2 = st.columns(2)
for col, party in zip([col1, col2], [game.party_A, game.party_B]):
    with col:
        role = "R Role (監督)" if game.r_role_party == party else "H Role (行政)"
        crown = "👑" if game.ruling_party == party else ""
        acc = min(1.0, view_party.predict_ability / cfg['MAX_ABILITY']) if not god_mode else 1.0
        blur = 1.0 - acc
        
        if is_election_year or god_mode: disp_sup = f"{party.support:.1f}%"
        else:
            if party == view_party: disp_sup = f"估約 {party.current_poll_result:.1f}%" if party.current_poll_result is not None else "??? (需作民調)"
            else: disp_sup = f"估約 {100.0 - view_party.current_poll_result:.1f}%" if view_party.current_poll_result is not None else "??? (需作民調)"

        rng_status = random.Random(f"status_{game.year}_{party.name}_{view_party.name}")
        fog_w = rng_status.uniform(max(0, party.wealth * (1 - blur)), party.wealth * (1 + blur))
        disp_w = f"{party.wealth:.0f}" if (party == view_party or god_mode) else f"估約 {fog_w:.0f}"

        if party == view_party:
            st.success(f"### 👁️ {party.name} {crown}\n**位置:** {role} | **存款:** {disp_w} | **支持度:** {disp_sup}")
        else:
            st.info(f"### {party.name} {crown}\n**位置:** {role} | **存款:** {disp_w} | **支持度:** {disp_sup}")

st.markdown("---")

# ==========================================
# 4. 遊戲流程 (Phase 1 & Phase 2)
# ==========================================
def handle_trust_breakdown():
    penalty_funds = 100.0
    game.party_A.wealth -= penalty_funds
    game.party_B.wealth -= penalty_funds
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True
    st.session_state.news_flash = f"🚨 **談判破裂！** R 黨強行終止協商，觸發憲政危機並強制換位！\n📉 雙方各扣除 {penalty_funds:.0f} 資金！"
    game.phase = 2

if not hasattr(game, 'p1_proposals'):
    game.p1_proposals = {'R': None, 'H': None, 'Neutral': None}
    game.p1_selected_plan = None
    game.p1_step = 'draft_r' 

if game.phase == 1:
    st.subheader(f"🤝 Phase 1: 目標與預算協商 (目前協商輪數: {game.proposal_count})")
    
    if view_party == game.ruling_party and game.p1_step != 'ultimatum':
        st.markdown("### 💥 執政黨專屬權力 (撕破臉選項)")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚨 1. 下達最後通牒", use_container_width=True, type="primary"):
                if game.p1_selected_plan is None: st.error("⚠️ 必須至少完成一次表決後，才能下達最後通牒！")
                else:
                    game.p1_step = 'ultimatum'
                    game.proposing_party = game.party_B if game.ruling_party == game.party_A else game.party_A
                    st.rerun()
        with c2:
            if st.button("⚡ 2. 強行通過 R 黨方案並換位", use_container_width=True, type="primary"):
                if game.p1_proposals.get('R') is None: st.error("⚠️ R 黨尚未提出草案！")
                else:
                    st.session_state.turn_data.update(game.p1_proposals['R'])
                    penalty_funds = game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO']
                    game.party_A.wealth -= penalty_funds
                    game.party_B.wealth -= penalty_funds
                    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                    game.swap_triggered_this_year = True
                    st.session_state.news_flash = f"🚨 **憲政危機！** 執政黨強行通過草案並倒閣換位！\n📉 扣除 {penalty_funds:.0f} 資金！"
                    game.phase = 2
                    game.proposing_party = game.ruling_party
                    st.rerun()
        st.markdown("---")

    if game.p1_step in ['draft_r', 'draft_h']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H'
        active_party = game.r_role_party if active_role == 'R' else game.h_role_party
        
        if view_party != active_party:
            st.warning(f"⏳ **等待中**：目前輪到 {active_party.name} ({active_role} 黨) 閉門擬定草案...")
        else:
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown(f"#### 📝 {view_party.name} ({active_role} 黨) 草案擬定室")
                strategy = st.radio("🤖 策略", ["自訂", "🤝 友善讓步", "⚖️ 公平分攤", "🔥 極限逼近"], horizontal=True)
                
                def_r = 1.0; def_h = float(game.h_fund); def_gdp = 0.0; def_pay = 50; def_decay = float(view_party.current_forecast)
                if game.p1_selected_plan:
                    def_r = game.p1_selected_plan['r_value']; def_h = game.p1_selected_plan['target_h_fund']
                    def_gdp = game.p1_selected_plan['target_gdp_growth']; def_pay = game.p1_selected_plan['r_pay_ratio']
                    def_decay = game.p1_selected_plan['claimed_decay']
                
                if strategy == "🤝 友善讓步":
                    def_r = 0.8 if active_role == 'R' else 1.2; def_pay = 70 if active_role == 'R' else 30
                elif strategy == "🔥 極限逼近":
                    def_r = 1.8 if active_role == 'R' else 0.5; def_pay = 30 if active_role == 'R' else 70
                
                claimed_decay = st.number_input("公告預估衰退值", value=float(def_decay), step=0.05)
                r_val = st.slider("績效達成嚴格度", 0.5, 2.0, float(def_r), 0.1)
                max_possible_h = max(100.0, float(game.total_budget))
                t_h_fund = st.slider("目標行政獎勵基金", 0.0, max_possible_h, float(min(def_h, max_possible_h)), 10.0)
                t_gdp_growth = st.slider("目標 GDP 成長率 (%)", -5.0, 15.0, float(def_gdp), 0.5)
                t_gdp = game.gdp * (1 + (t_gdp_growth / 100.0))
                r_pay_ratio = st.slider("R 黨出資比例 (%)", 0, 100, int(def_pay))
                
                req_funds, h_ratio = formulas.calculate_required_funds(cfg, t_h_fund, t_gdp, game.h_fund, game.gdp, r_val, claimed_decay, game.h_role_party.build_ability)
                r_pays = int(req_funds * (r_pay_ratio / 100.0)); h_pays = req_funds - r_pays
                st.info(f"💰 **本草案必需總額:** `{req_funds}` (R 出 `{r_pays}` / H 出 `{h_pays}`)")

            with col_r:
                st.markdown("#### 📊 智庫真實沙盤推演")
                gdp_pct, h_g, h_n, r_g, r_n, h_sup, r_sup, est_gdp, est_h_fund = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, view_party.current_forecast, game.h_role_party.build_ability, r_pays, h_pays)
                
                my_is_h = (active_role == 'H')
                my_net, my_pays, my_sup = (h_n, h_pays, h_sup) if my_is_h else (r_n, r_pays, r_sup)
                opp_net, opp_pays, opp_sup = (r_n, r_pays, r_sup) if my_is_h else (h_n, h_pays, h_sup)

                st.success(f"🟢 **我方實際淨收入:** `{my_net:.0f}` | **民調:** `{my_sup:+.2f}%`")
                st.error(f"🔴 **對手實際淨收入:** `{opp_net:.0f}` | **民調:** `{opp_sup:+.2f}%`")
                st.markdown(f"📈 **預期 GDP 變動：`{gdp_pct:+.2f}%`**\n🎯 **預期結算 H Fund：`{est_h_fund:.0f}`**")

                if st.button("📤 封存並送出草案", use_container_width=True):
                    proposal = {
                        'r_value': r_val, 'target_h_fund': t_h_fund, 'target_gdp_growth': t_gdp_growth, 
                        'target_gdp': t_gdp, 'r_pay_ratio': r_pay_ratio, 'claimed_decay': claimed_decay,
                        'total_funds': req_funds, 'r_pays': r_pays, 'h_pays': h_pays, 'h_ratio': h_ratio, 'author': active_role
                    }
                    game.p1_proposals[active_role] = proposal
                    
                    if game.p1_step == 'draft_r':
                        game.p1_step = 'draft_h'
                        game.proposing_party = game.h_role_party
                    else:
                        game.p1_step = 'voting_pick'
                        game.proposing_party = game.ruling_party
                    st.rerun()

    elif game.p1_step == 'voting_pick':
        st.markdown("### 🗳️ 表決大會 (第一階段：執政黨定奪)")
        p_R = game.p1_proposals['R']; p_H = game.p1_proposals['H']
        avg_decay = (p_R['claimed_decay'] + p_H['claimed_decay']) / 2.0
        avg_gdp = (p_R['target_gdp'] + p_H['target_gdp']) / 2.0
        avg_h_fund = (p_R['target_h_fund'] + p_H['target_h_fund']) / 2.0
        avg_growth = (p_R['target_gdp_growth'] + p_H['target_gdp_growth']) / 2.0
        
        req_funds_N, h_ratio_N = formulas.calculate_required_funds(cfg, avg_h_fund, avg_gdp, game.h_fund, game.gdp, 1.0, avg_decay, game.h_role_party.build_ability)
        game.p1_proposals['Neutral'] = {
            'r_value': 1.0, 'target_h_fund': avg_h_fund, 'target_gdp_growth': avg_growth, 'target_gdp': avg_gdp,
            'r_pay_ratio': 50, 'claimed_decay': avg_decay, 'total_funds': req_funds_N,
            'r_pays': int(req_funds_N * 0.5), 'h_pays': req_funds_N - int(req_funds_N * 0.5), 'h_ratio': h_ratio_N, 'author': 'Neutral'
        }

        cols = st.columns(3)
        plan_keys = ['R', 'Neutral', 'H']
        plan_titles = ['📘 R 黨草案', '⚖️ 電腦折衷案', '📙 H 黨草案']
        
        for idx, col in enumerate(cols):
            key = plan_keys[idx]
            plan = game.p1_proposals[key]
            with col:
                st.markdown(f"#### {plan_titles[idx]}")
                st.write(f"**衰退:** `{plan['claimed_decay']:.2f}` | **R:** `{plan['r_value']:.2f}`")
                st.write(f"**總額:** `{plan['total_funds']}` | **R負擔:** `{plan['r_pay_ratio']}%`")
                if view_party == game.ruling_party:
                    if st.button(f"✅ 選擇 {plan_titles[idx]}", key=f"pick_{key}", use_container_width=True):
                        game.p1_selected_plan = plan
                        game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party == game.party_A else game.party_A 
                        st.rerun()

    elif game.p1_step == 'voting_confirm':
        st.markdown("### 🗳️ 表決大會 (第二階段：在野黨覆議)")
        plan = game.p1_selected_plan
        if view_party != game.proposing_party:
            st.warning("⏳ 等待在野黨確認...")
        else:
            c1, c2 = st.columns(2)
            if c1.button("✅ 同意法案 (進入執行階段)", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(plan)
                st.session_state.news_flash = f"🗞️ **共識達成！** 正式簽署 [{plan['author']} 案]。"
                game.phase = 2
                game.proposing_party = game.ruling_party
                st.rerun()
            if c2.button("❌ 拒絕並退回重談", use_container_width=True):
                game.proposal_count += 1
                game.p1_step = 'draft_r' 
                game.proposing_party = game.r_role_party
                st.rerun()

    elif game.p1_step == 'ultimatum':
        st.markdown("### 🚨 最後通牒 (Ultimatum)")
        plan = game.p1_selected_plan
        opp_ruling = game.party_B if game.ruling_party == game.party_A else game.party_A
        if view_party != opp_ruling: st.warning(f"⏳ 等待 {opp_ruling.name} 回應...")
        else:
            c1, c2 = st.columns(2)
            if c1.button("✅ 忍辱負重 (接受通牒)", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(plan)
                game.phase = 2
                game.proposing_party = game.ruling_party
                st.rerun()
            if c2.button("💥 寧死不屈 (倒閣換位)", use_container_width=True):
                st.session_state.turn_data.update(plan)
                handle_trust_breakdown()
                st.rerun()

elif game.phase == 2:
    st.subheader(f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name}")
    d = st.session_state.turn_data
    is_h = (view_party == game.h_role_party)
    current_wealth = int(view_party.wealth)
    required_payment = d.get('h_pays', 0) if is_h else d.get('r_pays', 0)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 公共領域")
        st.info(f"📜 **法定款:** 需支付 `{required_payment}`")
        if is_h:
            h_corruption = st.slider("秘密貪污比例 (%)", 0, 100, 0, key="h_corr")
            pub_prop = st.number_input("一般宣傳", 0, current_wealth, 100, key=f"pub_prop_{view_party.name}")
            pub_edu, pub_red = 0, 0  
        else:
            pub_prop = st.number_input("一般宣傳", 0, current_wealth, 100, key=f"pub_prop_{view_party.name}")
            pub_edu = st.number_input("推行教育", 0, current_wealth, key=f"pub_edu_{view_party.name}")
            pub_red = st.number_input("推行降智", 0, current_wealth, key=f"pub_red_{view_party.name}")
        
    with col_b:
        st.markdown("#### 私人領域")
        priv_inv = st.slider("提升調查能力", 0, current_wealth, 0, key=f"priv_inv_{view_party.name}")
        priv_pre = st.slider("提升智庫能力", 0, current_wealth, 0, key=f"priv_pre_{view_party.name}")
        priv_prop = st.slider("提升宣傳能力", 0, current_wealth, 0, key=f"priv_prop_up_{view_party.name}")
        priv_blame_up = st.slider("提升甩鍋能力", 0, current_wealth, 0, key=f"priv_blame_up_{view_party.name}")
        priv_blame_act = st.number_input("投入甩鍋資金", 0, current_wealth, key=f"priv_blame_act_{view_party.name}")
        h_build_up = st.slider("提升建設能力", 0, current_wealth, 0) if is_h else 0

    total_cost = required_payment + pub_prop + pub_edu + pub_red + priv_inv + priv_pre + priv_prop + priv_blame_up + priv_blame_act + h_build_up
    st.write(f"**總花費:** `{total_cost}` / `{current_wealth}`")
    
    if total_cost > current_wealth: st.error("🚨 資金不足！")
    else:
        if st.button(f"確認行動並換手/結算 ({view_party.name})", use_container_width=True, key=f"btn_p2_{view_party.name}_{game.year}"):
            st.session_state[f"{view_party.name}_acts"] = {
                'prop': pub_prop, 'edu': pub_edu, 'red': pub_red,
                'p_inv': priv_inv, 'p_pre': priv_pre, 'p_prop': priv_prop, 'p_blame_up': priv_blame_up, 'p_blame_act': priv_blame_act,
                'h_build_up': h_build_up, 'corr': h_corruption if is_h else 0
            }
            
            if f"{opponent_party.name}_acts" not in st.session_state:
                game.proposing_party = opponent_party
                st.session_state.game = game 
                st.rerun()
            else:
                rp, hp = game.r_role_party, game.h_role_party
                r_acts, h_acts = st.session_state[f"{rp.name}_acts"], st.session_state[f"{hp.name}_acts"]
                
                def calc_turn_stats(decay_val, is_real_calc=False):
                    corrupt_amount = d.get('h_pays',0) * (h_acts['corr'] / 100.0)
                    actual_build = d.get('total_funds', 0) - corrupt_amount
                    caught = False; fine = 0.0; confiscated = 0.0
                    
                    if is_real_calc and h_acts['corr'] > 0:
                        eff_inv = rp.investigate_ability * cfg['R_INV_BONUS']
                        risk_ratio = corrupt_amount / max(1.0, hp.wealth)
                        catch_prob = min(1.0, (eff_inv / cfg['MAX_ABILITY']) * risk_ratio * 10.0)
                        if random.random() < catch_prob:
                            caught = True
                            fine = corrupt_amount * cfg['CORRUPTION_PENALTY']
                            confiscated = corrupt_amount; corrupt_amount = 0 
                    
                    h_ratio = d.get('h_ratio', 1.0)
                    actual_h_funds = actual_build * h_ratio
                    h_bst = (actual_h_funds * hp.build_ability) / max(0.1, d.get('r_value', 1.0))
                    decay_eff = decay_val * d.get('r_value', 1.0) * 0.2 * game.h_fund
                    new_h_fund = max(0.0, game.h_fund + h_bst - decay_eff)
                    
                    gdp_bst = (actual_build * hp.build_ability) / cfg['BUILD_DIFF']
                    new_gdp = max(0.0, game.gdp + gdp_bst - (decay_val * 1000))
                    budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
                    h_share_ratio = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
                    
                    hp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party == hp else 0) + (budg * h_share_ratio) - d.get('h_pays',0) + corrupt_amount - fine
                    rp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party == rp else 0) + (budg * (1 - h_share_ratio)) - d.get('r_pays',0)
                    
                    shift_amt = formulas.calc_support_shift(cfg, hp, rp, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, h_acts['prop'], r_acts['prop'], h_acts['p_blame_act'], r_acts['p_blame_act'])
                    if caught: shift_amt -= 5.0
                    hp_sup_new = max(0.0, min(100.0, hp.support + shift_amt))
                    
                    edu_t, red_t = r_acts['edu'] + h_acts['edu'], r_acts['red'] + h_acts['red']
                    new_san = max(0.0, min(1.0, game.sanity + (edu_t * 0.005) - (red_t * 0.005)))
                    return hp_inc, rp_inc, hp_sup_new, 100.0 - hp_sup_new, new_h_fund, new_gdp, new_san, caught, confiscated

                hp_exp_inc, _, hp_exp_sup, _, _, _, _, _, _ = calc_turn_stats(hp.current_forecast)
                _, rp_exp_inc, _, rp_exp_sup, _, _, _, _, _ = calc_turn_stats(rp.current_forecast)
                hp_act_inc, rp_act_inc, hp_act_sup, rp_act_sup, final_h_fund, final_gdp, final_san, caught, confis = calc_turn_stats(game.current_real_decay, is_real_calc=True)
                
                hp.last_income_diff, hp.last_sup_diff = hp_act_inc - hp_exp_inc, hp_act_sup - hp_exp_sup
                rp.last_income_diff, rp.last_sup_diff = rp_act_inc - rp_exp_inc, rp_act_sup - rp_exp_sup
                hp.last_forecast, rp.last_forecast = hp.current_forecast, rp.current_forecast
                game.last_real_decay = game.current_real_decay

                if caught: st.session_state.news_flash = "🚨 **【貪污醜聞】** R黨監察成功！H黨不法所得全數充公並遭重罰！"
                else: st.session_state.news_flash = "🗞️ 年度結算完畢，社會運轉正常。請開始新年度協商。"

                rp.investigate_ability = min(cfg['MAX_ABILITY'], rp.investigate_ability + formulas.calc_log_gain(r_acts['p_inv']))
                rp.predict_ability = min(cfg['MAX_ABILITY'], rp.predict_ability + formulas.calc_log_gain(r_acts['p_pre']))
                rp.prop_ability = min(cfg['MAX_ABILITY'], rp.prop_ability + formulas.calc_log_gain(r_acts['p_prop']))
                rp.blame_ability = min(cfg['MAX_ABILITY'], rp.blame_ability + formulas.calc_log_gain(r_acts['p_blame_up']))
                
                hp.investigate_ability = min(cfg['MAX_ABILITY'], hp.investigate_ability + formulas.calc_log_gain(h_acts['p_inv']))
                hp.predict_ability = min(cfg['MAX_ABILITY'], hp.predict_ability + formulas.calc_log_gain(h_acts['p_pre']))
                hp.prop_ability = min(cfg['MAX_ABILITY'], hp.prop_ability + formulas.calc_log_gain(h_acts['p_prop']))
                hp.blame_ability = min(cfg['MAX_ABILITY'], hp.blame_ability + formulas.calc_log_gain(h_acts['p_blame_up']))
                hp.build_ability = min(cfg['MAX_ABILITY'], hp.build_ability + formulas.calc_log_gain(h_acts['h_build_up']))
                
                hp.support, rp.support = hp_act_sup, rp_act_sup
                game.sanity, game.h_fund, game.gdp = final_san, final_h_fund, final_gdp
                game.total_budget = cfg['BASE_TOTAL_BUDGET'] + (final_gdp * cfg['HEALTH_MULTIPLIER']) + confis
                hp.wealth += hp_act_inc
                rp.wealth += rp_act_inc
                game.party_A.current_poll_result = None
                game.party_B.current_poll_result = None

                # 歷史資料封裝
                game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))

                game.year += 1
                game.phase = 1
                game.p1_state = 'drafting'
                game.proposal_count = 0
                game.r_role_party = game.ruling_party
                game.h_role_party = game.party_B if game.ruling_party == game.party_A else game.party_A
                game.proposing_party = game.r_role_party
                
                st.session_state.pop(f"{rp.name}_acts", None)
                st.session_state.pop(f"{hp.name}_acts", None)
                del st.session_state.turn_initialized
                st.rerun()
