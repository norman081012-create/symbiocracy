# ==========================================
# phase2.py
# 負責 第二階段 (政策執行與結算) 的 UI 與邏輯
# ==========================================
import streamlit as st
import random
import formulas
import ui_core

def render(game, view_party, opponent_party, cfg):
    is_h = (view_party.name == game.h_role_party.name)
    st.subheader(f"🛠️ Phase 2: 政策執行與行動 - 輪到 {view_party.name} ({'🛡️ 執行系統' if is_h else '⚖️ 監管系統'})")
    
    d = st.session_state.turn_data
    cw = int(view_party.wealth)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📣 政策與媒體")
        if is_h: 
            st.caption("💡 **執行系統特性**: 媒體操控值 1.2 倍加成")
            h_invest = st.slider("🏗️ 實質建設投入 (將轉化為GDP並結算標案)", 0, cw, int(cw * 0.3))
        else: 
            st.caption("💡 **監管系統特性**: 調查能力值 1.2 倍加成")
            h_invest = 0
            
        inv_corr_amt = st.slider("🔍 調查貪污 (投入資金)", 0, cw, 0) if not is_h else 0
        edu_policy = st.slider("🎓 教育方針 (左:填鴨 右:思辨)", -cw, cw, 0)
        edu_up, edu_down = (edu_policy, 0) if edu_policy > 0 else (0, -edu_policy)
        
        media_ctrl = st.slider("📺 媒體操控 (推卸責任/攻擊)", 0, cw, min(50, cw))
        camp_amt = st.slider("🎉 舉辦競選 (提升自身支持度)", 0, cw, 0)
        incite_emo = st.slider("🔥 煽動情緒 (短期降理智)", 0, cw, 0)
        
    with c2:
        st.markdown("#### 🔒 內部升級與維護 (指數型成本)")
        t_inv, c_inv = ui_core.ability_slider("🔍 調查能力", f"up_inv", view_party.investigate_ability, cw, cfg)
        t_stl, c_stl = ui_core.ability_slider("🥷 隱密能力", f"up_stl", view_party.stealth_ability, cw, cfg)
        t_pre, c_pre = ui_core.ability_slider("🕵️ 預測能力", f"up_pre", view_party.predict_ability, cw, cfg)
        t_med, c_med = ui_core.ability_slider("📺 媒體操控力", f"up_med", view_party.media_ability, cw, cfg)
        t_edu, c_edu = ui_core.ability_slider("🎓 教育能力", f"up_edu", view_party.edu_ability, cw, cfg)
        t_bld, c_bld = ui_core.ability_slider("🏗️ 建設能力", f"up_bld", view_party.build_ability, cw, cfg) if is_h else (view_party.build_ability, 0)

    tot = h_invest + media_ctrl + camp_amt + incite_emo + edu_up + edu_down + inv_corr_amt + c_inv + c_pre + c_med + c_edu + c_stl + c_bld
    
    if tot > cw: st.error(f"❌ 資金不足！總花費 `{int(tot)}` 超出資產 `{cw}`")
    else: st.success(f"✅ 資金充裕：總花費 `{int(tot)}` / `{cw}`")
    
    ra, ha = {}, {}
    if f"{opponent_party.name}_acts" in st.session_state:
        opp_acts = st.session_state[f"{opponent_party.name}_acts"]
        ra = opp_acts if is_h else {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'inv_corr': inv_corr_amt}
        ha = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'h_invest': h_invest} if is_h else opp_acts
    else:
        ra = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'inv_corr': inv_corr_amt} if not is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_up': 0, 'edu_down': 0, 'inv_corr': 0}
        ha = {'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 'h_invest': h_invest} if is_h else {'media': 0, 'camp': 0, 'incite': 0, 'edu_up': 0, 'edu_down': 0, 'h_invest': 0}

    # 使用新的預估引擎呈現結果
    preview_data = formulas.calculate_preview(cfg, game, d.get('c_funds', 0), d.get('c_diff', 0), view_party.current_forecast, view_party)
    preview_data['budg'] = game.total_budget
    preview_data['san'] = max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + ((ra['edu_up']+ha['edu_up']) * 0.005) - ((ra['edu_down']+ha['edu_down']) * 0.005)))
    preview_data['emo'] = max(0.0, min(100.0, game.emotion + (ha['incite'] + ra['incite']) * 0.1 - (game.sanity * 20.0)))
    
    ui_core.render_dashboard(game, view_party, cfg, is_preview=True, preview_data=preview_data)
    
    # 修改防消失機制：用 disabled 控制按鈕，保證永遠顯示
    if st.button("確認行動/結算", use_container_width=True, type="primary", disabled=(tot > cw)):
        view_party.wealth -= tot
        
        st.session_state[f"{view_party.name}_acts"] = {
            'media': media_ctrl, 'camp': camp_amt, 'incite': incite_emo, 'edu_up': edu_up, 'edu_down': edu_down, 
            'h_invest': h_invest, 'inv_corr': inv_corr_amt,
            't_inv': t_inv, 't_pre': t_pre, 't_med': t_med, 't_edu': t_edu, 't_stl': t_stl, 't_bld': t_bld
        }
        
        if f"{opponent_party.name}_acts" not in st.session_state:
            game.proposing_party = opponent_party; st.rerun()
        else:
            rp, hp = game.r_role_party, game.h_role_party
            ra, ha = st.session_state[f"{rp.name}_acts"], st.session_state[f"{hp.name}_acts"]
            
            # --- 核心物理結算 ---
            c_funds = d.get('c_funds', 0)
            new_gdp, c_net, l_gdp, gross, res = formulas.calc_economic_physics(cfg, game.gdp, game.current_real_decay, ha['h_invest'], hp.build_ability)
            target_req = c_funds * max(0.1, d.get('c_diff', 1.0))
            act_h_rate = min(1.0, c_net / target_req) if target_req > 0 else 1.0
            
            # 結算跨年發放
            game.pending_h_payout = c_funds * act_h_rate
            game.pending_r_payout = c_funds * (1.0 - act_h_rate) + (game.project_pool - c_funds)
            
            gdp_pct = ((new_gdp - game.gdp)/max(1.0, game.gdp)) * 100.0
            shift = formulas.calc_support_shift(cfg, hp, rp, act_h_rate, gdp_pct, ha, ra)
            hp_sup_new = max(0.0, min(100.0, hp.support + shift['actual_shift']))
            
            emotion_delta = (ha['incite'] + ra['incite']) * 0.1 - gdp_pct - (game.sanity * 20.0)
            game.emotion = max(0.0, min(100.0, game.emotion + emotion_delta))
            
            edu_t, red_t = ra['edu_up'] + ha['edu_up'], ra['edu_down'] + ha['edu_down']
            game.sanity = max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + (edu_t * 0.005) - (red_t * 0.005)))
            
            game.last_year_report = {
                'old_gdp': game.gdp, 'old_san': game.sanity, 'old_emo': game.emotion,
                'h_party_name': hp.name, 'real_decay': game.current_real_decay, 
                'view_party_forecast': view_party.current_forecast
            }

            hp.support, rp.support = hp_sup_new, 100.0 - hp_sup_new
            
            if game.year % cfg['ELECTION_CYCLE'] == 1:
                winner = hp if hp.support > rp.support else rp
                st.session_state.news_flash = f"🎉 **【大選結果】真實支持度 {winner.support:.1f}% vs {(100-winner.support):.1f}%** {winner.name} 取勝，成為當權政府！"
                st.session_state.anim = 'balloons'
                game.ruling_party = winner

            game.gdp = new_gdp
            
            # 能力更新
            rp.investigate_ability = ra['t_inv']; rp.predict_ability = ra['t_pre']; rp.media_ability = ra['t_med']; rp.edu_ability = ra['t_edu']; rp.stealth_ability = ra['t_stl']
            hp.investigate_ability = ha['t_inv']; hp.predict_ability = ha['t_pre']; hp.media_ability = ha['t_med']; hp.edu_ability = ha['t_edu']; hp.stealth_ability = ha['t_stl']; hp.build_ability = ha['t_bld']

            game.record_history(is_election=(game.year % cfg['ELECTION_CYCLE'] == 1))
            
            game.year += 1; game.phase = 1; game.p1_step = 'draft_r'
            game.p1_proposals = {'R': None, 'H': None}; game.p1_selected_plan = None
            game.proposing_party = game.r_role_party
            for k in list(st.session_state.keys()):
                if k.startswith('ui_decay_') or k.endswith('_acts'): del st.session_state[k]
            del st.session_state.turn_initialized; st.rerun()
