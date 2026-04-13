# ==========================================
# engine.py
# ==========================================
import random
import streamlit as st

class Department:
    def __init__(self, eff):
        self.eff = eff
        self.target = eff
        self.invested = 0.0

class Party:
    def __eq__(self, other): return self.name == other.name if hasattr(other, 'name') else False
    def __init__(self, name, cfg):
        self.name = name; self.wealth = cfg['INITIAL_WEALTH']; self.support = 50.0 
        self.depts = {
            'build': Department(cfg['EFF_DEFAULT']), 'investigate': Department(cfg['EFF_DEFAULT']),
            'edu': Department(cfg['EFF_DEFAULT']), 'media': Department(cfg['EFF_DEFAULT']),
            'predict': Department(cfg['EFF_DEFAULT']), 'stealth': Department(cfg['EFF_DEFAULT'])
        }
        self.current_forecast = 0.0; self.latest_poll = None; self.poll_count = 0
        self.poll_history = {'小型': [], '中型': [], '大型': []}
        self.last_acts = {'policy': 0, 'legal': 0, 'maint': 0}

class GameEngine:
    def __init__(self, cfg):
        self.year = 1
        self.party_A = Party(cfg['PARTY_A_NAME'], cfg); self.party_B = Party(cfg['PARTY_B_NAME'], cfg)
        self.gdp = cfg['CURRENT_GDP']
        self.pending_payouts = {'A': 0.0, 'B': 0.0} # 儲存明年初要發放的錢
        
        self.phase = 1; self.p1_step = 'draft_r' 
        self.p1_proposals = {'R': None, 'H': None}; self.p1_selected_plan = None
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
        self.swap_triggered_this_year = False

def execute_poll(game, view_party, cost):
    view_party.wealth -= cost
    error_margin = max(0.0, 15.0 - (view_party.depts['predict'].eff * 0.2) - (cost * 0.4))
    a_poll = max(0.0, min(100.0, game.party_A.support + random.uniform(-error_margin, error_margin)))
    poll_type = '小型' if cost == 5 else '中型' if cost == 10 else '大型'
    game.party_A.latest_poll = a_poll; game.party_A.poll_history[poll_type].append(a_poll)
    game.party_B.latest_poll = 100.0 - a_poll; game.party_B.poll_history[poll_type].append(100.0 - a_poll)
    view_party.poll_count += 1

def trigger_swap(game, penalty_amt, msg_prefix="政局動盪！"):
    game.party_A.wealth -= penalty_amt; game.party_B.wealth -= penalty_amt
    game.h_role_party, game.r_role_party = game.r_role_party, game.h_role_party
    game.swap_triggered_this_year = True
    game.emotion = min(100.0, game.emotion + 30.0) 
    st.session_state.news_flash = f"🗞️ **【快訊】{msg_prefix}** 雙方被迫各強制捐款 {penalty_amt} 資金給第三政黨，觸發換位！"
    st.session_state.anim = 'snow'
    game.phase = 2
