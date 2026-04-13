# ==========================================
# phase1.py
# 負責 第一階段 (提案與談判) 的 UI 與邏輯
# ==========================================
import streamlit as st
import engine
import ui_core

def render(game, view_party, cfg):
    penalty_amt = int(game.gdp * cfg['TRUST_BREAK_PENALTY_RATIO'])
    st.subheader(f"🤝 Phase 1: 監管系統委託執行系統建設提案 (輪數: {game.proposal_count})")
    
    if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_draft_r']:
        active_role = 'R' if game.p1_step in ['draft_r', 'ultimatum_draft_r'] else 'H'
        
        if game.p1_step == 'ultimatum_draft_r':
            st.error("🚨 **最後通牒啟動中：** 監管系統必須擬定最終裁決草案！")
            
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手公布草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({'監管系統' if active_role == 'R' else '執行系統'}黨) 草案擬定室")
            
            c_decay, c_gdp = st.columns(2)
            with c_decay: claimed_decay = st.number_input("公告衰退值", value=float(view_party.current_forecast), step=0.01)

            max_c = float(game.budget_t)
            c_funds = st.slider("投標資金 (C) (最高不超過當年總預算)", 0.0, max_c, min(max_c, 1000.0), 10.0)
            d_cost = st.slider("標案實質成本 (D) (備註:留點賺頭給對手)", 0.0, float(c_funds * 2), float(c_funds * 0.8), 10.0)
            
            plan_dict = {
                'claimed_decay': claimed_decay, 'c_funds': c_funds, 'd_cost': d_cost, 'author': active_role
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
            ui_core.render_proposal_component('📜 當前草案預覽', plan_dict, game, view_party, cfg)

            opp_role = 'H' if active_role == 'R' else 'R'
            opp_plan = game.p1_proposals.get(opp_role)
            if opp_plan:
                st.markdown("---")
                ui_core.render_proposal_component('📜 對手 (執行系統) 既有草案參考', opp_plan, game, view_party, cfg)

    elif game.p1_step == 'voting_pick':
        st.markdown(f"### 🗳️ 執政黨定奪 ({game.ruling_party.name})")
        if view_party.name != game.ruling_party.name:
            st.warning("⏳ 等待執政黨定奪...")
        else:
            for idx, key in enumerate(['R', 'H']):
                plan = game.p1_proposals.get(key)
                if plan is None: st.info("等待對方發布草案..."); continue
                st.markdown("---")
                ui_core.render_proposal_component('⚖️ 監管系統草案' if key=='R' else '🛡️ 執行系統草案', plan, game, view_party, cfg)
                if st.button(f"✅ 選擇此方案", key=f"pick_{key}"):
                    game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                    game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            ui_core.render_proposal_component('📜 待覆議草案內容', game.p1_selected_plan, game, view_party, cfg)
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("✅ 同意法案", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **【快訊】預算案三讀通過！** 歷經 {game.proposal_count} 輪黨團協商，雙方正式簽署法案。"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            
            if c2.button("❌ 拒絕並重談", use_container_width=True):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()
            
            if c3.button(f"🔄 同意但換位\n(各付 {penalty_amt})", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "執政權轉移！")
                game.proposing_party = game.ruling_party; st.rerun()
            
            if game.proposing_party.name == game.h_role_party.name:
                if c4.button("💥 逼迫最終提案 (通牒)", use_container_width=True):
                    st.session_state.news_flash = f"🗞️ **【快訊】執行系統下達最後通牒！** {view_party.name} 逼迫監管系統只能再提最後一次案！"
                    game.p1_step = 'ultimatum_draft_r'; game.proposing_party = game.r_role_party; st.rerun()

    elif game.p1_step == 'ultimatum_resolve_h':
        st.markdown("### 🚨 最終方案決斷 (執行系統專屬)")
        if view_party.name != game.h_role_party.name: 
            st.warning(f"⏳ 等待執行系統 {game.h_role_party.name} 決斷...")
        else:
            ui_core.render_proposal_component('📜 監管系統最終底線/通牒方案', game.p1_selected_plan, game, view_party, cfg)
            st.markdown("---")
            c1, c2 = st.columns(2)
            if c1.button("✅ 忍辱負重 (接受通牒)", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **【快訊】通牒生效！** 執行系統妥協吞下底線方案。"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button(f"🔄 掀桌倒閣換位\n(警告: 各付 {penalty_amt})", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "掀桌倒閣！")
                game.proposing_party = game.r_role_party; st.rerun()
