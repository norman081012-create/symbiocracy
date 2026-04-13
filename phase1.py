# ==========================================
# phase1.py
# 負責 第一階段 (提案與談判) 的 UI 與邏輯
# ==========================================
import streamlit as st
import formulas
import engine
import ui_core

def render(game, view_party, cfg):
    penalty_amt = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
    st.subheader(f"🤝 Phase 1: 監管系統委託執行系統建設提案 (輪數: {game.proposal_count})")
    
    if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_draft_r']:
        active_role = 'R' if game.p1_step in ['draft_r', 'ultimatum_draft_r'] else 'H'
        
        if game.p1_step == 'ultimatum_draft_r':
            st.error("🚨 **最後通牒啟動中：** 監管系統必須擬定最終裁決草案！")
            
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手公布草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({'監管系統' if active_role == 'R' else '執行系統'}黨) 草案擬定室")
            
            opp_role = 'H' if active_role == 'R' else 'R'
            opp_plan = game.p1_proposals.get(opp_role)
            opp_claimed = opp_plan['claimed_decay'] if opp_plan else None
            
            c_decay, c_gdp = st.columns(2)
            input_key = f"ui_decay_val_{game.year}_{active_role}"
            
            if input_key not in st.session_state: st.session_state[input_key] = float(view_party.current_forecast)
            
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
            r_pays = st.slider(f"💰 資金分配調整", 0, safe_req, int(safe_req * 0.5), label_visibility="collapsed")
            h_pays = req_funds - r_pays
            r_pct = (r_pays / max(1, req_funds)) * 100
            h_pct = (h_pays / max(1, req_funds)) * 100
            
            st.markdown(f"### 監管系統出資 {r_pays} (佔比 {r_pct:.1f}%) / 本草案必需總額: {req_funds} / 執行系統出資 {h_pays} (佔比 {h_pct:.1f}%)")
            
            o_gdp_pct, o_h_g, o_h_n, o_r_g, o_r_n, o_h_sup, o_r_sup, o_est_gdp, o_est_h_fund, o_h_roi, o_r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, view_party.current_forecast, game.h_role_party.build_ability, r_pays, h_pays)
            c_gdp_pct, c_h_g, c_h_n, c_r_g, c_r_n, c_h_sup, c_r_sup, c_est_gdp, c_est_h_fund, c_h_roi, c_r_roi = formulas.calculate_preview(cfg, game, req_funds, h_ratio, r_val, claimed_decay, game.h_role_party.build_ability, r_pays, h_pays)

            plan_dict = {
                'r_value': r_val, 'target_h_fund': t_h_fund, 'target_gdp_growth': t_gdp_growth, 
                'target_gdp': t_gdp, 'r_pays': r_pays, 'claimed_decay': claimed_decay,
                'total_funds': req_funds, 'h_pays': h_pays, 'h_ratio': h_ratio, 'author': active_role,
                'h_roi': c_h_roi, 'r_roi': c_r_roi,
                'est_h_n': o_h_n, 'est_r_n': o_r_n, 'est_h_sup': o_h_sup, 'est_r_sup': o_r_sup
            }

            c_btn1, c_btn2, c_btn3 = st.columns(3)
            
            if c_btn1.button("📤 送出常規草案", use_container_width=True, type="primary"):
                if game.p1_step == 'ultimatum_draft_r':
                    game.p1_selected_plan = plan_dict; game.p1_step = 'ultimatum_resolve_h'; game.proposing_party = game.h_role_party
                else:
                    game.p1_proposals[active_role] = plan_dict
                    if game.p1_step == 'draft_r': game.p1_step = 'draft_h'; game.proposing_party = game.h_role_party
                    else: game.p1_step = 'voting_pick'; game.proposing_party = game.ruling_party
                st.rerun()
                
            if active_role == 'R' and game.p1_step == 'draft_r':
                if c_btn2.button("💥 發布最後通牒", use_container_width=True):
                    game.p1_selected_plan = plan_dict
                    game.p1_step = 'ultimatum_resolve_h'
                    game.proposing_party = game.h_role_party
                    st.session_state.news_flash = f"🗞️ **【快訊】監管系統下達最後通牒！** {view_party.name} 逼迫執行系統必須接受此案，否則將引發倒閣！"
                    st.rerun()
                
                swap_cost = 0 if view_party.name == game.ruling_party.name else penalty_amt
                if c_btn3.button(f"🔄 強制通過並換位 (費用: {swap_cost})", use_container_width=True):
                    st.session_state.turn_data.update(plan_dict)
                    engine.trigger_swap(game, swap_cost, "監管系統強制接管！")
                    game.proposing_party = game.ruling_party; st.rerun()

            st.markdown("---")
            c_prev1, c_prev2 = st.columns(2)
            my_is_h = (active_role == 'H')
            
            with c_prev1:
                my_net, my_sup, my_roi = (o_h_n, o_h_sup, o_h_roi) if my_is_h else (o_r_n, o_r_sup, o_r_roi)
                opp_net, opp_sup, opp_roi = (o_r_n, o_r_sup, o_r_roi) if my_is_h else (o_h_n, o_h_sup, o_h_roi)
                st.markdown(f"**🛡️ 依據自己智庫估算** *(衰退估算: -{view_party.current_forecast:.2f})*")
                st.markdown(f"<h3>🟢 我方預期收益: {my_net:.0f} (ROI: {my_roi:.1f}%)</h3>", unsafe_allow_html=True)
                st.markdown(f"<h3>🔴 對手預期收益: {opp_net:.0f} (ROI: {opp_roi:.1f}%)</h3>", unsafe_allow_html=True)
                st.info(f"📈 **預期 GDP:** `{game.gdp:.0f} ➔ {o_est_gdp:.0f}` ({o_gdp_pct:+.2f}%)")
            
            with c_prev2:
                my_net, my_sup, my_roi = (c_h_n, c_h_sup, c_h_roi) if my_is_h else (c_r_n, c_r_sup, c_r_roi)
                opp_net, opp_sup, opp_roi = (c_r_n, c_r_sup, c_r_roi) if my_is_h else (c_h_n, c_h_sup, c_h_roi)
                st.markdown(f"**📢 依據方案公告估算** *(衰退估算: -{claimed_decay:.2f})*")
                st.markdown(f"<h3>🟢 我方預期收益: {my_net:.0f} (ROI: {my_roi:.1f}%)</h3>", unsafe_allow_html=True)
                st.markdown(f"<h3>🔴 對手預期收益: {opp_net:.0f} (ROI: {opp_roi:.1f}%)</h3>", unsafe_allow_html=True)
                st.info(f"📈 **預期 GDP:** `{game.gdp:.0f} ➔ {c_est_gdp:.0f}` ({c_gdp_pct:+.2f}%)")

            if opp_plan:
                st.markdown("---")
                ui_core.render_proposal_component('📜 對手 (執行系統) 既有草案參考', opp_plan, game, view_party, cfg)

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
                    ui_core.render_proposal_component('⚖️ 監管系統草案' if key=='R' else '🛡️ 執行系統草案', plan, game, view_party, cfg)
                    if st.button(f"✅ 選擇此方案", key=f"pick_{key}", use_container_width=True):
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            ui_core.render_proposal_component('📜 待覆議草案內容', game.p1_selected_plan, game, view_party, cfg)
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("✅ 同意法案", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **【快訊】預算案三讀通過！** 歷經 {game.proposal_count} 輪黨團協商，雙方正式簽署法案。"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            
            if c2.button("❌ 拒絕並重談", use_container_width=True):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()
            
            if c3.button(f"🔄 同意但換位\n(警告: 各付 {penalty_amt} 給第三政黨)", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "執政權轉移！")
                game.proposing_party = game.ruling_party; st.rerun()
            
            if game.proposing_party.name == game.h_role_party.name:
                if c4.button("💥 逼迫最終提案 (最後通牒)", use_container_width=True):
                    st.session_state.news_flash = f"🗞️ **【快訊】執行系統下達最後通牒！** {view_party.name} 逼迫監管系統只能再提最後一次案！"
                    game.p1_step = 'ultimatum_draft_r'; game.proposing_party = game.r_role_party; st.rerun()

    elif game.p1_step == 'ultimatum_resolve_h':
        st.markdown("### 🚨 最終方案決斷 (執行系統專屬)")
        if view_party.name != game.h_role_party.name: 
            st.warning(f"⏳ 等待執行系統 {game.h_role_party.name} 決斷...")
        else:
            ui_core.render_proposal_component('📜 監管系統最終底線/通牒方案', game.p1_selected_plan, game, view_party, cfg)
            c1, c2 = st.columns(2)
            if c1.button("✅ 忍辱負重 (接受通牒)", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **【快訊】通牒生效！** 執行系統妥協吞下底線方案。"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button(f"🔄 掀桌倒閣換位\n(警告: 各付 {penalty_amt} 給第三政黨)", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "掀桌倒閣！")
                game.proposing_party = game.r_role_party; st.rerun()
