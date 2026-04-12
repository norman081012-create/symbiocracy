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
    'EMOTION_DEFAULT': 30.0,
    'SUPPORT_CONVERSION_RATE': 0.05, # 新增：影響量轉換為支持度 % 的常數
    'PERF_IMPACT_BASE': 500.0        # 新增：達標率影響的基礎常數量
}

CONFIG_TRANSLATIONS = {
    'PARTY_A_NAME': "A黨名稱", 'PARTY_B_NAME': "B黨名稱", 
    'INITIAL_WEALTH': "初始黨產", 'END_YEAR': "遊戲總年數",
    'DECAY_MIN': "最小衰退率", 'DECAY_MAX': "最大衰退率",  
    'BUILD_DIFF': "建設難度", 'INVESTIGATE_DIFF': "調查難度", 'EDU_DIFF': "教育難度", 'PREDICT_DIFF': "預測難度", 'MEDIA_DIFF': "媒體難度",
    'CURRENT_GDP': "初始 GDP", 'HEALTH_MULTIPLIER': "GDP轉預算乘數", 'BASE_TOTAL_BUDGET': "基礎預算",  
    'RULING_BONUS': "執政紅利", 'DEFAULT_BONUS': "基本補助金", 
    'H_FUND_DEFAULT': "初始執行獎勵基金", 
    'H_MEDIA_BONUS': "執行系統媒體加成", 'R_INV_BONUS': "監管系統調查加成",
    'CORRUPTION_PENALTY': "貪污罰金倍率", 'MAX_ABILITY': "能力上限", 'ABILITY_DEFAULT': "初始能力", 'MAINTENANCE_RATE': "維護費倍率",
    'TRUST_BREAK_PENALTY_RATIO': "換位扣款比例", 'ELECTION_CYCLE': "大選週期(年)",
    'SUPPORT_CONVERSION_RATE': "支持度轉換率", 'PERF_IMPACT_BASE': "施政表現基礎影響量"
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

def get_election_icon(year, cycle):
    rem = year % cycle
    if rem == 1: return "🗳️ 【大選年】"
    elif rem == 0: return "🚨 距大選 1 年"
    elif rem == cycle - 1: return "⏳ 距大選 2 年"
    else: return f"🏛️ 距大選 {cycle - rem + 1} 年"

def get_thinktank_eval(ability, diff):
    abi_lvl = "high" if ability >= 7 else "med" if ability >= 4 else "low"
    acc_lvl = "high" if diff <= 0.05 else "med" if diff <= 0.15 else "low"
    
    matrix = {
        ('high', 'high'): "頂尖智庫發揮應有水準，完美預判走勢。",
        ('high', 'med'): "頂尖智庫微幅誤差，仍在戰略可控範圍內。",
        ('high', 'low'): "黑天鵝事件！頂尖智庫也未能看透經濟劇變。",
        ('med', 'high'): "常規智庫表現超常，精準命中市場波動。",
        ('med', 'med'): "常規智庫表現中規中矩，誤差在預期之內。",
        ('med', 'low'): "常規智庫嚴重誤判形勢，建議升級預測能力。",
        ('low', 'high'): "低階智庫瞎貓碰上死耗子，幸運猜中走向。",
        ('low', 'med'): "低階智庫表現尚可，但數據參考價值有限。",
        ('low', 'low'): "低階智庫完全失去功能，嚴重誤導決策！"
    }
    return matrix.get((abi_lvl, acc_lvl), "智庫系統運作異常。")

def get_target_eval_text(actual, target):
    if target <= 0: return "無目標"
    diff_pct = ((actual - target) / target) * 100
    if diff_pct >= 15: return f"🟢 大幅超標 (+{diff_pct:.1f}%)"
    elif diff_pct >= 5: return f"🟢 中幅超標 (+{diff_pct:.1f}%)"
    elif diff_pct >= 0: return f"🟢 微幅超標 (+{diff_pct:.1f}%)"
    elif diff_pct >= -5: return f"🔴 微幅落後 ({diff_pct:.1f}%)"
    elif diff_pct >= -15: return f"🔴 中幅落後 ({diff_pct:.1f}%)"
    else: return f"🔴 嚴重落後 ({diff_pct:.1f}%)"
