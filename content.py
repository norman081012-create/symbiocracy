# ==========================================
# content.py
# 負責管理遊戲全域設定、UI 中文本與判讀邏輯
# ==========================================

DEFAULT_CONFIG = {
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'INITIAL_WEALTH': 1000.0, 'END_YEAR': 12,
    'DECAY_MIN': 0.0, 'DECAY_MAX': 0.8,  
    'BUILD_DIFF': 1.0, 'INVESTIGATE_DIFF': 1.0, 'EDU_DIFF': 1.0, 'PREDICT_DIFF': 1.0, 'MEDIA_DIFF': 1.0,
    'CURRENT_GDP': 5000.0, 
    'HEALTH_MULTIPLIER': 0.2, 
    'BASE_TOTAL_BUDGET': 0.0,  
    'RULING_BONUS': 50.0, 'DEFAULT_BONUS': 100.0, 
    'H_FUND_DEFAULT': 600.0, 
    'H_MEDIA_BONUS': 1.2, 'R_INV_BONUS': 1.2,
    'CORRUPTION_PENALTY': 2.0,
    'MAX_ABILITY': 10.0, 'ABILITY_DEFAULT': 3.0, 'MAINTENANCE_RATE': 10.0,
    'TRUST_BREAK_PENALTY_RATIO': 0.05,
    'ELECTION_CYCLE': 4,
    'SANITY_DEFAULT': 0.60, 
    'EMOTION_DEFAULT': 30.0 
}

CONFIG_TRANSLATIONS = {
    'PARTY_A_NAME': "A黨名稱", 'PARTY_B_NAME': "B黨名稱", 
    'INITIAL_WEALTH': "初始黨產", 'END_YEAR': "遊戲總年數",
    'DECAY_MIN': "最小隨機衰退率", 'DECAY_MAX': "最大隨機衰退率",  
    'BUILD_DIFF': "建設難度", 'INVESTIGATE_DIFF': "調查難度", 'EDU_DIFF': "教育難度", 'PREDICT_DIFF': "預測難度", 'MEDIA_DIFF': "媒體操控難度",
    'CURRENT_GDP': "初始 GDP", 'HEALTH_MULTIPLIER': "GDP轉預算乘數", 'BASE_TOTAL_BUDGET': "基礎常態預算",  
    'RULING_BONUS': "執政紅利", 'DEFAULT_BONUS': "基本政黨補助金", 
    'H_FUND_DEFAULT': "初始執行獎勵基金", 
    'H_MEDIA_BONUS': "執行者媒體加成倍率", 'R_INV_BONUS': "調節者調查加成倍率",
    'CORRUPTION_PENALTY': "貪污被逮罰金倍率", 'MAX_ABILITY': "能力值上限", 'ABILITY_DEFAULT': "初始能力值", 'MAINTENANCE_RATE': "能力維護費倍率",
    'TRUST_BREAK_PENALTY_RATIO': "談判破裂扣款比例", 'ELECTION_CYCLE': "大選週期(年)",
    'SANITY_DEFAULT': "初始識讀指數(0~1)", 'EMOTION_DEFAULT': "初始選民情緒(0~100)"
}

def get_economic_forecast_text(decay_val):
    if decay_val <= 0.15: return "🌟 景氣極佳"
    elif decay_val <= 0.35: return "📈 穩定成長"
    elif decay_val <= 0.55: return "⚖️ 持平放緩"
    elif decay_val <= 0.75: return "📉 衰退警報"
    else: return "⚠️ 經濟風暴"

def get_civic_index_text(index_val):
    score = index_val * 100
    if score < 40: return f"群氓狀態 ({score:.1f}分)"
    elif score < 60: return f"盲從階段 ({score:.1f}分)"
    elif score < 80: return f"理性中等 ({score:.1f}分)"
    else: return f"覺醒公民 ({score:.1f}分)"

def get_emotion_text(emotion_val):
    if emotion_val < 20: return f"平穩冷靜 ({emotion_val:.1f})"
    elif emotion_val < 50: return f"些微躁動 ({emotion_val:.1f})"
    elif emotion_val < 80: return f"群情激憤 ({emotion_val:.1f})"
    else: return f"陷入狂熱 ({emotion_val:.1f})"
