# ==========================================
# content.py
# 負責管理遊戲全域設定、UI 中文本與判讀邏輯
# ==========================================

# 全域變數預設值 (對應 UI 顯示)
DEFAULT_CONFIG = {
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'INITIAL_WEALTH': 1000.0, 'END_YEAR': 12,
    'DECAY_MIN': 0.0, 'DECAY_MAX': 0.8,  
    'BUILD_DIFF': 1.0, 'INVESTIGATE_DIFF': 1.0, 'EDU_DIFF': 1.0, 'PREDICT_DIFF': 1.0, 'PROP_DIFF': 1.0,
    'CURRENT_GDP': 5000.0, 
    'HEALTH_MULTIPLIER': 0.2, 
    'BASE_TOTAL_BUDGET': 0.0,  
    'RULING_BONUS': 50.0, 'DEFAULT_BONUS': 100.0, 
    'H_FUND_DEFAULT': 600.0, 
    'H_PROP_BONUS': 1.2, 'R_INV_BONUS': 1.2,
    'CORRUPTION_PENALTY': 2.0,
    'MAX_ABILITY': 10.0,
    'TRUST_BREAK_PENALTY_RATIO': 0.05,
    'ELECTION_CYCLE': 4
}

# 變數中文對照表 (用於側邊欄設定)
CONFIG_TRANSLATIONS = {
    'PARTY_A_NAME': "A黨名稱", 'PARTY_B_NAME': "B黨名稱", 
    'INITIAL_WEALTH': "初始黨產", 'END_YEAR': "遊戲總年數",
    'DECAY_MIN': "最小隨機衰退率", 'DECAY_MAX': "最大隨機衰退率",  
    'BUILD_DIFF': "建設難度係數", 'INVESTIGATE_DIFF': "調查難度係數", 'EDU_DIFF': "教育難度係數", 'PREDICT_DIFF': "預測難度係數", 'PROP_DIFF': "宣傳難度係數",
    'CURRENT_GDP': "初始 GDP", 'HEALTH_MULTIPLIER': "GDP轉預算乘數", 'BASE_TOTAL_BUDGET': "基礎常態預算",  
    'RULING_BONUS': "執政紅利", 'DEFAULT_BONUS': "基本政黨補助金", 
    'H_FUND_DEFAULT': "初始行政獎勵基金", 
    'H_PROP_BONUS': "H黨宣傳加成倍率", 'R_INV_BONUS': "R黨調查加成倍率",
    'CORRUPTION_PENALTY': "貪污被逮罰金倍率", 'MAX_ABILITY': "能力值上限",
    'TRUST_BREAK_PENALTY_RATIO': "談判破裂扣款比例", 'ELECTION_CYCLE': "大選週期(年)"
}

def get_economic_forecast_text(decay_val):
    if decay_val <= 0.15: return "🌟 景氣極佳 (經濟繁榮，預算壓力小)"
    elif decay_val <= 0.35: return "📈 穩定成長 (市場動能良好)"
    elif decay_val <= 0.55: return "⚖️ 持平放緩 (需注意潛在風險)"
    elif decay_val <= 0.75: return "📉 衰退警報 (經濟疲軟，維持現狀成本高)"
    else: return "⚠️ 經濟風暴 (嚴重衰退，極易引發民怨)"

def get_civic_index_text(index_val):
    """將 0~1 的 sanity 轉換為 0~100 的公民識讀指數並判讀"""
    score = index_val * 100
    if score < 40: return f"群氓狀態 ({score:.1f}分 - 極易受民粹與假新聞操弄)"
    elif score < 60: return f"盲從階段 ({score:.1f}分 - 缺乏獨立批判思考能力)"
    elif score < 80: return f"明智社會 ({score:.1f}分 - 及格，具備基本媒體識讀力)"
    else: return f"覺醒公民 ({score:.1f}分 - 高度理性，極難被政客大內宣洗腦)"
