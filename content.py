# ==========================================
# content.py
# 負責管理遊戲全域設定、UI 中文本與判讀邏輯
# ==========================================
import random

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

def generate_phase2_flavor_text(game, view_party):
    """根據國家現況生成帶入感文案 (Phase 2)"""
    gdp_lvl = "high" if game.gdp > 6000 else "low" if game.gdp < 4000 else "med"
    san_lvl = "high" if game.sanity > 0.7 else "low" if game.sanity < 0.4 else "med"
    emo_lvl = "high" if game.emotion > 70 else "low" if game.emotion < 30 else "med"
    decay_lvl = "high" if view_party.current_forecast > 0.5 else "low" if view_party.current_forecast < 0.2 else "med"
    
    prompts = {
        ('high', 'high', 'low', 'low'): "經濟繁榮，社會理性且平靜。這是一個推動長遠建設的絕佳時機。",
        ('low', 'low', 'high', 'high'): "經濟衰退，民怨沸騰，社會充滿盲從與狂熱。我們必須在風暴中尋找生存之道，任何政策都可能引發反彈。",
        ('med', 'med', 'med', 'med'): "國家處於平穩狀態，各項指標皆在掌控之中。穩紮穩打是目前的最佳策略。",
        ('high', 'low', 'high', 'low'): "雖然經濟數據亮眼，但社會理智低迷且情緒高漲。我們需要小心引導這股狂熱，避免局勢失控。",
        ('low', 'high', 'low', 'high'): "經濟面臨嚴峻挑戰，但公民具備高度理智，社會情緒穩定。這是一場考驗我們韌性的持久戰。"
    }
    
    key = (gdp_lvl, san_lvl, emo_lvl, decay_lvl)
    return prompts.get(key, "局勢錯綜複雜，請審慎評估各項政策的影響，帶領國家度過這一年的挑戰。")

def generate_phase1_flavor_text(game, view_party):
    """根據國家現況生成帶入感文案 (Phase 1)"""
    if game.year == 1:
        return "新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商，確立今年的施政方向。"
    
    rep = game.last_year_report
    if not rep:
        return "新的一年開始了，請展開預算與目標協商。"

    gdp_diff = ((game.gdp - rep['old_gdp']) / max(1.0, rep['old_gdp'])) * 100
    h_diff = rep['h_perf']
    
    gdp_str = f"成長 {gdp_diff:.1f}%" if gdp_diff >= 0 else f"衰退 {abs(gdp_diff):.1f}%"
    h_str = "達標" if h_diff >= 0 else f"落後 {abs(h_diff):.1f}%"
    
    return f"回顧去年，GDP {gdp_str}，執行者目標 {h_str}。基於此現況，請擬定今年的預算草案。"
