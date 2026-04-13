# ==========================================
# config.py
# 負責管理遊戲全域設定、UI 中文本與判讀邏輯
# ==========================================
import streamlit as st

def t(en, zh):
    return zh if st.session_state.get('lang') == 'ZH' else en

DEFAULT_CONFIG = {
    'CALENDAR_NAME': "Star Calendar", 'PARTY_A_COLOR': "#2E8B57", 'PARTY_B_COLOR': "#4169E1",
    'PARTY_A_NAME': "Prosperity", 'PARTY_B_NAME': "Equity", 
    'CROWN_WINNER': "👑 Ruling", 'CROWN_LOSER': "🎯 Candidate",
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
    'SANITY_DEFAULT': 60.0, 
    'EMOTION_DEFAULT': 30.0,
    'SUPPORT_CONVERSION_RATE': 0.05, 
    'PERF_IMPACT_BASE': 500.0        
}

def get_config_translations():
    if st.session_state.get('lang') == 'ZH':
        return {
            'CALENDAR_NAME': "紀元名稱", 'PARTY_A_COLOR': "A黨代表色", 'PARTY_B_COLOR': "B黨代表色",
            'PARTY_A_NAME': "A黨名稱", 'PARTY_B_NAME': "B黨名稱", 
            'CROWN_WINNER': "勝選者稱呼", 'CROWN_LOSER': "敗選者稱呼",
            'INITIAL_WEALTH': "初始黨產", 'END_YEAR': "遊戲總年數",
            'DECAY_MIN': "最小衰退率", 'DECAY_MAX': "最大衰退率",  
            'BUILD_DIFF': "建設難度", 'INVESTIGATE_DIFF': "調查難度", 'EDU_DIFF': "教育難度", 'PREDICT_DIFF': "預測難度", 'MEDIA_DIFF': "媒體難度",
            'CURRENT_GDP': "初始 GDP", 'HEALTH_MULTIPLIER': "GDP轉預算乘數", 'BASE_TOTAL_BUDGET': "基礎預算",  
            'RULING_BONUS': "當權紅利", 'DEFAULT_BONUS': "基本補助金", 
            'H_FUND_DEFAULT': "初始執行獎勵基金", 
            'H_MEDIA_BONUS': "執行系統媒體加成", 'R_INV_BONUS': "監管系統調查加成",
            'CORRUPTION_PENALTY': "貪污罰金倍率", 'MAX_ABILITY': "能力上限", 'ABILITY_DEFAULT': "初始能力", 'MAINTENANCE_RATE': "維護費倍率",
            'TRUST_BREAK_PENALTY_RATIO': "換位扣款比例", 'ELECTION_CYCLE': "大選週期(年)",
            'SUPPORT_CONVERSION_RATE': "支持度轉換率", 'PERF_IMPACT_BASE': "施政表現基礎影響量"
        }
    return {
        'CALENDAR_NAME': "Era Name", 'PARTY_A_COLOR': "Party A Color", 'PARTY_B_COLOR': "Party B Color",
        'PARTY_A_NAME': "Party A Name", 'PARTY_B_NAME': "Party B Name", 
        'CROWN_WINNER': "Winner Title", 'CROWN_LOSER': "Loser Title",
        'INITIAL_WEALTH': "Initial Wealth", 'END_YEAR': "Total Years",
        'DECAY_MIN': "Min Decay", 'DECAY_MAX': "Max Decay",  
        'BUILD_DIFF': "Build Diff", 'INVESTIGATE_DIFF': "Inv Diff", 'EDU_DIFF': "Edu Diff", 'PREDICT_DIFF': "Predict Diff", 'MEDIA_DIFF': "Media Diff",
        'CURRENT_GDP': "Initial GDP", 'HEALTH_MULTIPLIER': "GDP Multiplier", 'BASE_TOTAL_BUDGET': "Base Budget",  
        'RULING_BONUS': "Ruling Bonus", 'DEFAULT_BONUS': "Basic Grant", 
        'H_FUND_DEFAULT': "Init Reward Fund", 
        'H_MEDIA_BONUS': "H-Media Bonus", 'R_INV_BONUS': "R-Inv Bonus",
        'CORRUPTION_PENALTY': "Fine Multiplier", 'MAX_ABILITY': "Max Ability", 'ABILITY_DEFAULT': "Init Ability", 'MAINTENANCE_RATE': "Maint. Rate",
        'TRUST_BREAK_PENALTY_RATIO': "Swap Fee Ratio", 'ELECTION_CYCLE': "Election Cycle",
        'SUPPORT_CONVERSION_RATE': "Conversion Rate", 'PERF_IMPACT_BASE': "Perf. Impact Base"
    }

def get_economic_forecast_text(decay_val):
    lang = st.session_state.get('lang', 'EN')
    if decay_val <= 0.15: return t("🌟 Booming", "🌟 景氣極佳")
    elif decay_val <= 0.35: return t("📈 Growing", "📈 穩定成長")
    elif decay_val <= 0.55: return t("⚖️ Stagnant", "⚖️ 持平放緩")
    elif decay_val <= 0.75: return t("📉 Recession", "📉 衰退警報")
    else: return t("⚠️ Crisis", "⚠️ 經濟風暴")

def get_civic_index_text(score):
    if score < 15: return t(f"Gullible ({score:.1f})", f"易受灌輸 ({score:.1f}分)")
    elif score < 30: return t(f"Suggestible ({score:.1f})", f"較易受灌輸 ({score:.1f}分)")
    elif score < 45: return t(f"Slightly Indoctrinated ({score:.1f})", f"略受灌輸 ({score:.1f}分)")
    elif score < 60: return t(f"Moderate ({score:.1f})", f"理性中等 ({score:.1f}分)")
    elif score < 75: return t(f"Discerning ({score:.1f})", f"略具思辨 ({score:.1f}分)")
    elif score < 90: return t(f"Critical Thinker ({score:.1f})", f"思辨成熟 ({score:.1f}分)")
    else: return t(f"Independent Thinker ({score:.1f})", f"高度獨立思考 ({score:.1f}分)")

def get_emotion_text(emotion_val):
    if emotion_val < 20: return t(f"Calm ({emotion_val:.1f})", f"平穩冷靜 ({emotion_val:.1f})")
    elif emotion_val < 50: return t(f"Restless ({emotion_val:.1f})", f"些微躁動 ({emotion_val:.1f})")
    elif emotion_val < 80: return t(f"Angry ({emotion_val:.1f})", f"群情激憤 ({emotion_val:.1f})")
    else: return t(f"Fanatical ({emotion_val:.1f})", f"陷入狂熱 ({emotion_val:.1f})")

def get_election_icon(year, cycle):
    rem = year % cycle
    if rem == 1: return t("🗳️ Election Year", "🗳️ 大選年")
    elif rem == 2: return t("🌱 Year 1", "🌱 施政元年")
    elif rem == cycle - 1: return t("⏳ 2 Years to Election", "⏳ 距選舉 2 年")
    elif rem == 0: return t("🚨 Election Next Year", "🚨 明年選舉")
    else: return t(f"{cycle - rem + 1} Years to Election", f"距大選 {cycle - rem + 1} 年")

def get_party_logo(name):
    if name == "Prosperity": return "🦅"
    elif name == "Equity": return "🤝"
    return "🚩"

def get_thinktank_eval(ability, diff):
    abi_lvl = "high" if ability >= 7 else "med" if ability >= 4 else "low"
    acc_lvl = "high" if diff <= 0.05 else "med" if diff <= 0.15 else "low"
    matrix = {
        ('high', 'high'): t("Top Performance", "頂尖發揮，完美預判"), 
        ('high', 'med'): t("Minor Margin", "微幅誤差，戰略可控"), 
        ('high', 'low'): t("Black Swan!", "黑天鵝事件！未能看透劇變"),
        ('med', 'high'): t("Superb Prediction", "表現超常，精準命中"), 
        ('med', 'med'): t("Expected Margin", "中規中矩，誤差預期內"), 
        ('med', 'low'): t("Major Misjudgment", "嚴重誤判，建議升級"),
        ('low', 'high'): t("Pure Luck", "瞎貓碰死耗子，幸運猜中"), 
        ('low', 'med'): t("Unreliable", "表現尚可，參考價值低"), 
        ('low', 'low'): t("Total Failure!", "完全失能，嚴重誤導決策！")
    }
    return matrix.get((abi_lvl, acc_lvl), t("Error", "運作異常"))
