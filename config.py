# config.py
DEFAULT_CONFIG = {
    'CALENDAR_NAME': "星曆", 'PARTY_A_COLOR': "#2E8B57", 'PARTY_B_COLOR': "#4169E1",
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'CROWN_WINNER': "👑 當權", 'CROWN_LOSER': "🎯 候選",
    'INITIAL_WEALTH': 1000.0, 'END_YEAR': 12,
    'DECAY_MIN': 0.0, 'DECAY_MAX': 0.8,  
    'CURRENT_GDP': 5000.0, 
    # v3.1 經濟系統參數
    'TAX_RATE': 0.20,             # 稅收預算化比例
    'BASE_ANNUITY': 0.05,         # 政黨基本金比例
    'RULING_ANNUITY': 0.10,       # 當權紅利比例
    'RESISTANCE_MULT': 5.0,       # 衰退阻力放大倍率
    'DECAY_COEFF': 0.072,         # 衰退基準係數 (0.5=3.6%)
    'H_INDEX_PERF_WEIGHT': 100.0, # H-Index 政績影響權重
    'GDP_PERF_WEIGHT': 500.0,     # GDP 政績影響權重
    'BASE_UPGRADE_COST': 10.0,    # 部門升級基準花費
    'ABILITY_DEGRADE_RATE': 10.0, # 每年未維護自然下降的速度
    
    'MAX_ABILITY': 100.0, 'ABILITY_DEFAULT': 20.0, 'MAINTENANCE_RATE': 0.1,
    'TRUST_BREAK_PENALTY_RATIO': 0.05,
    'ELECTION_CYCLE': 4,
    'SANITY_DEFAULT': 60.0, 'EMOTION_DEFAULT': 30.0,
}

CONFIG_TRANSLATIONS = {
    'TAX_RATE': "稅收預算比例", 'BASE_ANNUITY': "基本年金比例", 'RULING_ANNUITY': "當權紅利比例",
    'RESISTANCE_MULT': "衰退阻力倍率", 'DECAY_COEFF': "衰退基準係數",
    'MAX_ABILITY': "能力上限", 'ABILITY_DEFAULT': "初始能力", 'MAINTENANCE_RATE': "維護費係數"
}

def get_economic_forecast_text(decay_val):
    if decay_val <= 0.15: return "🌟 景氣極佳"
    elif decay_val <= 0.35: return "📈 穩定成長"
    elif decay_val <= 0.55: return "⚖️ 持平放緩"
    elif decay_val <= 0.75: return "📉 衰退警報"
    else: return "⚠️ 經濟風暴"

def get_civic_index_text(score):
    if score < 15: return f"易受灌輸 ({score:.1f}分)"
    elif score < 30: return f"較易受灌輸 ({score:.1f}分)"
    elif score < 60: return f"理性中等 ({score:.1f}分)"
    elif score < 90: return f"思辨成熟 ({score:.1f}分)"
    else: return f"高度獨立思考 ({score:.1f}分)"

def get_emotion_text(emotion_val):
    if emotion_val < 30: return f"平穩冷靜 ({emotion_val:.1f})"
    elif emotion_val < 70: return f"群情激憤 ({emotion_val:.1f})"
    else: return f"陷入狂熱 ({emotion_val:.1f})"

def get_election_icon(year, cycle):
    rem = year % cycle
    if rem == 1: return "🗳️ 大選年"
    elif rem == 0: return "🚨 明年選舉"
    else: return f"距大選 {cycle - rem + 1} 年"

def get_party_logo(name):
    return "🦅" if name == "Prosperity" else "🤝"
