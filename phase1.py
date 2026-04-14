# ==========================================
# phase1.py
# ==========================================
import streamlit as st
import formulas
import engine
import ui_core
import ui_proposal
import i18n
t = i18n.t

def render(game, view_party, cfg):
    penalty_amt = int(game.total_budget * cfg['TRUST_BREAK_PENALTY_RATIO'])
    st.subheader(f"🤝 Phase 1: R-System Commissions H-System Proposal (Round: {game.proposal_count})")
    
    if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_draft_r']:
        active_role = 'R' if game.p1_step in ['draft_r', 'ultimatum_draft_r'] else 'H'
        
        if game.p1_step == 'ultimatum_draft_r':
            st.error("🚨 **Ultimatum Active:** R-System must draft final resolution!")
            
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ Waiting for opponent's draft...")
        else:
            role_text_en = 'R-System' if active_role == 'R' else 'H-System'
            
            c_title, c_btn = st.columns([0.8, 0.2])
            with c_title:
                st.markdown(f"#### 📝 {view_party.name} ({role_text_en}) Draft Room")
            
            opp_role = 'H' if active_role == 'R' else 'R'
            opp_plan = game.p1_proposals.get(opp_role)
            
            input_decay_key = f"ui_decay_val_{game.year}_{active_role}"
            input_cost_key = f"ui_cost_val_{game.year}_{active_role}"
            widget_decay_key = f"num_{input_decay_key}"
            widget_cost_key = f"num_{input_cost_key}"
            
            obs_abis = ui_core.get_observed_abilities(view_party, game.h_role_party, game, cfg)
            tt_decay = float(view_party.current_forecast)
            suggested_unit_cost = formulas.calc_unit_cost(cfg, game.gdp, obs_abis['build'], view_party.current_forecast)
            tt_cost = round(suggested_unit_cost, 2)
            
            if widget_decay_key not in st.session_state: st.session_state[widget_decay_key] = tt_decay
            if widget_cost_key not in st.session_state: st.session_state[widget_cost_key] = tt_cost

            with c_btn:
                if st.button("🔄 Auto-Fill Intel", use_container_width=True):
                    st.session_state[widget_decay_key] = tt_decay
                    st.session_state[widget_cost_key] = tt_cost
                    st.rerun()

            c_ann1, c_ann2 = st.columns(2)
            with c_ann1:
                opp_claimed_decay = opp_plan.get('claimed_decay') if opp_plan else None
                opp_txt1 = f"Opp. Claimed: {opp_claimed_decay:.3f}" if opp_claimed_decay is not None else "Awaiting Opp."
                
                current_val = st.session_state.get(widget_decay_key, tt_decay)
                conv_rate = cfg.get('GDP_CONVERSION_RATE', 0.2)
                gdp_loss = game.gdp * (current_val * cfg.get('DECAY_WEIGHT_MULT', 0.05) + cfg.get('BASE_DECAY_RATE', 0.0))
                req_infra_to_balance = gdp_loss / conv_rate
                
                st.markdown(f"**Claimed Decay (Current: {current_val:.3f}) (Equals {req_infra_to_balance:.1f} construction volume)** | {opp_txt1}")
                claimed_decay = st.number_input("Claimed Decay", step=0.001, min_value=0.0, key=widget_decay_key, label_visibility="collapsed")
                st.session_state[input_decay_key] = claimed_decay
                
            with c_ann2:
                opp_claimed_cost = opp_plan.get('claimed_cost') if opp_plan else None
                opp_txt2 = f"Opp. Claimed: {opp_claimed_cost:.2f}" if opp_claimed_cost is not None else "Awaiting Opp."
                st.markdown(f"**Claimed Unit Cost (Current: {st.session_state.get(widget_cost_key, tt_cost):.2f})** | {opp_txt2}")
                claimed_cost = st.number_input("Claimed Unit Cost", step=0.01, key=widget_cost_key, label_visibility="collapsed")
                st.session_state[input_cost_key] = claimed_cost
            
            max_budget = max(10.0, float(game.total_budget))
            
            def_proj = float(opp_plan.get('proj_fund', 0.0)) if opp_plan else 0.0
            def_bid = float(opp_plan.get('bid_cost', 0.0)) if opp_plan else 0.0
            def_rpays = float(opp_plan.get('r_pays', 0.0)) if opp_plan else 0.0
            
            proj_fund = st.slider("Total Plan Reward (Max=Budget)", 0.0, max_budget, def_proj, 10.0)
            bid_cost = st.slider("Plan Total Benefit (Construction Volume)", 0.0, max_budget * 1.5, def_bid, 10.0)
            r_pays = st.slider("💰 R-Pays (Subsidy from R-System)", 0.0, max_budget, def_rpays, 10.0)
            
            req_cost = bid_cost * claimed_cost
            h_pays = req_cost - r_pays
            
            is_invalid = False
            warning_msg = ""
            if proj_fund <= 0:
                is_invalid = True; warning_msg = "⚠️ Error: Reward must be > 0!"
            elif bid_cost <= 0:
                is_invalid = True; warning_msg = "⚠️ Error: Benefit must be > 0!"
            elif r_pays > req_cost:
                is_invalid = True; warning_msg = "⚠️ Error: R-Pays cannot exceed Total Req. Cost!"

            r_pct = (r_pays / max(1.0, req_cost)) * 100 if req_cost > 0 else 0
            h_pct = (h_pays / max(1.0, req_cost)) * 100 if req_cost > 0 else 0
            
            if is_invalid:
                st.error(warning_msg)
            else:
                st.markdown(f"<h4><span style='font-size: 1.2em; color: {cfg['PARTY_B_COLOR']}'>R-Pays: {r_pays:.1f} ({r_pct:.1f}%)</span> / Req. Cost: {req_cost:.1f} / <span style='font-size: 1.2em; color: {cfg['PARTY_A_COLOR']}'>H-Pays: {h_pays:.1f} ({h_pct:.1f}%)</span></h4>", unsafe_allow_html=True)
            
            plan_dict = {
                'proj_fund': proj_fund, 'bid_cost': bid_cost, 
                'r_pays': r_pays, 'h_pays': h_pays, 
                'claimed_decay': claimed_decay, 'claimed_cost': claimed_cost,
                'author': active_role, 'req_cost': req_cost
            }

            st.markdown("<br>", unsafe_allow_html=True)
            c_btn1, c_btn2, c_btn3 = st.columns(3)
            if c_btn1.button("📤 Submit Draft", use_container_width=True, type="primary", disabled=is_invalid):
                if game.p1_step == 'ultimatum_draft_r':
                    game.p1_selected_plan = plan_dict; game.p1_step = 'ultimatum_resolve_h'; game.proposing_party = game.h_role_party
                else:
                    game.p1_proposals[active_role] = plan_dict
                    if game.p1_step == 'draft_r': game.p1_step = 'draft_h'; game.proposing_party = game.h_role_party
                    else: game.p1_step = 'voting_pick'; game.proposing_party = game.ruling_party
                st.rerun()
                
            if active_role == 'R' and game.p1_step == 'draft_r':
                if c_btn2.button("💥 Issue Ultimatum", use_container_width=True, disabled=is_invalid):
                    game.p1_selected_plan = plan_dict
                    game.p1_step = 'ultimatum_resolve_h'
                    game.proposing_party = game.h_role_party
                    st.session_state.news_flash = f"🗞️ **[BREAKING] R-System Ultimatum!** {view_party.name} forces H-System to accept or trigger swap!"
                    st.rerun()
                
                swap_cost = 0 if view_party.name == game.ruling_party.name else penalty_amt
                if c_btn3.button(f"🔄 Force Pass & Swap (Cost: {swap_cost:.1f})", use_container_width=True, disabled=is_invalid):
                    st.session_state.turn_data.update(plan_dict)
                    engine.trigger_swap(game, swap_cost, "R-System Forced Takeover!")
                    game.proposing_party = game.ruling_party; st.rerun()

            if not is_invalid:
                st.markdown("---")
                ui_proposal.render_proposal_component('📜 Current Draft Preview', plan_dict, game, view_party, cfg)

            if opp_plan:
                st.markdown("---")
                ui_proposal.render_proposal_component('📜 Opponent Draft Ref.', opp_plan, game, view_party, cfg)

    elif game.p1_step == 'voting_pick':
        st.markdown(f"### 🗳️ Ruling Party Decision ({game.ruling_party.name})")
        if view_party.name != game.ruling_party.name:
            st.warning("⏳ Waiting for ruling party decision...")
        else:
            for idx, key in enumerate(['R', 'H']):
                plan = game.p1_proposals.get(key)
                if plan is None: st.info("Waiting for opponent draft..."); continue
                st.markdown("---")
                ui_proposal.render_proposal_component('⚖️ R-System Draft' if key=='R' else '🛡️ H-System Draft', plan, game, view_party, cfg)
                if st.button(f"✅ Select this draft", key=f"pick_{key}"):
                    game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                    game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ Waiting for opponent confirmation...")
        else:
            ui_proposal.render_proposal_component('📜 Draft to Confirm', game.p1_selected_plan, game, view_party, cfg)
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("✅ Agree to Bill", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"🗞️ **[BREAKING] Bill Passed!** After {game.proposal_count} rounds, bill is signed."
                st.session_state.anim = 'balloons'
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            
            if c2.button("❌ Reject & Renegotiate", use_container_width=True):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()
            
            if c3.button(f"🔄 Agree & Swap\n(Cost: {penalty_amt:.1f})", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "Power Shift!")
                game.proposing_party = game.ruling_party; st.rerun()
            
            if game.proposing_party.name == game.h_role_party.name:
                if c4.button("💥 Force Final (Ultimatum)", use_container_width=True):
                    st.session_state.news_flash = f"🗞️ **[BREAKING] H-System Ultimatum!** R-System has one last chance."
                    game.p1_step = 'ultimatum_draft_r'; game.proposing_party = game.r_role_party; st.rerun()

    elif game.p1_step == 'ultimatum_resolve_h':
        st.markdown("### 🚨 Final Decision (H-System Only)")
        if view_party.name != game.h_role_party.name: 
            st.warning(f"⏳ Waiting for H-System {game.h_role_party.name} decision...")
        else:
            ui_proposal.render_proposal_component('📜 R-System Final Ultimatum Draft', game.p1_selected_plan, game, view_party, cfg)
            st.markdown("---")
            c1, c2 = st.columns(2)
            if c1.button("✅ Accept Ultimatum", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = "🗞️ **[BREAKING] Ultimatum Accepted!** H-System compromises."
                st.session_state.anim = 'balloons'
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
                
            if c2.button(f"🔄 Flip Table & Swap\n(Warning: Cost {penalty_amt:.1f})", use_container_width=True):
                st.session_state.turn_data.update(game.p1_selected_plan)
                engine.trigger_swap(game, penalty_amt, "Cabinet Fall!")
                game.proposing_party = game.r_role_party; st.rerun()
