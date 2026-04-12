# ==========================================
# content.py
# 負責管理遊戲全域設定、UI 中文本與判定邏輯
# ==========================================

DEFAULT_CONFIG = {
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'INITIAL_WEALTH': 1000.0, 'END_YEAR': 12,
    'DECAY_MIN': 0.0, 'DECAY_MAX': 0.8,  
    'BUILD_DIFF': 1.0, 'INVESTIGATE_DIFF': 1.0, 'EDU_DIFF': 1.0, 'PREDICT_DIFF': 1.0, 'MEDIA_DIFF': 1.0,
    'CURRENT_GDP': 5000.0, 'HEALTH_MULTIPLIER': 0.2, 'BASE_TOTAL_BUDGET': 0.0,  
    'RULING_BONUS': 50.0, 'DEFAULT_BONUS': 100.0, 
    'H_FUND_DEFAULT': 600.0, 'H_MEDIA_BONUS': 1.2, 'R_INV_BONUS': 1.2,
    'CORRUPTION_PENALTY': 2.0, 'MAX_ABILITY': 10.0, 'ABILITY_DEFAULT': 3.0, 
    'MAINTENANCE_RATE': 10.0, 'TRUST_BREAK_PENALTY_RATIO': 0.05,
    'THIRD_PARTY_FEE': 100.0, 
    'ELECTION_CYCLE': 4, 'SANITY_DEFAULT': 0.60, 'EMOTION_DEFAULT': 30.0,
    'CAMPAIGN_MAGNITUDE': 15.0 
}

CONFIG_TRANSLATIONS = {
    'PARTY_A_NAME': "A黨名稱", 'PARTY_B_NAME': "B黨名稱", 
    'INITIAL_WEALTH': "初始黨產", 'END_YEAR': "遊戲總年數",
    'DECAY_MIN': "最小衰退率", 'DECAY_MAX': "最大衰退率",  
    'BUILD_DIFF': "建設難度", 'INVESTIGATE_DIFF': "調查難度", 'EDU_DIFF': "教育難度", 'PREDICT_DIFF': "預測難度", 'MEDIA_DIFF': "媒體難度",
    'CURRENT_GDP': "初始 GDP", 'HEALTH_MULTIPLIER': "GDP轉預算乘數", 'BASE_TOTAL_BUDGET': "基礎預算",  
    'RULING_BONUS': "執政紅利", 'DEFAULT_BONUS': "基本補助金", 
    'H_FUND_DEFAULT': "初始標案付款基金", 
    'H_MEDIA_BONUS': "執行系統媒體加成", 'R_INV_BONUS': "監管系統調查加成",
    'CORRUPTION_PENALTY': "貪污罰金倍率", 'MAX_ABILITY': "能力上限", 'ABILITY_DEFAULT': "初始能力", 'MAINTENANCE_RATE': "維護費倍率",
    'TRUST_BREAK_PENALTY_RATIO': "換位扣款比例", 'ELECTION_CYCLE': "大選週期(年)",
    'SANITY_DEFAULT': "初始識讀指數(0~1)", 'EMOTION_DEFAULT': "初始選民情緒(0~100)"
}

def get_election_icon(year, cycle):
    rem = (cycle - (year % cycle)) % cycle
    if year % cycle == 1: return "🗳️ 【大選年】"
    if rem == 0: return "🚨 倒數 1 年"
    if rem == 1: return "⏳ 倒數 2 年"
    return f"🏛️ 距下屆大選 {rem + 1} 年"

def get_performance_eval(actual, target):
    diff = actual - target
    if diff > 500: return "超越極高"
    if diff > 100: return "大幅超越"
    if diff > -50: return "達標"
    if diff > -300: return "落後"
    return "嚴重偏離"

def get_thinktank_eval(ability, diff):
    abi_lvl = "high" if ability >= 7 else "med" if ability >= 4 else "low"
    acc_lvl = "high" if diff <= 0.05 else "med" if diff <= 0.15 else "low"
    matrix = {
        ('high', 'high'): "精準預判市場，戰略布局完美。",
        ('high', 'med'): "判斷正確，唯細節受波動干擾。",
        ('high', 'low'): "遭遇黑天鵝，智庫受極限挑戰。",
        ('med', 'high'): "表現優異，超乎現有資源水準。",
        ('med', 'med'): "中規中矩，符合數據常規。",
        ('med', 'low'): "誤判情勢，建議升級預測能力。",
        ('low', 'high'): "數據僥倖吻合，建議加強深度。",
        ('low', 'med'): "預測力薄弱，參考價值有限。",
        ('low', 'low'): "預測形同廢紙，嚴重誤導決策！"
    }
    return matrix.get((abi_lvl, acc_lvl), "系統重啟中")

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
