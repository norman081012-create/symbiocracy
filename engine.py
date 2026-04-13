# ==========================================
# engine.py
# ==========================================
import random
import streamlit as st

class Party:
    def __init__(self, name, cfg):
        self.name = name; self.wealth = cfg['INITIAL_WEALTH']; self.support = 50.0 
        self.build_ability = cfg['ABILITY_DEFAULT']; self.investigate_ability = cfg['ABILITY_DEFAULT']
        self.edu_ability = cfg['ABILITY_DEFAULT']; self.media_ability = cfg['ABILITY_DEFAULT']
        self.predict_ability = cfg['ABILITY_DEFAULT']; self.stealth_ability = cfg['ABILITY_DEFAULT']
        
        self.invest_pools = {'build': 0.0, 'inv': 0.0, 'edu': 0.0, 'media': 0.0, 'pre': 0.0, 'stl': 0.0}
        self.current_forecast = 0.0
        self.poll_history = {'小型': [], '中型': [], '大型': []}; self.latest_poll = None; self.poll_count = 0
        self.last_acts = {}

class GameEngine:
    def __init__(self, cfg):
        self.year = 1
        self.party_A = Party(cfg['PARTY_A_NAME'], cfg); self.party_B = Party(cfg['PARTY_B_NAME'], cfg)
        self.gdp = cfg['CURRENT_GDP']
        self.budget_t = self.gdp * cfg['TAX_RATE']
        self.pending_payouts = {'H': 0.0, 'R': 0.0, 'R_residual': 0.0}
        
        self.phase = 1; self.p1_step = 'draft_r'; self.p1_proposals = {'R': None, 'H': None}; self.p1_selected_plan = None
        self.ruling_party = self.party_A; self.r_role_party = self.party_A; self.h_role_party = self.party_B  
        self.sanity = cfg['SANITY_DEFAULT']; self.emotion = cfg['EMOTION_DEFAULT']
        self.current_real_decay = 0.0
        self.proposal_count = 1; self.proposing_party = self.party_A
        self.history = []; self.swap_triggered_this_year = False
        self.last_year_report = None

    def record_history(self, is_election):
        self.history.append({
            'Year': self.year, 'GDP': self.gdp, 'Sanity': self.sanity, 'Emotion': self.emotion,
            'A_Support': self.party_A.support, 'B_Support': self.party_B.support,
            'A_Wealth': self.party_A.wealth, 'B_Wealth': self.party_B.wealth,
            'Is_Election': is_election, 'Is_Swap': self.swap_triggered_this_year
        })

def trigger_swap(game, penalty_amt, msg_prefix="政局動盪！"):
    game.party_A.wealth -= penalty_amt; game.party_B.wealth -= penalty_amt
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True
    game.emotion = min(100.0, game.emotion + 30.0) 
    st.session_state.news_flash = f"🗞️ **【快訊】{msg_prefix}** 雙方被迫捐款 {penalty_amt}，觸發換位！"
    st.session_state.anim = 'snow'
    game.phase = 2
