# phase1.py
import streamlit as st
import formulas
import engine
import ui_core

def render(game, view_party, cfg):
    penalty_amt = int(game.gdp * cfg['TRUST_BREAK_PENALTY_RATIO'])
    st.subheader(f"🤝 Phase 1: 監管系統委託執行系統建設提案")
    
    if game.p1_step in ['draft_r', 'draft_h']:
        active_role = 'R' if game.p1_step == 'draft_r' else 'H'
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手公布草案...")
        else:
            st.markdown(f"#### 📝 {view_party.name} ({'監管系統' if active_role == 'R' else '執行系統'}黨) 草案擬定室")
            
            c_decay, c_funds = st.columns(2)
            with c_decay:
                claimed_decay = st.number_input("公告衰退值", value=float(view_party.current_forecast), step=0.01)
            with c_funds:
                max_c = float(game.budget_t)
                c_funds = st.slider("投標資金 (最高不超過當年總預算)", 0.0, max_c, min(max_c, 1000.0), 10.0)
            
            d_cost = st.slider("標案實質成本 (備註:留點賺頭給對手)", 0.0, float(c_funds * 2), float(c_funds * 0.8), 10.0)
            
            plan_dict = {
                'claimed_decay': claimed_decay, 'c_funds': c_funds, 'd_cost': d_cost, 'author': active_role
            }
            
            if st.button("📤 送出常規草案", use_container_width=True, type="primary"):
                game.p1_proposals[active_role] = plan_dict
                if game.p1_step == 'draft_r': game.p1_step = 'draft_h'; game.proposing_party = game.h_role_party
                else: game.p1_step = 'voting_pick'; game.proposing_party = game.ruling_party
                st.rerun()

            st.markdown("---")
            ui_core.render_proposal_component('📜 當前草案預覽', plan_dict, game, view_party, cfg)
            
            opp_role = 'H' if active_role == 'R' else 'R'
            opp_plan = game.p1_proposals.get(opp_role)
            if opp_plan:
                st.markdown("---")
                ui_core.render_proposal_component('📜 對手既有草案參考', opp_plan, game, view_party, cfg)

    elif game.p1_step == 'voting_pick':
        if view_party.name != game.ruling_party.name:
            st.warning("⏳ 等待執政黨定奪...")
        else:
            for key in ['R', 'H']:
                plan = game.p1_proposals.get(key)
                if plan:
                    ui_core.render_proposal_component(f"{key}草案", plan, game, view_party, cfg)
                    if st.button(f"✅ 選擇 {key} 方案", key=f"pick_{key}"):
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            ui_core.render_proposal_component('📜 待覆議草案內容', game.p1_selected_plan, game, view_party, cfg)
            if st.button("✅ 同意法案", type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
