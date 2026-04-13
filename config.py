# ==========================================
# config.py
# 負責管理遊戲全域設定、UI 中文本與判讀邏輯
# ==========================================

DEFAULT_CONFIG = {
    'CALENDAR_NAME': "星曆", 'PARTY_A_COLOR': "#2E8B57", 'PARTY_B_COLOR': "#4169E1",
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'CROWN_WINNER': "👑 當權", 'CROWN_LOSER': "🎯 候選",
    'INITIAL_WEALTH': 1000.0, 'END_YEAR': 12,
    'DECAY_MIN': 0.0, 'DECAY_MAX': 0.8,  
    'CURRENT_GDP': 5000.0, 
    
    # --- v3.0 經濟與數學系統 ---
    'TAX_RATE': 0.20,             # 稅收預算比例
    'BASE_ANNUITY': 0.05,         # 基本年金
    'RULING_ANNUITY': 0.10,       # 當權紅利
    'RESISTANCE_MULT': 5.0,       # 衰退阻力倍率
    'DECAY_COEFF': 0.072,         # 衰退基準係數
    'H_INDEX_PERF_WEIGHT': 100.0, 
    'GDP_PERF_WEIGHT': 500.0,     
    
    # --- 漸進式升級系統 ---
    'BASE_UPGRADE_COST': 30.0,    # 基礎升級成本 (已乘以3)
    'MAX_ABILITY': 100.0, 'ABILITY_DEFAULT': 20.0, 'MAINTENANCE_RATE': 0.1,
    
    'CORRUPTION_PENALTY': 2.0,
    'TRUST_BREAK_PENALTY_RATIO': 0.05,
    'ELECTION_CYCLE': 4,
    'SANITY_DEFAULT': 60.0, 
    'EMOTION_DEFAULT': 30.0,
}

CONFIG_TRANSLATIONS = {
    'CALENDAR_NAME': "紀元名稱", 'PARTY_A_COLOR': "A黨代表色", 'PARTY_B_COLOR': "B黨代表色",
    'PARTY_A_NAME': "A黨名稱", 'PARTY_B_NAME': "B黨名稱", 
    'CROWN_WINNER': "勝選者稱呼", 'CROWN_LOSER': "敗選者稱呼",
    'INITIAL_WEALTH': "初始黨產", 'END_YEAR': "遊戲總年數",
    'DECAY_MIN': "最小衰退率", 'DECAY_MAX': "最大衰退率",  
    'CURRENT_GDP': "初始 GDP", 'TAX_RATE': "稅收預算比例", 
    'CORRUPTION_PENALTY': "貪污罰金倍率", 'MAX_ABILITY': "能力上限", 'ABILITY_DEFAULT': "初始能力", 
    'TRUST_BREAK_PENALTY_RATIO': "換位扣款比例", 'ELECTION_CYCLE': "大選週期(年)",
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
    elif score < 45: return f"略受灌輸 ({score:.1f}分)"
    elif score < 60: return f"理性中等 ({score:.1f}分)"
    elif score < 75: return f"略具思辨 ({score:.1f}分)"
    elif score < 90: return f"思辨成熟 ({score:.1f}分)"
    else: return f"高度獨立思考 ({score:.1f}分)"

def get_emotion_text(emotion_val):
    if emotion_val < 20: return f"平穩冷靜 ({emotion_val:.1f})"
    elif emotion_val < 50: return f"些微躁動 ({emotion_val:.1f})"
    elif emotion_val < 80: return f"群情激憤 ({emotion_val:.1f})"
    else: return f"陷入狂熱 ({emotion_val:.1f})"

def get_election_icon(year, cycle):
    rem = year % cycle
    if rem == 1: return "🗳️ 大選年"
    elif rem == 2: return "🌱 施政元年"
    elif rem == cycle - 1: return "⏳ 距選舉 2 年"
    elif rem == 0: return "🚨 明年選舉"
    else: return f"距大選 {cycle - rem + 1} 年"

def get_party_logo(name):
    if name == "Prosperity": return "🦅"
    elif name == "Equity": return "🤝"
    return "🚩"

def get_thinktank_eval(ability, diff):
    # 轉換為 0-100 制的判讀
    abi_lvl = "high" if ability >= 70 else "med" if ability >= 40 else "low"
    acc_lvl = "high" if diff <= 0.05 else "med" if diff <= 0.15 else "low"
    matrix = {
        ('high', 'high'): "頂尖發揮，完美預判", ('high', 'med'): "微幅誤差，戰略可控", ('high', 'low'): "黑天鵝事件！未能看透劇變",
        ('med', 'high'): "表現超常，精準命中", ('med', 'med'): "中規中矩，誤差預期內", ('med', 'low'): "嚴重誤判，建議升級",
        ('low', 'high'): "瞎貓碰死耗子，幸運猜中", ('low', 'med'): "表現尚可，參考價值低", ('low', 'low'): "完全失能，嚴重誤導決策！"
    }
    return matrix.get((abi_lvl, acc_lvl), "運作異常")
