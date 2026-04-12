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
    elec_status = content.get_election_icon(game.year, cfg['ELECTION_CYCLE'])
    st.write(f"**年份:** {game.year} / {cfg['END_YEAR']} ({elec_status})")
    if god_mode: st.error(f"👁️ **上帝視角：**\n真實衰退率為 **{game.current_real_decay:.2f}**")

st.title("🏛️ Symbiocracy 共生民主模擬器 v3.0.0")

# 渲染頂部儀表板與訊息欄
if game.phase == 1:
    interface.render_dashboard(game, view_party, cfg, is_preview=False)
interface.render_message_board(game)
interface.render_party_cards(game, view_party, god_mode, is_election_year, cfg)

def handle_trust_breakdown():
    penalty = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
    game.party_A.wealth -= penalty; game.party_B.wealth -= penalty
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True
    game.emotion = min(100.0, game.emotion + 30.0) 
    st.session_state.news_flash = f"🗞️ **【快訊】政局動盪！** 兩黨談判破裂觸發憲政危機，被迫換位！\n💸 雙方各遭強制捐款 {penalty} 資金給社福團體作為懲罰，社會情緒激憤！"
    game.phase = 2

if game.phase == 1:
    st.subheader(f"🤝 Phase 1: 監管系統委託執行系統建設提案 (輪數: {game.proposal_count})")
    
    if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_draft']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H' if game.p1_step == 'draft_h' else game.p1_step.split('_')[1].upper()
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手公布草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({'監管系統' if active_role == 'R' else '執行系統'}黨) 草案擬定室")
            
            opp_role = 'H' if active_role == 'R' else 'R'
            opp_plan = game.p1_proposals.get(opp_role)
            opp_claimed = opp_plan['claimed_decay'] if opp_plan else None
            
            my_plan = game.p1_proposals.get(active_role)
            my_last_claimed = my_plan['claimed_decay'] if my_plan else view_party.current_forecast
            
            c_decay, c_gdp = st.columns(2)
            input_key = f"ui_decay_val_{game.year}_{active_role}"
            
            if input_key not in st.session_state:
                st.session_state[input_key] = float(view_party.current_forecast)
            
            with c_decay:
                opp_txt = f"對手公告: {opp_claimed:.2f}" if opp_claimed is not None else "等待對手公告"
                st.markdown(f"**公告衰退值 (當前: {st.session_state[input_key]:.2f})** | {opp_txt}")
                claimed_decay = st.number_input("公告衰退值", value=float(st.session_state[input_key]), step=0.01, key=f"num_{input_key}", label_visibility="collapsed")
                st.session_state[input_key] = claimed_decay
                
            with c_gdp:
                st.markdown("**目標 GDP 成長率 (%)**")
                t_gdp_growth = st.number_input("GDP成長", value=0.0, step=0.5, label_visibility="collapsed")

            max_h = max(10.0, float(game.total_budget))
            t_h_fund = st.slider("標案達標付款 (最高不超過當年總預算)", 0.0, max_h, float(min(game.h_fund, max_h)), 10.0)
            r_val = st.slider("標案利潤 (右低利潤/高嚴格度，左高利潤/低嚴格度)", 0.5, 3.0, 1.0, 0.1)
            
            t_gdp = game.gdp * (1 + (t_gdp_growth / 100.0))
            req_funds, h_ratio = formulas.calculate_required_funds(cfg, t_h_fund, t_gdp, game.h_fund, game.gdp, r_val, claimed_decay, game.h_role_party.build_ability)
            
            safe_req = max(1, int(req_funds))
            r_pays = st.slider(f"💰 監管系統出資 | 總標案金額: {req_funds} (佔比 {(req_funds/max(1.0, game.total_budget))*100:.1f}%) | 執行系統出資", 0, safe_req, int(safe_req * 0.5))
            h_pays = req_funds - r_pays
            
            o_gdp_pct, o_h_g, o_h_n, o_r_g, o_r_n, o_h_sup, o_r_sup, o_est_gdp, o_est_h_fund, o_h_roi, o_r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, view_party.current_forecast, game.h_role_party.build_ability, r_pays, h_pays)
            c_gdp_pct, c_h_g, c_h_n, c_r_g, c_r_n, c_h_sup, c_r_sup, c_est_gdp, c_est_h_fund, c_h_roi, c_r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, claimed_decay, game.h_role_party.build_ability, r_pays, h_pays)

            if st.button("📤 送出草案", use_container_width=True, type="primary"):
                plan_dict = {
                    'r_value': r_val, 'target_h_fund': t_h_fund, 'target_gdp_growth': t_gdp_growth, 
                    'target_gdp': t_gdp, 'r_pays': r_pays, 'claimed_decay': claimed_decay,
                    'total_funds': req_funds, 'h_pays': h_pays, 'h_ratio': h_ratio, 'author': active_role,
                    'h_roi': c_h_roi, 'r_roi': c_r_roi,
                    'est_h_n': o_h_n, 'est_r_n': o_r_n, 'est_h_sup': o_h_sup, 'est_r_sup': o_r_sup
                }
                
                if game.p1_step == 'ultimatum_draft':
                    game.p1_selected_plan = plan_dict
                    game.p1_step = 'ultimatum_resolve'
                    game.proposing_party = game.party_B if view_party.name == game.party_A.name else game.party_A
                else:
                    game.p1_proposals[active_role] = plan_dict
                    if game.p1_step == 'draft_r': game.p1_step = 'draft_h'; game.proposing_party = game.h_role_party
                    else: game.p1_step = 'voting_pick'; game.proposing_party = game.ruling_party
                st.rerun()

            st.markdown("---")
            c_prev1, c_prev2 = st.columns(2)
            my_is_h = (active_role == 'H')
            
            with c_prev1:
                my_net, my_sup, my_roi = (o_h_n, o_h_sup, o_h_roi) if my_is_h else (o_r_n, o_r_sup, o_r_roi)
                opp_net, opp_sup, opp_roi = (o_r_n, o_r_sup, o_r_roi) if my_is_h else (o_h_n, o_h_sup, o_h_roi)
                st.markdown(f"**🛡️ 依據自己智庫估算** *(衰退估算: -{view_party.current_forecast:.2f})*")
                st.success(f"🟢 **我方預期收益:** `{my_net:.0f}` (ROI: {my_roi:.1f}%) | **支持度:** `{my_sup:+.2f}%`")
                st.error(f"🔴 **對手預期收益:** `{opp_net:.0f}` (ROI: {opp_roi:.1f}%) | **支持度:** `{opp_sup:+.2f}%`")
                st.info(f"📈 **預期 GDP:** `{game.gdp:.0f} ➔ {o_est_gdp:.0f}` ({o_gdp_pct:+.2f}%)")
            
            with c_prev2:
                my_net, my_sup, my_roi = (c_h_n, c_h_sup, c_h_roi) if my_is_h else (c_r_n, c_r_sup, c_r_roi)
                opp_net, opp_sup, opp_roi = (c_r_n, c_r_sup, c_r_roi) if my_is_h else (c_h_n, c_h_sup, c_h_roi)
                st.markdown(f"**📢 依據方案公告估算** *(衰退估算: -{claimed_decay:.2f})*")
                st.success(f"🟢 **我方預期收益:** `{my_net:.0f}` (ROI: {my_roi:.1f}%) | **支持度:** `{my_sup:+.2f}%`")
                st.error(f"🔴 **對手預期收益:** `{opp_net:.0f}` (ROI: {opp_roi:.1f}%) | **支持度:** `{opp_sup:+.2f}%`")
                st.info(f"📈 **預期 GDP:** `{game.gdp:.0f} ➔ {c_est_gdp:.0f}` ({c_gdp_pct:+.2f}%)")

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
                    interface.render_proposal_component('⚖️ 監管系統草案' if key=='R' else '🛡️ 執行系統草案', plan, game, view_party, cfg)
                    if st.button(f"✅ 選擇此方案", key=f"pick_{key}", use_container_width=True):
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            interface.render_proposal_component('📜 待覆議草案內容', game.p1_selected_plan, game, view_party, cfg)
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("✅ 同意法案", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **【快訊】預算案三讀通過！** 歷經 {game.proposal_count} 輪黨團協商，雙方正式簽署法案。"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button("❌ 拒絕並重談", use_container_width=True):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()
            if c3.button("🔄 同意但換位", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                penalty = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
                game.party_A.wealth -= penalty; game.party_B.wealth -= penalty
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.swap_triggered_this_year = True
                st.session_state.news_flash = f"🗞️ **【快訊】執政權轉移！** 在野黨同意預算案但要求換位，雙方扣款捐贈 {penalty} 資金！"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c4.button("💥 提最後通牒", use_container_width=True):
                st.session_state.news_flash = f"🗞️ **【快訊】最後通牒！** {view_party.name} 拒絕提案並下達最後通牒，這將是最後一次提案機會！"
                game.p1_step = 'ultimatum_draft'
                game.proposing_party = view_party
                st.rerun()

    elif game.p1_step == 'ultimatum_resolve':
        st.markdown("### 🚨 最後通牒決斷 (Ultimatum)")
        if view_party.name != game.proposing_party.name: st.warning(f"⏳ 等待 {game.proposing_party.name} 回應...")
        else:
            interface.render_proposal_component('📜 通牒底線方案', game.p1_selected_plan, game, view_party, cfg)
            c1, c2 = st.columns(2)
            if c1.button("✅ 忍辱負重 (接受通牒)", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **【快訊】通牒生效！** 在野黨妥協吞下底線方案。"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button("🔄 同意但換位", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                penalty = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
                game.party_A.wealth -= penalty; game.party_B.wealth -= penalty
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.swap_triggered_this_year = True
                game.emotion = min(100.0, game.emotion + 20.0) 
                st.session_state.news_flash = f"🗞️ **【快訊】政局動盪！** 接受通牒但強行倒閣換位，雙方扣款捐贈 {penalty} 資金！"
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
        if is_h: st.caption("💡 **執行系統特性**: 媒體操控值 1.2 倍加成")
        else: st.caption("💡 **監管系統特性**: 調查能力值 1.2 倍加成")
        
        media_ctrl = st.slider("📺 媒體操控 (搶功勞/推卸責任)", 0, current_wealth, min(100, current_wealth))
        incite_emo = st.slider("🔥 煽動情緒 (短期降理智)", 0, current_wealth, 0)
        edu_up = st.slider("🎓 推行教育 (提升理智)", 0, current_wealth, 0) if not is_h else 0
        edu_down = st.slider("🧠 推行降智 (降低理智)", 0, current_wealth, 0) if not is_h else 0
        
        if is_h:
            h_corr_pct = st.slider("💸 秘密貪污 (%)", 0, 100, 0)
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
    
    # 建構 Preview Dictionary
    if f"{opponent_party.name}_acts" in st.session_state:
        opp_acts = st.session_state[f"{opponent_party.name}_acts"]
        ra = opp_acts if is_h else {'media': media_ctrl, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct}
        ha = {'media': media_ctrl, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct} if is_h else opp_acts
    else:
        ra = {'media': media_ctrl, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct} if not is_h else {'media': 0, 'incite': 0, 'edu_up': 0, 'edu_down': 0, 'corr': 0}
        ha = {'media': media_ctrl, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct} if is_h else {'media': 0, 'incite': 0, 'edu_up': 0, 'edu_down': 0, 'corr': 0}

    corr_amt = d.get('total_funds', 0) * (ha['corr'] / 100.0)
    act_build = d.get('total_funds', 0) - corr_amt
    h_bst = (act_build * d.get('h_ratio', 1.0) * game.h_role_party.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
    new_h_fund = max(0.0, game.h_fund + h_bst - (view_party.current_forecast * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
    gdp_bst = (act_build * game.h_role_party.build_ability) / cfg['BUILD_DIFF']
    new_gdp = max(0.0, game.gdp + gdp_bst - (view_party.current_forecast * 1000))
    budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
    h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5

    preview_data = {
        'gdp': new_gdp, 'budg': budg, 'h_fund': new_h_fund,
        'san': max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + ((ra['edu_up']+ha['edu_up']) * 0.005) - ((ra['edu_down']+ha['edu_down']) * 0.005))),
        'emo': max(0.0, min(100.0, game.emotion + (ha['incite'] + ra['incite']) * 0.1 - (((new_gdp - game.gdp)/max(1.0, game.gdp))*100) - (game.sanity * 20.0)))
    }
    
    interface.render_dashboard(game, view_party, cfg, is_preview=True, preview_data=preview_data)
    
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
            new_h_fund = max(0
