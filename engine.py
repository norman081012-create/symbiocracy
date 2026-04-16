# ==========================================
# engine.py
# ==========================================
import random
import streamlit as st
import i18n
t = i18n.t

class Party:
    def __eq__(self, other): return self.name == other.name if hasattr(other, 'name') else False
    def __init__(self, name, cfg):
        self.name = name
        self.wealth = cfg['INITIAL_WEALTH']
        self.support = 50.0 
        
        self.build_ability = cfg.get('BUILD_ABILITY_DEFAULT', 3.0)
        self.investigate_ability = cfg.get('ABILITY_DEFAULT', 3.0)
        self.media_ability = cfg.get('ABILITY_DEFAULT', 3.0)
        self.predict_ability = cfg.get('ABILITY_DEFAULT', 3.0)
        self.stealth_ability = cfg.get('ABILITY_DEFAULT', 3.0)
        self.edu_ability = cfg.get('EDU_ABILITY_DEFAULT', 3.0)
        self.edu_stance = 0.0 
        
        self.current_forecast = 0.0
        self.poll_history = {'Small': [], 'Medium': [], 'Large': []}
        self.latest_poll = None
        self.poll_count = 0
        self.last_acts = {}

class GameEngine:
    def __init__(self, cfg):
        self.year = 1
        self.party_A = Party(cfg['PARTY_A_NAME'], cfg)
        self.party_B = Party(cfg['PARTY_B_NAME'], cfg)
        self.gdp = cfg['CURRENT_GDP']
        self.total_budget = cfg['BASE_TOTAL_BUDGET'] + (self.gdp * cfg['HEALTH_MULTIPLIER'])
        self.h_fund = cfg['H_FUND_DEFAULT']
        
        self.phase = 1
        self.p1_step = 'draft_r' 
        self.p1_proposals = {'R': None, 'H': None}
        self.p1_selected_plan = None
        self.ruling_party = self.party_A
        self.r_role_party = self.party_A
        self.h_role_party = self.party_B  
        
        self.sanity = cfg['SANITY_DEFAULT']
        self.emotion = cfg['EMOTION_DEFAULT']
        self.current_real_decay = 0.0
        self.proposal_count = 1
        self.proposing_party = self.party_A
        self.history = []
        self.swap_triggered_this_year = False
        self.last_year_report = None
        
        self.boundary_B = 100 
        self.h_rigidity_buff = {'amount': 0.0, 'duration': 0, 'party': None}

    def record_history(self, is_election):
        self.history.append({
            'Year': self.year, 'GDP': self.gdp, 'Sanity': self.sanity, 'Emotion': self.emotion,
            'A_Support': self.party_A.support, 'B_Support': self.party_B.support,
            'A_Wealth': self.party_A.wealth, 'B_Wealth': self.party_B.wealth,
            'Is_Election': is_election, 'Is_Swap': self.swap_triggered_this_year,
            'Ruling': self.ruling_party.name, 'H_Party': self.h_role_party.name,
            'R_Party': self.r_role_party.name,
            'A_Edu': float(self.party_A.edu_stance),
            'B_Edu': float(self.party_B.edu_stance),
            'A_Avg_Abi': (self.party_A.build_ability + self.party_A.investigate_ability + self.party_A.media_ability + self.party_A.predict_ability + self.party_A.stealth_ability + self.party_A.edu_ability)/6,
            'B_Avg_Abi': (self.party_B.build_ability + self.party_B.investigate_ability + self.party_B.media_ability + self.party_B.predict_ability + self.party_B.stealth_ability + self.party_B.edu_ability)/6
        })
        self.swap_triggered_this_year = False

def execute_poll(game, view_party, cost):
    view_party.wealth -= cost
    error_margin = max(0.0, 15.0 - (view_party.predict_ability * 0.5) - (cost * 0.4))
    a_actual = game.party_A.support
    a_poll = max(0.0, min(100.0, a_actual + random.uniform(-error_margin, error_margin)))
    
    poll_type = 'Small' if cost == 5 else 'Medium' if cost == 10 else 'Large'
    game.party_A.latest_poll = a_poll
    game.party_A.poll_history[poll_type].append(a_poll)
    b_poll = 100.0 - a_poll
    game.party_B.latest_poll = b_poll
    game.party_B.poll_history[poll_type].append(b_poll)
    view_party.poll_count += 1

def trigger_swap(game, penalty_amt, msg_prefix="Political Turmoil!"):
    game.party_A.wealth -= penalty_amt; game.party_B.wealth -= penalty_amt
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True
    game.emotion = min(100.0, game.emotion + 30.0) 
    
    st.session_state.news_flash = f"🗞️ **[BREAKING] {msg_prefix}** Both parties forced to pay {penalty_amt:.1f} to charities, triggering an immediate Cabinet Swap!"
    st.session_state.anim = 'snow'
    game.phase = 2

