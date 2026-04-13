# ==========================================
# config.py
# ==========================================
DEFAULT_CONFIG = {
    'CALENDAR_NAME': "星曆", 'PARTY_A_COLOR': "#2E8B57", 'PARTY_B_COLOR': "#4169E1",
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'INITIAL_WEALTH': 1000.0, 'END_YEAR': 12,
    'DECAY_MIN': 0.0, 'DECAY_MAX': 0.8,  
    'TAX_RATE': 0.20, 'P_B_RATE': 0.05, 'P_R_RATE': 0.10, # 新經濟系統稅率與年金
    'RESISTANCE_MULT': 5.0, 'DECAY_COEFF': 0.072,         # 阻力與衰退係數
    'CURRENT_GDP': 5000.0, 
    'UPGRADE_BASE_COST': 5.0, 'UPGRADE_EXP_MULT': 1.04,   # 指數升級參數 (1.04^eff)
    'DOWNGRADE_RATE_PER_YEAR': 15.0, 
    'CORRUPTION_PENALTY': 2.0, 'EFF_DEFAULT': 20.0,
    'TRUST_BREAK_PENALTY_RATIO': 0.05, 'ELECTION_CYCLE': 4,
    'SANITY_DEFAULT': 0.60, 'EMOTION_DEFAULT': 30.0,
    'LIVELIHOOD_WEIGHT': 50.0, 'SUPPORT_CONVERSION_RATE': 0.05
}

CONFIG_TRANSLATIONS = {
    'CALENDAR_NAME': "紀元名稱", 'PARTY_A_COLOR': "A黨代表色", 'PARTY_B_COLOR': "B黨代表色",
    'PARTY_A_NAME': "A黨名稱", 'PARTY_B_NAME': "B黨名稱", 
    'INITIAL_WEALTH': "初始黨產", 'END_YEAR': "遊戲總年數",
    'DECAY_MIN': "最小衰退率", 'DECAY_MAX': "最大衰退率",  
    'CURRENT_GDP': "初始 GDP", 'TAX_RATE': "稅收轉換率", 'P_B_RATE': "基本年金%", 'P_R_RATE': "當權紅利%",
    'RESISTANCE_MULT': "阻力放大倍率", 'DECAY_COEFF': "衰退係數",
    'UPGRADE_BASE_COST': "升級基礎費", 'UPGRADE_EXP_MULT': "升級指數率",
    'CORRUPTION_PENALTY': "貪污罰金", 'EFF_DEFAULT': "初始效率", 
    'DOWNGRADE_RATE_PER_YEAR': "每年降級速率(%)",
    'LIVELIHOOD_WEIGHT': "民生影響權重", 'TRUST_BREAK_PENALTY_RATIO': "換位扣款", 'ELECTION_CYCLE': "大選週期"
}

def get_economic_forecast_text(decay_val): return "🌟 景氣極佳" if decay_val <= 0.15 else "📉 衰退警報"
def get_civic_index_text(index_val): return f"覺醒公民 ({index_val*100:.1f}分)" if index_val > 0.8 else f"群氓狀態 ({index_val*100:.1f}分)"
def get_emotion_text(emotion_val): return f"陷入狂熱 ({emotion_val:.1f})" if emotion_val > 80 else f"平穩冷靜 ({emotion_val:.1f})"
def get_election_icon(year, cycle): return "🗳️ 大選年" if year % cycle == 1 else "⏳ 備戰期"
def get_party_logo(name): return "🦅" if name == "Prosperity" else "🤝"
