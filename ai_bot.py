# ==========================================
# ai_bot.py (The Symbiocracy AI Engine)
# ==========================================
import random
import formulas
import streamlit as st

def take_turn(game, cfg):
    ai_party = game.party_A if game.party_A.name == game.ai_party_name else game.party_B
    is_h = (game.h_role_party.name == ai_party.name)
    active_role = 'H' if is_h else 'R'

    if game.phase == 1:
        if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_draft_r']:
            total_bonus = game.total_budget * ((cfg['BASE_INCOME_RATIO'] * 2) + cfg['RULING_BONUS_RATIO'])
            max_proj = max(10.0, float(game.total_budget) - total_bonus)
            unit_cost = formulas.calc_unit_cost(cfg, game.gdp, ai_party.build_ability, ai_party.current_forecast)

            my_projects = ai_party.projects
            if is_h:
                selected_projects = sorted(my_projects, key=lambda x: x['ev'], reverse=True)[:2]
                proj_fund = max_proj * random.uniform(0.7, 0.9) 
                bid_cost = sum(p['ev'] for p in selected_projects)
                req_cost = bid_cost * unit_cost
                r_pays = min(req_cost * random.uniform(0.2, 0.4), max_proj)
                fine_mult = 0.3 
            else:
                selected_projects = sorted(my_projects, key=lambda x: x['ev'])[:3]
                proj_fund = max_proj * random.uniform(0.2, 0.4) 
                bid_cost = sum(p['ev'] for p in selected_projects)
                req_cost = bid_cost * unit_cost
                r_pays = 0.0 
                fine_mult = random.uniform(0.8, 1.5) 

            plan = {
                'proj_fund': proj_fund, 'bid_cost': bid_cost,
                'r_pays': r_pays, 'h_pays': max(0.0, req_cost - r_pays),
                'claimed_decay': ai_party.current_forecast, 'claimed_cost': unit_cost,
                'author': active_role, 'author_party': ai_party.name,
                'req_cost': req_cost, 'fine_mult': fine_mult,
                'selected_projects': selected_projects
            }

            if game.p1_step == 'ultimatum_draft_r':
                game.p1_selected_plan = plan
                game.p1_step = 'ultimatum_resolve_h'
                game.proposing_party = game.h_role_party
            else:
                game.p1_proposals[active_role] = plan
                if game.p1_step == 'draft_r':
                    game.p1_step = 'draft_h'
                    game.proposing_party = game.h_role_party
                else:
                    game.p1_step = 'voting_pick'
                    game.proposing_party = game.ruling_party

        elif game.p1_step == 'voting_pick':
            my_draft = game.p1_proposals.get(active_role)
            if not my_draft: my_draft = game.p1_proposals.get('H' if active_role == 'R' else 'R')
            game.p1_selected_plan = my_draft
            game.p1_step = 'voting_confirm'
            game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A

        elif game.p1_step in ['voting_confirm', 'ultimatum_resolve_h']:
            if game.p1_step == 'voting_confirm' and game.proposal_count < 3 and random.random() < 0.4:
                game.proposal_count += 1
                game.p1_step = 'draft_r'
                game.proposing_party = game.r_role_party
                st.session_state.news_flash = f"🗞️ **[BREAKING]** {ai_party.name} rejected the draft. Renegotiation started."
            else:
                st.session_state.turn_data.update(game.p1_selected_plan)
                
                for np_proj in game.p1_selected_plan.get('selected_projects', []):
                    if not any(ap['id'] == np_proj['id'] for ap in game.active_projects):
                        game.active_projects.append(np_proj)
                        
                game.phase = 2
                game.proposing_party = game.ruling_party
                st.session_state.news_flash = f"🗞️ **[BREAKING]** {ai_party.name} accepted the draft. Bill passed!"

    elif game.phase == 2:
        d = st.session_state.get('turn_data', {})
        bid_cost = float(d.get('bid_cost', 1.0))
        selected_projects = d.get('selected_projects', [])
        
        inv_cap = int(ai_party.investigate_ability * 10 * (1.2 if not is_h else 1.0))
        ci_cap = int(ai_party.stealth_ability * 10)
        med_cap = int(ai_party.media_ability * 10 * (1.2 if not is_h else 1.0))
        tt_cap = int(ai_party.predict_ability * 10.0)
        
        my_acts = {
            'alloc_tt_dec': float(int(tt_cap * 0.33)), 'alloc_tt_obs': float(int(tt_cap * 0.33)), 'alloc_tt_opt': float(int(tt_cap * 0.34)),
            'alloc_inv_censor': 0.0, 'alloc_inv_audit': 0.0, 'alloc_inv_fin': 0.0,
            'alloc_ci_anticen': 0.0, 'alloc_ci_hideorg': 0.0, 'alloc_ci_hidefin': 0.0,
            'alloc_med_camp': float(int(med_cap * 0.5)), 'alloc_med_incite': 0.0, 'alloc_med_control': float(int(med_cap * 0.5)), 'alloc_med_edu': 0.0,
            'edu_stance': ai_party.edu_stance, 'fake_ev': 0.0,
            't_pre': ai_party.predict_ability, 't_inv': ai_party.investigate_ability,
            't_med': ai_party.media_ability, 't_bld': ai_party.build_ability,
            'invest_wealth': 0.0, 'c_net': 0.0, 'allocations': {}
        }

        unit_cost = formulas.calc_unit_cost(cfg, game.gdp, ai_party.build_ability, game.current_real_decay)
        maint_ev = sum([ai_party.predict_ability, ai_party.investigate_ability, ai_party.media_ability, ai_party.stealth_ability, ai_party.build_ability]) * 5.0
        eng_base_ev = ai_party.build_ability * 10 * (1.2 if is_h else 1.0)

        if is_h:
            my_acts['alloc_ci_hidefin'] = float(ci_cap)
            
            c_net = bid_cost
            fake_ev_total = bid_cost * random.uniform(0.1, 0.3) if random.random() < 0.4 else 0.0
            
            allocations = {}
            avail_ev_real = c_net
            avail_ev_fake = fake_ev_total
            
            for p in game.active_projects:
                invested = sum(inv.get('real', inv['amount']) + inv.get('fake', 0.0) for inv in p.get('investments', []))
                remaining = max(0.0, p['ev'] - invested)
                min_req = remaining * 0.2
                
                # AI tries to fund min req, evenly splitting real and fake if possible
                alloc_real = min(avail_ev_real, min_req * 1.5)
                alloc_fake = min(avail_ev_fake, min_req * 0.5) 
                
                allocations[p['id']] = {'real': alloc_real, 'fake': alloc_fake}
                avail_ev_real -= alloc_real
                avail_ev_fake -= alloc_fake
                
            my_acts['allocations'] = allocations
            my_acts['fake_ev'] = fake_ev_total
            my_acts['c_net'] = c_net

            total_ev_req = c_net + (fake_ev_total * cfg.get('FAKE_EV_COST_RATIO', 0.2)) + maint_ev
            ev_to_buy = max(0.0, total_ev_req - eng_base_ev)
            my_acts['invest_wealth'] = ev_to_buy * max(0.01, unit_cost / 1.2)
        else:
            my_acts['alloc_inv_fin'] = float(inv_cap)
            
            total_ev_req = maint_ev
            ev_to_buy = max(0.0, total_ev_req - eng_base_ev)
            my_acts['invest_wealth'] = ev_to_buy * max(0.01, unit_cost)

        st.session_state[f"{ai_party.name}_acts"] = my_acts

        opp_name = game.human_party_name
        if f"{opp_name}_acts" not in st.session_state:
            game.proposing_party = game.party_A if game.party_A.name == opp_name else game.party_B
        else:
            game.phase = 3
            game.proposing_party = game.r_role_party
