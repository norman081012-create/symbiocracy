# ==========================================
# config.py
# ==========================================
import i18n
t = i18n.t

DEFAULT_CONFIG = {
    'CALENDAR_NAME': "Year", 'PARTY_A_COLOR': "#2E8B57", 'PARTY_B_COLOR': "#4169E1",
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
    'BUILD_ABILITY_DEFAULT': 6.0,    
    'MAINTENANCE_RATE': 10.0,        
    'TRUST_BREAK_PENALTY_RATIO': 0.05,
    'ELECTION_CYCLE': 4,
    'SANITY_DEFAULT': 50.0,   
    'EMOTION_DEFAULT': 30.0,
    'SUPPORT_CONVERSION_RATE': 0.05, 
    'PERF_IMPACT_BASE': 1000.0,
    'OBS_ERR_BASE': 0.7,      
    'CLAIMED_DECAY_WEIGHT': 0.2  
}

def get_config_translations():
    return {
        'DECAY_MIN': "Min Decay Rate", 'DECAY_MAX': "Max Decay Rate",  
        'DECAY_WEIGHT_MULT': "Decay GDP Weight (Default 0.05)", 'BASE_DECAY_RATE': "Base Decay Limit",
        'CATCH_RATE_PER_PERCENT': "Base Catch Rate per % Corruption", 'CRONY_CATCH_RATE_PER_PERCENT': "Base Catch Rate per % Cronyism",
    }
    
def get_intel_market_eval(unit_cost):
    if unit_cost < 0.8: return "🌟 Extremely Undervalued (Excess capacity, golden era for construction)"
    elif unit_cost < 1.2: return "🟢 Stable Market (Balanced supply/demand, costs as expected)"
    elif unit_cost < 1.8: return "🟡 Inflation Premium (Tight labor/materials, costs rising)"
    elif unit_cost < 2.5: return "🔴 Overheated Market (High systemic resistance, rapid budget burn)"
    else: return "💀 Structural Decay (Destructive inflation, pause non-essential development)"

def get_economic_forecast_text(drop_val):
    if drop_val <= 10.0: return "🌟 Excellent (Minimal decline)"
    elif drop_val <= 30.0: return "📈 Stable Growth (Controlled decline)"
    elif drop_val <= 50.0: return "⚖️ Stagnant (Facing recession)"
    elif drop_val <= 70.0: return "📉 Recession Alert (Widespread depression)"
    else: return "⚠️ Economic Storm (Systemic collapse)"

def get_civic_index_text(score):
    if score < 15: return f"Highly Gullible ({score:.1f})"
    elif score < 30: return f"Easily Influenced ({score:.1f})"
    elif score < 45: return f"Slightly Influenced ({score:.1f})"
    elif score < 60: return f"Moderately Rational ({score:.1f})"
    elif score < 75: return f"Slightly Critical ({score:.1f})"
    elif score < 90: return f"Mature Critical Thinking ({score:.1f})"
    else: return f"Highly Independent ({score:.1f})"

def get_emotion_text(emotion_val):
    if emotion_val < 20: return f"Calm & Stable ({emotion_val:.1f})"
    elif emotion_val < 50: return f"Slightly Restless ({emotion_val:.1f})"
    elif emotion_val < 80: return f"Enraged ({emotion_val:.1f})"
    else: return f"Fanatical ({emotion_val:.1f})"

def get_election_icon(year, cycle):
    rem = year % cycle
    if rem == 1: return "🗳️ Election Year"
    elif rem == 2: return "🌱 First Year of Term"
    elif rem == cycle - 1: return "⏳ 2 Years to Election"
    elif rem == 0: return "🚨 Election Next Year"
    else: return f"⏳ {cycle - rem + 1} Years to Election"

def get_party_logo(name):
    if name == "Prosperity": return "🦅"
    elif name == "Equity": return "🤝"
    return "🚩"

def get_thinktank_eval(ability, diff):
    abi_lvl = "high" if ability >= 7 else "med" if ability >= 4 else "low"
    acc_lvl = "high" if diff <= 5.0 else "med" if diff <= 15.0 else "low" 
    matrix = {
        ('high', 'high'): "Top-tier performance, perfect prediction",
        ('high', 'med'): "Slight error, strategically manageable",
        ('high', 'low'): "Black Swan event! Failed to foresee drastic changes",
        ('med', 'high'): "Exceptional performance, highly accurate",
        ('med', 'med'): "Average performance, within expected error margin",
        ('med', 'low'): "Severe miscalculation, upgrade recommended",
        ('low', 'high'): "Blind luck, happened to guess correctly",
        ('low', 'med'): "Acceptable performance, but low reference value",
        ('low', 'low'): "Complete failure, severely misleading decisions!"
    }
    return matrix.get((abi_lvl, acc_lvl), "Operational Anomaly")
