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
            
            c_decay, _ = st.columns(2)
            input_key = f"ui_decay_val_{game.year}_{active_role}"
            
            if input_key not in st.session_state: st.session_state[input_key] = float(view_party.current_forecast)
            
            with c_decay:
                opp_txt = f"對手公告: {opp_claimed:.2f}" if opp_claimed is not None else "等待對手公告"
                st.markdown(f"**公告衰退值 (當前: {st.session_state[input_key]:.2f})** | {opp_txt}")
                claimed_decay = st.number_input("公告衰退值", value=float(st.session_state[input_key]), step=0.01, key=f"num_{input_key}", label_visibility="collapsed")
                st.session_state[input_key] = claimed_decay
                
            c_funds = st.slider("投標資金 (最高不超過當年總預算)", 0.0, float(max(1.0, game.project_pool)), float(min(game.project_pool * 0.5, game.project_pool)), 10.0)
            c_diff = st.slider("標案實質成本 (備註:留點賺頭給對手)", 0.0, 3.0, 1.0, 0.1)

            # 計算預估值
            o_prev = formulas.calculate_preview(cfg, game, c_funds, c_diff, view_party.current_forecast, view_party)
            c_prev = formulas.calculate_preview(cfg, game, c_funds, c_diff, claimed_decay, view_party)

            plan_dict = {
                'c_funds': c_funds, 'c_diff': c_diff, 'claimed_decay': claimed_decay,
                'author': active_role,
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
                if c_btn3.button(f"🔄 強制接管並換位 (費用: {swap_cost})", use_container_width=True):
                    st.session_state.turn_data.update(plan_dict)
                    engine.trigger_swap(game, swap_cost, "監管系統強制接管！")
                    game.proposing_party = game.ruling_party; st.rerun()

            st.markdown("---")
            if opp_plan:
                # ====== 鎖死的智庫評估 UI ======
                st.markdown("### 📜 對手既有草案與智庫評估")
                opp_eval = formulas.calculate_preview(cfg, game, opp_plan['c_funds'], opp_plan['c_diff'], view_party.current_forecast, view_party)
                
                c_info, c_warn = st.columns([2, 1])
                with c_info:
                    st.markdown(f"**1. 我方預估專案回收:** {opp_eval['my_inc']:.0f} (ROI: {opp_eval['my_roi']:.1f}%)")
                    st.markdown(f"**2. 對方預估專案回收:** {opp_eval['opp_inc']:.0f} (ROI: {opp_eval['opp_roi'] if 'opp_roi' in opp_eval else 'N/A'})")
                    st.markdown(f"**3. 支持度預估:** {opp_eval['sup_shift']:+.2f}%")
                    st.markdown(f"📈 **4. 預期 GDP:** `{game.gdp:.0f} ➔ {opp_eval['est_gdp']:.0f}` ({opp_eval['gdp_pct']:+.2f}%)")
                with c_warn:
                    diff = abs(opp_plan['claimed_decay'] - view_party.current_forecast)
                    if diff < 0.1: icon, txt = "🟢", "智庫認為：對方估計十分誠實，符合預期"
                    elif diff < 0.3: icon, txt = "🟡", "智庫提醒：數值有落差，對方可能藏有私心"
                    else: icon, txt = "🔴", "智庫警告：對方隱瞞了極大風險！嚴重偏離現實"
                    st.markdown(f"**5. 衰退值差異:** \n\n{icon} {txt} \n*(公告 {opp_plan['claimed_decay']:.2f} vs 估值 {view_party.current_forecast:.2f})*")
                st.markdown("---")

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
                st.session_state.anim = 'balloons'
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
                st.session_state.anim = 'balloons'
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button(f"🔄 掀桌倒閣換位\n(警告: 各付 {penalty_amt} 給第三政黨)", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "掀桌倒閣！")
                game.proposing_party = game.r_role_party; st.rerun()
