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
    'THIRD_PARTY_FEE': 100.0, # 換位懲罰金
    'ELECTION_CYCLE': 4, 'SANITY_DEFAULT': 0.60, 'EMOTION_DEFAULT': 30.0,
    'CAMPAIGN_MAGNITUDE': 15.0 # 競選影響支持度的基數
}

def get_election_icon(year, cycle):
    rem = (cycle - (year % cycle)) % cycle
    if year % cycle == 1: return "🗳️ 【大選年】"
    if rem == 0: return "🚨 倒數 1 年 (籌備期)"
    if rem == 1: return "⏳ 倒數 2 年 (觀察期)"
    return f"🏛️ 距離下屆大選 {rem + 1} 年"

def get_performance_eval(actual, target):
    diff = actual - target
    if diff > 1000: return "👑 超大幅超越目標 (極高)"
    if diff > 300: return "📈 穩健超越目標 (高)"
    if diff > -100: return "✅ 達成目標 (中)"
    if diff > -500: return "📉 未能達標 (低)"
    return "🚨 嚴重偏離目標 (極低)"

def get_thinktank_eval(ability, diff):
    abi_lvl = "high" if ability >= 7 else "med" if ability >= 4 else "low"
    acc_lvl = "high" if diff <= 0.05 else "med" if diff <= 0.15 else "low"
    matrix = {
        ('high', 'high'): "精準預判市場，戰略布局完美。",
        ('high', 'med'): "趨勢判斷正確，唯細節受波動干擾。",
        ('high', 'low'): "遭遇黑天鵝，智庫能力受極限挑戰。",
        ('med', 'high'): "表現優異，超乎現有資源水準。",
        ('med', 'med'): "中規中矩，符合數據常規。",
        ('med', 'low'): "誤判情勢，建議重新校準調查機制。",
        ('low', 'high'): "數據僥倖吻合，建議加強研究深度。",
        ('low', 'med'): "預測力薄弱，參考價值有限。",
        ('low', 'low'): "系統失效，預測數據完全脫節！"
    }
    return matrix.get((abi_lvl, acc_lvl), "系統重啟中")
