# ==========================================
# main.py
# 主程式：負責狀態轉移、UI 拼裝與動態數值分發
# ==========================================
import streamlit as st
import random
import content, formulas, interface

st.set_page_config(page_title="Symbiocracy v3.0.0", layout="wide")
st.components.v1.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)

if 'cfg' not in st.session_state: st.session_state.cfg = content.DEFAULT_CONFIG.copy()
cfg = st.session_state.cfg

if 'game' not in st.session_state:
    st.session_state.game = formulas.GameEngine(cfg)
    st.session_state.turn_data = {}

game = st.session_state.game

if game.year > cfg['END_YEAR']:
    interface.render_endgame_charts(game.history, cfg)
    if st.button("🔄 重新開始全新遊戲", use_container_width=True): st.session_state.clear(); st.rerun()
    st.stop()

if 'turn_initialized' not in st.session_state:
    game.current_real_decay = max(0.0, round(random.uniform(cfg['DECAY_MIN'], cfg['DECAY_MAX']), 2))
    for p in [game.party_A, game.party_B]:
        error = cfg['PREDICT_DIFF'] / max(0.1, p.predict_ability)
        p.current_forecast = max(0.0, round(game.current_real_decay + random.uniform(-error, error), 2))
    
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

st.title("🏛️ Symbiocracy 共生民主模擬器 v3.0.0")

if game.phase == 1: interface.render_dashboard(game, view_party, cfg, False)
interface.render_message_board(game, game.phase)
interface.render_party_cards(game, view_party, god_mode, is_election_year, cfg)

if game.phase == 1:
    st.subheader(f"🤝 Phase 1: 預算標案協商 (輪數: {game.proposal_count})")
    
    if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_draft']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H' if game.p1_step == 'draft_h' else game.p1_step.split('_')[1].upper()
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning("⏳ 等待對手公布草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({'監管系統' if active_role == 'R' else '執行系統'}) 草案擬定室")
            
            c_top1, c_top2 = st.columns(2)
            with c_top1:
                claimed_decay = st.number_input(f"公告衰退值 (當前: {view_party.current_forecast:.2f})", value=float(view_party.current_forecast), step=0.01)
            with c_top2:
                t_gdp_growth = st.number_input("目標 GDP 成長 (%)", value=0.0, step=0.5)

            max_h = max(10.0, float(game.total_budget))
            t_h_fund = st.slider("標案達標付款 (目標獎勵)", 0.0, max_h, float(min(game.h_fund, max_h)))
            r_val = st.slider("標案利潤 (嚴格度)", 0.5, 3.0, 1.0)
            
            req_funds, h_ratio = formulas.calculate_required_funds(cfg, t_h_fund, game.gdp*(1+t_gdp_growth/100), game.h_fund, game.gdp, r_val, claimed_decay, game.h_role_party.build_ability)
            
            st.markdown(f"💰 **監管出資** | 總標案: `{req_funds}` (佔比 {(req_funds/max(1, game.total_budget))*100:.1f}%) | **執行出資:** `{req_funds - st.session_state.get('r_pays_sl', int(req_funds*0.5))}`")
            r_pays = st.slider("監管系統出資", 0, max(1, int(req_funds)), int(req_funds * 0.5), key="r_pays_sl", label_visibility="collapsed")
            h_pays = req_funds - r_pays
            
            if st.button("📤 送出提案", use_container_width=True, type="primary"):
                _, _, _, _, _, _, _, _, _, c_h_roi, c_r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, claimed_decay, game.h_role_party.build_ability, r_pays, h_pays)
                _, _, o_h_n, _, o_r_n, o_h_sup, o_r_sup, _, _, _, _ = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, view_party.current_forecast, game.h_role_party.build_ability, r_pays, h_pays)
                
                plan = {
                    'r_value': r_val, 'target_h_fund': t_h_fund, 'target_gdp_growth': t_gdp_growth, 'target_gdp': game.gdp*(1+t_gdp_growth/100),
                    'r_pays': r_pays, 'h_pays': h_pays, 'total_funds': req_funds, 'h_ratio': h_ratio, 'claimed_decay': claimed_decay,
                    'h_roi': c_h_roi, 'r_roi': c_r_roi, 'h_net_est': o_h_n, 'r_net_est': o_r_n, 'h_sup_est': o_h_sup, 'r_sup_est': o_r_sup
                }
                
                if game.p1_step == 'ultimatum_draft':
                    game.p1_selected_plan = plan; game.p1_step = 'ultimatum_resolve'
                    game.proposing_party = game.party_B if view_party.name == game.party_A.name else game.party_A
                else:
                    game.p1_proposals[active_role] = plan
                    if game.p1_step == 'draft_r': game.p1_step = 'draft_h'; game.proposing_party = game.h_role_party
                    else: game.p1_step = 'voting_pick'; game.proposing_party = game.ruling_party
                st.rerun()

    elif game.p1_step == 'voting_pick':
        if view_party.name != game.ruling_party.name: st.warning("⏳ 等待執政黨定奪...")
        else:
            cols = st.columns(2)
            for idx, key in enumerate(['R', 'H']):
                plan = game.p1_proposals.get(key)
                with cols[idx]:
                    if not plan: st.info("等待對方發布草案..."); continue
                    interface.render_proposal_component('⚖️ 監管草案' if key=='R' else '🛡️ 執行草案', plan, game, view_party, cfg)
                    if st.button(f"✅ 選擇此方案", key=f"pick_{key}", use_container_width=True):
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            interface.render_proposal_component('📜 待覆議標案內容', game.p1_selected_plan, game, view_party, cfg)
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("✅ 同意法案"):
                st.session_state.turn_data.update(game.p1_selected_plan); game.phase = 2; st.session_state.news_flash = "預算案三讀通過！" ; st.rerun()
            if c2.button("❌ 拒絕並重談"):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()
            if c3.button("🔄 同意但換位"):
                fee = cfg['THIRD_PARTY_FEE']; st.warning(f"⚠️ 警告：換位需支付 ${fee} 懲罰金。")
                if st.button("確認換位"):
                    st.session_state.turn_data.update(game.p1_selected_plan)
                    game.party_A.wealth -= fee; game.party_B.wealth -= fee
                    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                    game.swap_triggered_this_year = True; game.phase = 2; st.session_state.news_flash = f"執政權轉移！雙方扣款捐贈 ${fee}！"; st.rerun()
            if c4.button("💥 提最後通牒"):
                st.session_state.news_flash = "已下達最後通牒！"
                game.p1_step = 'ultimatum_draft'; game.proposing_party = view_party; st.rerun()

    elif game.p1_step == 'ultimatum_resolve':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待決斷...")
        else:
            interface.render_proposal_component('🚨 最後通牒方案', game.p1_selected_plan, game, view_party, cfg)
            c1, c2 = st.columns(2)
            if c1.button("✅ 忍辱負重 (接受)"):
                st.session_state.turn_data.update(game.p1_selected_plan); game.phase = 2; st.rerun()
            if c2.button("💥 寧死不屈 (換位)"):
                fee = cfg['THIRD_PARTY_FEE']
                st.session_state.turn_data.update(game.p1_selected_plan)
                game.party_A.wealth -= fee; game.party_B.wealth -= fee
                game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
                game.swap_triggered_this_year = True; game.phase = 2; st.rerun()

elif game.phase == 2:
    st.subheader(f"🛠️ Phase 2: 政策與預算執行 - {view_party.name}")
    d = st.session_state.turn_data
    is_h = (view_party.name == game.h_role_party.name)
    req_pay = d.get('h_pays', 0) if is_h else d.get('r_pays', 0)
    current_wealth = int(view_party.wealth)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📣 政策與媒體")
        st.info(f"📜 法定專案款 (不可動用): `${req_pay}`")
        media_ctrl = st.slider("📺 媒體操控 (搶功勞/推卸責任)", 0, current_wealth, 0)
        camp = st.slider("🎉 競選宣傳 (提升中長期支持度)", 0, current_wealth, 0)
        incite_emo = st.slider("🔥 煽動情緒 (短期降理智)", 0, current_wealth, 0)
        edu_up = st.slider("🎓 推行教育 (提升理智)", 0, current_wealth, 0) if not is_h else 0
        edu_down = st.slider("🧠 推行降智 (降低理智)", 0, current_wealth, 0) if not is_h else 0
        h_corr_pct = st.slider("💸 秘密貪污 (%)", 0, 100, 0) if is_h else 0
        
    with c2:
        st.markdown("#### 🔒 內部升級與維護")
        priv_inv = interface.ability_slider("🔍 調查能力", f"up_inv_{view_party.name}", view_party.investigate_ability, current_wealth, cfg)
        priv_pre = interface.ability_slider("🕵️ 預測能力", f"up_pre_{view_party.name}", view_party.predict_ability, current_wealth, cfg)
        priv_media = interface.ability_slider("📺 媒體能力", f"up_med_{view_party.name}", view_party.media_ability, current_wealth, cfg)
        priv_edu = interface.ability_slider("🎓 教育能力", f"up_edu_{view_party.name}", view_party.edu_ability, current_wealth, cfg)
        h_build_up = interface.ability_slider("🏗️ 建設能力", f"up_bld_{view_party.name}", view_party.build_ability, current_wealth, cfg) if is_h else 0

    tot = req_pay + media_ctrl + camp + incite_emo + edu_up + edu_down + priv_inv + priv_pre + priv_media + priv_edu + h_build_up
    st.write(f"**總花費:** `{tot}` / `{current_wealth}`")
    
    # 建立預覽字典
    ra = {'media': media_ctrl, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct, 'camp': camp} if not is_h else {'media': 0, 'incite': 0, 'edu_up': 0, 'edu_down': 0, 'corr': 0, 'camp': 0}
    ha = {'media': media_ctrl, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct, 'camp': camp} if is_h else {'media': 0, 'incite': 0, 'edu_up': 0, 'edu_down': 0, 'corr': 0, 'camp': 0}
    if f"{opponent_party.name}_acts" in st.session_state:
        opp_acts = st.session_state[f"{opponent_party.name}_acts"]
        ra = opp_acts if is_h else ra; ha = ha if is_h else opp_acts
    
    rp, hp = game.r_role_party, game.h_role_party
    corr_amt = d.get('total_funds', 0) * (ha['corr'] / 100.0)
    act_build = d.get('total_funds', 0) - corr_amt
    h_bst = (act_build * d.get('h_ratio', 1.0) * hp.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
    new_h_fund = max(0.0, game.h_fund + h_bst - (view_party.current_forecast * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
    gdp_bst = (act_build * hp.build_ability) / cfg['BUILD_DIFF']
    new_gdp = max(0.0, game.gdp + gdp_bst - (view_party.current_forecast * 1000))
    budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
    h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
    
    hp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == hp.name else 0) + (budg * h_shr) - d.get('h_pays',0) + corr_amt
    rp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == rp.name else 0) + (budg * (1 - h_shr)) - d.get('r_pays',0)
    
    shift = formulas.calc_support_shift(cfg, hp, rp, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha['media'], ra['media'])
    
    preview_data = {
        'gdp': new_gdp, 'budg': budg, 'h_fund': new_h_fund,
        'san': max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + ((ra['edu_up']+ha['edu_up']) * 0.005) - ((ra['edu_down']+ha['edu_down']) * 0.005))),
        'emo': max(0.0, min(100.0, game.emotion + (ha['incite'] + ra['incite']) * 0.1 - (((new_gdp - game.gdp)/max(1.0, game.gdp))*100) - (game.sanity * 20.0))),
        'h_net': hp_inc, 'r_net': rp_inc,
        'h_roi': (hp_inc / max(1, float(req_pay))) * 100.0 if req_pay > 0 else float('inf'),
        'r_roi': (rp_inc / max(1, float(d.get('h_pays' if not is_h else 'r_pays', 0)))) * 100.0 if d.get('h_pays' if not is_h else 'r_pays', 0) > 0 else float('inf'),
        'h_sup': shift['actual_shift'], 'r_sup': -shift['actual_shift']
    }
    
    # 底部動態預覽
    interface.render_dashboard(game, view_party, cfg, is_preview=True, preview_data=preview_data)
    
    if tot <= current_wealth and st.button("確認行動/結算", use_container_width=True, type="primary"):
        st.session_state[f"{view_party.name}_acts"] = {
            'media': media_ctrl, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'corr': h_corr_pct, 'camp': camp,
            'p_inv': priv_inv, 'p_pre': priv_pre, 'p_media': priv_media, 'p_edu': priv_edu, 'p_bld': h_build_up
        }
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            formulas.execute_year_end(game, cfg, st.session_state[f"{game.r_role_party.name}_acts"], st.session_state[f"{game.h_role_party.name}_acts"], d)
            for p_key, act_data in [(game.r_role_party.name, st.session_state[f"{game.r_role_party.name}_acts"]), (game.h_role_party.name, st.session_state[f"{game.h_role_party.name}_acts"])]:
                p = game.r_role_party if p_key == game.r_role_party.name else game.h_role_party
                p.investigate_ability, _, _ = formulas.get_ability_preview(p.investigate_ability, act_data['p_inv'], cfg)
                p.predict_ability, _, _ = formulas.get_ability_preview(p.predict_ability, act_data['p_pre'], cfg)
                p.media_ability, _, _ = formulas.get_ability_preview(p.media_ability, act_data['p_media'], cfg)
                p.edu_ability, _, _ = formulas.get_ability_preview(p.edu_ability, act_data['p_edu'], cfg)
                p.build_ability, _, _ = formulas.get_ability_preview(p.build_ability, act_data['p_bld'], cfg)

            if game.year % cfg['ELECTION_CYCLE'] == 1:
                winner = game.party_A if game.party_A.support > game.party_B.support else game.party_B
                game.ruling_party = winner
                st.session_state.news_flash = f"🎉 **【大選結果】** {winner.name} 以 {winner.support:.1f}% 勝出！"

            game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
            game.year += 1; game.phase = 1; game.p1_step = 'draft_r'
            game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
            game.poll_done_this_year = False; game.proposing_party = game.r_role_party
            for k in list(st.session_state.keys()):
                if k.startswith('ui_decay_') or k.endswith('_acts'): del st.session_state[k]
            del st.session_state.turn_initialized; st.rerun()
