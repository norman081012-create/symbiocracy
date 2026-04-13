# ==========================================
# config.py
# ==========================================
DEFAULT_CONFIG = {
    'CALENDAR_NAME': "星曆", 'PARTY_A_COLOR': "#2E8B57", 'PARTY_B_COLOR': "#4169E1",
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'INITIAL_WEALTH': 1000.0, 'END_YEAR': 12,
    'DECAY_MIN': 0.0, 'DECAY_MAX': 0.8,  
    'BUILD_DIFF': 1.0, 'INVESTIGATE_DIFF': 1.0, 'EDU_DIFF': 1.0, 'PREDICT_DIFF': 1.0, 'MEDIA_DIFF': 1.0,
    'CURRENT_GDP': 5000.0, 'HEALTH_MULTIPLIER': 0.2, 'BASE_TOTAL_BUDGET': 0.0,  
    'RULING_BONUS': 50.0, 'DEFAULT_BONUS': 100.0, 'H_FUND_DEFAULT': 600.0, 
    'H_MEDIA_BONUS': 1.2, 'R_INV_BONUS': 1.2, 'CORRUPTION_PENALTY': 2.0,
    'MAX_EFFICIENCY': 100.0, 'EFF_DEFAULT': 20.0, 'MAINTENANCE_BASE': 10.0, 
    'UPGRADE_COST_PER_PCT': 1.5, 'DOWNGRADE_RATE_PER_YEAR': 15.0, # 每年掉落 15% 效率
    'TRUST_BREAK_PENALTY_RATIO': 0.05, 'ELECTION_CYCLE': 4,
    'SANITY_DEFAULT': 0.60, 'EMOTION_DEFAULT': 30.0,
    'LIVELIHOOD_WEIGHT': 50.0, 
    'SUPPORT_CONVERSION_RATE': 0.05, 'PERF_IMPACT_BASE': 500.0        
}

CONFIG_TRANSLATIONS = {
    'CALENDAR_NAME': "紀元名稱", 'PARTY_A_COLOR': "A黨代表色", 'PARTY_B_COLOR': "B黨代表色",
    'PARTY_A_NAME': "A黨名稱", 'PARTY_B_NAME': "B黨名稱", 
    'INITIAL_WEALTH': "初始黨產", 'END_YEAR': "遊戲總年數",
    'DECAY_MIN': "最小衰退率", 'DECAY_MAX': "最大衰退率",  
    'BUILD_DIFF': "建設難度", 'INVESTIGATE_DIFF': "調查難度", 'EDU_DIFF': "教育難度", 'PREDICT_DIFF': "預測難度", 'MEDIA_DIFF': "媒體難度",
    'CURRENT_GDP': "初始 GDP", 'HEALTH_MULTIPLIER': "預算乘數", 'BASE_TOTAL_BUDGET': "基礎預算",  
    'RULING_BONUS': "當權紅利", 'DEFAULT_BONUS': "基本補助", 
    'H_FUND_DEFAULT': "初始獎勵池", 
    'H_MEDIA_BONUS': "執行媒體加成", 'R_INV_BONUS': "監管調查加成",
    'CORRUPTION_PENALTY': "貪污罰金", 'MAX_EFFICIENCY': "效率上限", 'EFF_DEFAULT': "初始效率", 
    'MAINTENANCE_BASE': "基礎維護費", 'DOWNGRADE_RATE_PER_YEAR': "每年降級速率(%)",
    'LIVELIHOOD_WEIGHT': "民生影響權重", 'TRUST_BREAK_PENALTY_RATIO': "換位扣款", 'ELECTION_CYCLE': "大選週期"
}

def get_economic_forecast_text(decay_val): return "🌟 景氣極佳" if decay_val <= 0.15 else "📉 衰退警報"
def get_civic_index_text(index_val): return f"覺醒公民 ({index_val*100:.1f}分)" if index_val > 0.8 else f"群氓狀態 ({index_val*100:.1f}分)"
def get_emotion_text(emotion_val): return f"陷入狂熱 ({emotion_val:.1f})" if emotion_val > 80 else f"平穩冷靜 ({emotion_val:.1f})"
def get_election_icon(year, cycle): return "🗳️ 大選年" if year % cycle == 1 else "⏳ 備戰期"
def get_party_logo(name): return "🦅" if name == "Prosperity" else "🤝"
