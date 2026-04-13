# ==========================================
# phase1.py
# ==========================================
import streamlit as st
import engine
import ui_core

def render(game, view_party, cfg):
    penalty_amt = int(game.gdp * cfg['TRUST_BREAK_PENALTY_RATIO'])
    st.subheader(f"🤝 Phase 1: 監管系統委託執行系統建設提案 (輪數: {game.proposal_count})")
    
    if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_draft_r']:
        active_role = 'R' if game.p1_step in ['draft_r', 'ultimatum_draft_r'] else 'H'
        
        if game.p1_step == 'ultimatum_draft_r': st.error("🚨 **最後通牒啟動中：** 必須擬定最終裁決草案！")
            
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手公布草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({'監管系統' if active_role == 'R' else '執行系統'}黨) 草案擬定室")
            
            c_decay, c_gdp = st.columns(2)
            with c_decay: claimed_decay = st.number_input("公告衰退值", value=float(view_party.current_forecast), step=0.01)
            with c_gdp: t_gdp_growth = st.number_input("目標 GDP 成長率 (%)", value=0.0, step=0.5)

            max_c = float(game.budget_t)
            c_funds = st.slider("標案總資金 (最高不超過當年總預算)", 0.0, max_c, min(max_c, 1000.0), 10.0)
            
            # 資金分配拉桿
            r_pays = st.slider("監管出資調整", 0, int(c_funds), int(c_funds * 0.5))
            h_pays = c_funds - r_pays
            r_pct = (r_pays / max(1, c_funds)) * 100 if c_funds > 0 else 0
            h_pct = (h_pays / max(1, c_funds)) * 100 if c_funds > 0 else 0
            st.markdown(f"**監管出資: {r_pays} ({r_pct:.1f}%) / 總額: {c_funds} / 執行出資: {h_pays} ({h_pct:.1f}%)**")

            d_cost = st.slider("標案實質成本 (備註:留點賺頭給對手)", 0.0, float(c_funds * 2), float(c_funds * 0.8), 10.0)
            
            plan_dict = {
                'claimed_decay': claimed_decay, 'target_gdp_growth': t_gdp_growth,
                'c_funds': c_funds, 'd_cost': d_cost, 'r_pays': r_pays, 'h_pays': h_pays, 'author': active_role
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
                    st.session_state.news_flash = f"🗞️ **【快訊】監管系統下達最後通牒！** {view_party.name} 逼迫執行系統接受此案！"
                    st.rerun()
                
                swap_cost = 0 if view_party.name == game.ruling_party.name else penalty_amt
                if c_btn3.button(f"🔄 強制通過並換位 (費用: {swap_cost})", use_container_width=True):
                    st.session_state.turn_data.update(plan_dict)
                    engine.trigger_swap(game, swap_cost, "監管系統強制接管！")
                    game.proposing_party = game.ruling_party; st.rerun()

            st.markdown("---")
            ui_core.render_proposal_component('📜 當前草案預覽', plan_dict, game, view_party, cfg)
            
            opp_role = 'H' if active_role == 'R' else 'R'
            opp_plan = game.p1_proposals.get(opp_role)
            if opp_plan:
                st.markdown("---")
                ui_core.render_proposal_component('📜 對手既有草案參考', opp_plan, game, view_party, cfg)

    elif game.p1_step == 'voting_pick':
        st.markdown(f"### 🗳️ 執政黨定奪 ({game.ruling_party.name})")
        if view_party.name != game.ruling_party.name:
            st.warning("⏳ 等待執政黨定奪...")
        else:
            for key in ['R', 'H']:
                plan = game.p1_proposals.get(key)
                if plan:
                    ui_core.render_proposal_component(f"{'⚖️ 監管' if key=='R' else '🛡️ 執行'}系統草案", plan, game, view_party, cfg)
                    if st.button(f"✅ 選擇此方案", key=f"pick_{key}"):
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            ui_core.render_proposal_component('📜 待覆議草案內容', game.p1_selected_plan, game, view_party, cfg)
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("✅ 同意法案", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.anim = 'balloons'
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button("❌ 拒絕並重談", use_container_width=True):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()
            if c3.button(f"🔄 同意但換位\n(各付 {penalty_amt})", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "執政權轉移！")
                game.proposing_party = game.ruling_party; st.rerun()
            if game.proposing_party.name == game.h_role_party.name:
                if c4.button("💥 逼迫最終提案 (通牒)", use_container_width=True):
                    game.p1_step = 'ultimatum_draft_r'; game.proposing_party = game.r_role_party; st.rerun()

    elif game.p1_step == 'ultimatum_resolve_h':
        st.markdown("### 🚨 最終方案決斷 (執行系統專屬)")
        if view_party.name != game.h_role_party.name: st.warning(f"⏳ 等待執行系統決斷...")
        else:
            ui_core.render_proposal_component('📜 監管系統最終底線/通牒方案', game.p1_selected_plan, game, view_party, cfg)
            c1, c2 = st.columns(2)
            if c1.button("✅ 忍辱負重 (接受通牒)", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.anim = 'balloons'
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button(f"🔄 掀桌倒閣換位\n(各付 {penalty_amt})", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "掀桌倒閣！")
                game.proposing_party = game.r_role_party; st.rerun()
