# ==========================================
# config.py
# ==========================================
import i18n
t = i18n.t

DEFAULT_CONFIG = {
    'CALENDAR_NAME': "Era", 'PARTY_A_COLOR': "#2E8B57", 'PARTY_B_COLOR': "#4169E1",
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'CROWN_WINNER': "👑 Ruling", 'CROWN_LOSER': "🎯 Candidate",
    'INITIAL_WEALTH': 1000.0, 'END_YEAR': 12,
    
    'DECAY_MIN': 0.1, 'DECAY_MAX': 1.0,  
    'DECAY_WEIGHT_MULT': 0.05,
    'BASE_DECAY_RATE': 0.0,
    
    'DECAY_AMOUNT_DEFAULT': 1500.0,
    'DECAY_AMOUNT_BUILD': 500.0,
    
    'CATCH_RATE_PER_PERCENT': 0.02,
    'CRONY_CATCH_RATE_PER_PERCENT': 0.01,
    
    'RESISTANCE_MULT': 1.0, 
    'BUILD_DIFF': 1.0, 'INVESTIGATE_DIFF': 1.0, 'PREDICT_DIFF': 1.0, 'MEDIA_DIFF': 1.0,
    'CURRENT_GDP': 5000.0, 
    'GDP_INFLATION_DIVISOR': 10000.0, 
    'GDP_CONVERSION_RATE': 0.2,   
    'HEALTH_MULTIPLIER': 0.2, 
    'BASE_TOTAL_BUDGET': 0.0,  
    'BASE_INCOME_RATIO': 0.05,    
    'RULING_BONUS_RATIO': 0.10,   
    'H_FUND_DEFAULT': 600.0, 
    'H_MEDIA_BONUS': 1.2, 'R_INV_BONUS': 1.2,
    'CORRUPTION_PENALTY': 2.0,
    'MAX_ABILITY': 10.0, 
    'ABILITY_DEFAULT': 3.0,          
    'BUILD_ABILITY_DEFAULT': 3.0, # 🚀 Fix: Engineering initial value lowered back to 30%
    'MAINTENANCE_RATE': 10.0,        
    'TRUST_BREAK_PENALTY_RATIO': 0.05,
    'ELECTION_CYCLE': 4,
    'SANITY_DEFAULT': 50.0,   
    'EMOTION_DEFAULT': 30.0,
    
    'CLAIMED_DECAY_WEIGHT': 0.2,
    'AMMO_MULTIPLIER': 50.0,
    'MAX_UPGRADE_SPEED': 20.0,
    'UPGRADE_COST_MULT': 0.15, # 🚀 Fix: Increase quadratic upgrade base cost
    
    'PREDICT_ACCURACY_WEIGHT': 0.8,     # 🚀 Added: Think Tank prediction accuracy weight
    'INVESTIGATE_ACCURACY_WEIGHT': 0.8, # 🚀 Added: Intel observation accuracy weight
    
    'PERF_IMPACT_BASE': 1000.0,
    'OBS_ERR_BASE': 0.7,      
}

def get_config_translations():
    return {
        'DECAY_MIN': "Min Decay Rate", 'DECAY_MAX': "Max Decay Rate",  
        'DECAY_WEIGHT_MULT': "Decay GDP Weight (Default 0.05)", 'BASE_DECAY_RATE': "Base Decay Floor",
        'CATCH_RATE_PER_PERCENT': "Corruption Base Catch Rate per %", 'CRONY_CATCH_RATE_PER_PERCENT': "Cronyism Base Catch Rate per %",
        'CLAIMED_DECAY_WEIGHT': "Expected Gap Impact Weight", 'AMMO_MULTIPLIER': "Perf to Support Pts Multiplier",
        'PREDICT_ACCURACY_WEIGHT': "Think Tank Prediction Accuracy Weight", 'INVESTIGATE_ACCURACY_WEIGHT': "Intel Observation Accuracy Weight"
    }
    
def get_intel_market_eval(unit_cost):
    if unit_cost < 0.8: return "🌟 Extremely Undervalued Market (Overcapacity, absolute construction bonus phase)"
    elif unit_cost < 1.2: return "🟢 Stable Market Quote (Supply/Demand balanced, construction cost matches expectations)"
    elif unit_cost < 1.8: return "🟡 Inflation Premium Emerging (Materials and labor tight, costs rising)"
    elif unit_cost < 2.5: return "🔴 Market Overheating Alert (High systemic resistance, heavy budget consumption)"
    else: return "💀 Structural Economic Deterioration (Destructive inflation, pause non-essential dev recommended)"

def get_economic_forecast_text(drop_val):
    if drop_val <= 10.0: return "🌟 Economic Boom (Minor Drop): Market is vibrant, private consumption strong!"
    elif drop_val <= 30.0: return "📈 Steady Growth (Manageable Drop): Smooth economic transition, investment confidence okay."
    elif drop_val <= 50.0: return "⚖️ Economic Slowdown (Recession Risk): Corporate investments turning conservative, handle downside risks."
    elif drop_val <= 70.0: return "📉 Recession Alert (Widespread Depression): Factories laying off, consumption frozen, domestic demand boost needed!"
    else: return "⚠️ Economic Storm (Systemic Collapse): Financial tsunami sweeps nation, bankruptcy wave, country on the edge!"

def get_civic_index_text(score):
    if score < 15: return f"Highly Susceptible ({score:.1f})"
    elif score < 30: return f"Susceptible ({score:.1f})"
    elif score < 45: return f"Mildly Susceptible ({score:.1f})"
    elif score < 60: return f"Moderately Rational ({score:.1f})"
    elif score < 75: return f"Slightly Critical ({score:.1f})"
    elif score < 90: return f"Mature Critical Thinker ({score:.1f})"
    else: return f"Highly Independent Thinker ({score:.1f})"

def get_emotion_text(emotion_val):
    if emotion_val < 20: return f"Stable and Calm ({emotion_val:.1f})"
    elif emotion_val < 50: return f"Slightly Restless ({emotion_val:.1f})"
    elif emotion_val < 80: return f"Aroused Public Anger ({emotion_val:.1f})"
    else: return f"Frenzied ({emotion_val:.1f})"

def get_election_icon(year, cycle):
    rem = year % cycle
    if rem == 1: return "🗳️ Election Year"
    elif rem == 2: return "🌱 Year 1 of Term"
    elif rem == cycle - 1: return "⏳ 2 Years to Election"
    elif rem == 0: return "🚨 Election Next Year"
    else: return f"{cycle - rem + 1} Years to Election"

def get_party_logo(name):
    if name == "Prosperity": return "🦅"
    elif name == "Equity": return "🤝"
    return "🚩"

def get_thinktank_eval(ability, diff):
    abi_lvl = "high" if ability >= 7 else "med" if ability >= 4 else "low"
    acc_lvl = "high" if diff <= 5.0 else "med" if diff <= 15.0 else "low" 
    matrix = {
        ('high', 'high'): "Top-tier execution, perfect prediction", ('high', 'med'): "Slight deviation, strategically controllable", ('high', 'low'): "Black Swan event! Failed to foresee drastic change",
        ('med', 'high'): "Overperforming, accurate hit", ('med', 'med'): "Standard, error within expectations", ('med', 'low'): "Severe misjudgment, upgrade recommended",
        ('low', 'high'): "Blind luck, luckily guessed correctly", ('low', 'med'): "Acceptable, low reference value", ('low', 'low'): "Completely dysfunctional, severely misleading decisions!"
    }
    return matrix.get((abi_lvl, acc_lvl), "Operating Abnormally")
