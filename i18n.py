# ==========================================
# i18n.py
# ==========================================
import streamlit as st
import re

EXACT_MATCH_DICT = {
    "👁️ God Mode": "👁️ 上帝模式",
    "🔄 Restart Game": "🔄 重新開始遊戲",
    "🎛️ Control Panel": "🎛️ 遊戲控制面板",
    "🌐 Switch to Chinese": "🌐 切換至繁體中文",
    "🌐 Switch to English": "🌐 Switch to English",
    "📝 Live Parameters": "📝 即時參數設定",
    "🔄 Auto-Fill Intel": "🔄 自動帶入智庫預測",
    "📤 Submit Draft": "📤 送出提案草案",
    "💥 Issue Ultimatum": "💥 下達最後通牒",
    "✅ Select this draft": "✅ 選擇此草案",
    "✅ Agree to Bill": "✅ 同意法案並簽署",
    "❌ Reject & Renegotiate": "❌ 拒絕並重新談判",
    "✅ Accept Ultimatum": "✅ 接受最後通牒",
    "🔄 Reset to Current Maintenance": "🔄 重置為當前維護狀態",
    "Confirm Action & Execute": "確認行動並執行 (進入結算)",
    "⏩ Confirm Report & Next Year": "⏩ 確認報告並進入下一年",
    "🔄 Restart a New Game": "🔄 重新開始新一局遊戲",
    "Switch to Think Tank Estimate": "切換至智庫預估數值",
    "Simulate Role Swap": "模擬對方視角 (換位思考)"
}

DYNAMIC_REPLACEMENTS = {
    "Symbiocracy Simulator v3.0.0": "共生體制模擬器 v3.0.0",
    "Phase 1: R-System Proposal": "第一階段：監管系統 (Regulator) 提案",
    "Phase 2: Execution - Turn:": "第二階段：資源分配與執行 - 輪到：",
    "Phase 3: Annual Resolution Report": "第三階段：年度結算與社會影響報告",
    "Game Over! Final Symbiocracy Summary": "🏁 遊戲結束！共生體制最終歷史結算",
    
    "[ANNUAL NOTICE]": "[年度通知]",
    "A new year begins. The nation awaits rebuilding; initiate budget negotiations immediately.": "新的一年開始了。百廢待舉，請立即展開預算協商。",
    "A new year begins. Initiate budget negotiations.": "新的一年開始了。請展開預算協商。",
    
    "Ruling": "當權",
    "Candidate": "候選",
    "(Won!)": "(勝選!)",
    "(Lost)": "(敗選)",
    
    "National Status": "國家總體狀態",
    "Executive Resources": "執行系統資源池",
    "Think Tank Intel": "智庫情報分析",
    "Financial Report": "財務收支報告",
    "Party Overview": "政黨狀態總覽",
    "Control Panel": "控制面板",
    "Economy & Finance": "經濟與財政結算",
    "Society & Opinion": "社會與民意變化",
    "Support Shift Resolution": "民意支持度板塊位移",
    
    "Total Budget Pool": "國家總預算池",
    "Reward Fund": "執行系統專案獎金",
    "Civic Literacy": "公民素養 (理性)",
    "Voter Emotion": "選民情緒 (狂熱)",
    "Party Wealth": "政黨資金",
    "Total Plan Reward (Max=Budget-Salaries)": "專案總獎金 (上限=總預算扣除薪資)",
    "Plan Total Benefit (Construction Volume)": "專案總效益 (建設規模/產值)",
    "R-Pays": "監管方墊付款",
    "H-Pays": "執行方自籌款",
    "Total Req. Cost": "專案總需成本",
    "Claimed Decay": "宣告衰退率",
    "Claimed Unit Cost": "宣告單位成本",
    
    "Fake EV": "假 EV (豆腐渣工程)",
    "Fake EV Investigation": "假 EV 調查 (金流查核)",
    "EV Loss": "EV 損失",
    
    "Media Censorship": "媒體審查與言論控制",
    "Education Policy (Left: Rote | Right: Critical)": "教育方針 (左: 填鴨愚民 | 右: 批判思考)",
    "Media Control": "媒體識讀與控制",
    "Campaign": "公關與造勢活動",
    "Incite Emotion": "煽動選民情緒",
    "Investigate Fin.": "調查金流",
    "Hide Fin.": "隱藏金流",
    
    "Think Tank": "智庫預測處",
    "Intelligence": "情報調查處",
    "Media Dept": "黨媒公關處",
    "Counter-Intel": "反情報與隱蔽處",
    "Engineering": "工程建設處",
    "Edu Dept": "教育處",
    "Propaganda Value": "宣傳量",
    "Investigation Value": "調查值",
    "Counter-Intel Value": "反情報值",
    "Engineering Value": "工程值",
    "Education Value": "教育值",
    
    "Current Draft Preview": "當前草案預覽",
    "Opponent Draft Ref.": "對手草案參考",
    "Ruling Party Decision": "執政黨最終裁決",
    "Final Decision (H-System Only)": "最終決定 (僅限執行系統)",
    "Think Tank Analysis Report": "智庫分析報告",
    "Our Est. Net Profit": "我方預估淨利",
    "Opp. Est. Net Profit": "對手預估淨利",
    "Total Expected Support": "預估獲得總支持度",
    "Expected GDP Shift": "預期 GDP 變化",
    "Drop Analysis": "衰退宣告分析",
    "Unit Cost Analysis": "單位成本分析",
    
    "Our Total:": "我方總和:",
    "Opp. Total:": "對手總和:",
    "Base:": "大環境:",
    "Proj:": "專案:",
    
    "Honest and Accurate": "誠實且精準",
    "Medium Expectation Gap": "中度預期落差",
    "Warning! Opponent is manipulating expectations!": "警告！對手正在操縱預期數值！",
    "Sir, this is our contrast bonus strategy.": "長官，這是我們為了製造反差紅利的策略。",
    
    "Available Net Assets": "可用淨資產",
    "Est.": "預估",
    "Round:": "回合：",
    "Year": "年",
    "Support:": "支持度:",
    "Share": "佔比",
    "Waiting for opponent's draft...": "等待對手提出草案...",
    "Waiting for ruling party...": "等待執政黨裁決...",
    "Waiting for opponent confirmation...": "等待對手確認..."
}

def t(text, fallback=None):
    if not isinstance(text, str): return text
    lang = st.session_state.get('lang', 'EN')
    if lang == 'EN':
        text = text.replace("切換至繁體中文", "Switch to Chinese")
        text = text.replace("執行系統", "Executive").replace("監管系統", "Regulator")
        return text

    if text in EXACT_MATCH_DICT: return EXACT_MATCH_DICT[text]
    protected_map = {
        "GDP": "__PROTECT_GDP__",
        "ROI": "__PROTECT_ROI__",
        "H-System": "執行系統",
        "R-System": "監管系統",
        "Executive": "執行系統",
        "Regulator": "監管系統",
        "EV": "__PROTECT_EV__"
    }
    
    for en_word, placeholder in protected_map.items():
        text = text.replace(en_word, placeholder)

    for en_phrase, zh_phrase in DYNAMIC_REPLACEMENTS.items():
        text = text.replace(en_phrase, zh_phrase)

    text = text.replace("__PROTECT_GDP__", "GDP")
    text = text.replace("__PROTECT_ROI__", "ROI")
    text = text.replace("__PROTECT_EV__", "EV")

    return text
