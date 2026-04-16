# ==========================================
# i18n.py
# 攔截器版本：全自動中英翻譯轉換 (保護 GDP & ROI)
# ==========================================
import streamlit as st
import re

# ==========================================
# 1. 靜態精確比對字典 (針對完全固定的 UI 字串)
# ==========================================
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

# ==========================================
# 2. 動態關鍵字替換字典 (處理 f-string 組合或長句子)
# 優先替換長句子，再替換短詞彙，避免翻譯衝突
# ==========================================
DYNAMIC_REPLACEMENTS = {
    # 系統與階段
    "Symbiocracy Simulator v3.0.0": "共生體制模擬器 v3.0.0",
    "Phase 1: R-System Proposal": "第一階段：監管系統 (Regulator) 提案",
    "Phase 2: Execution - Turn:": "第二階段：政策執行 - 輪到：",
    "Phase 3: Annual Resolution Report": "第三階段：年度結算與社會影響報告",
    "Game Over! Final Symbiocracy Summary": "🏁 遊戲結束！共生體制最終歷史結算",
    
    # 年度通知與廣播
    "[ANNUAL NOTICE]": "[年度通知]",
    "A new year begins. The nation awaits rebuilding; initiate budget negotiations immediately.": "新的一年開始了。百廢待舉，請立即展開預算協商。",
    "A new year begins. Initiate budget negotiations.": "新的一年開始了。請展開預算協商。",
    
    # 角色與選舉狀態
    "Ruling": "當權",
    "Candidate": "候選",
    "(Won!)": "(勝選!)",
    "(Lost)": "(敗選)",
    
    # 儀表板與面板
    "National Status": "國家總體狀態",
    "Executive Resources": "執行系統資源池",
    "Think Tank Intel": "智庫情報分析",
    "Financial Report": "財務收支報告",
    "Party Overview": "政黨狀態總覽",
    "Control Panel": "控制面板",
    "Economy & Finance": "經濟與財政結算",
    "Society & Opinion": "社會與民意變化",
    "Support Shift Resolution": "民意支持度板塊位移",
    
    # 專有名詞與屬性
    "Total Budget Pool": "國家總預算池",
    "Reward Fund": "執行系統專案獎金",
    "Civic Literacy": "公民素養 (理性)",
    "Voter Emotion": "選民情緒 (狂熱)",
    "Party Wealth": "政黨資金",
    "Total Plan Reward (Max=Budget)": "專案總獎金 (上限=總預算)",
    "Plan Total Benefit (Construction Volume)": "專案總效益 (建設規模/產值)",
    "R-Pays": "監管方墊付款",
    "H-Pays": "執行方自籌款",
    "Total Req. Cost": "專案總需成本",
    "Claimed Decay": "宣告衰退率",
    "Claimed Unit Cost": "宣告單位成本",
    
    # 動作與部門
    "Secret Corruption ($)": "隱蔽貪污金額 ($)",
    "Cronyism ($)": "圖利特定廠商 ($)",
    "Media Censorship (0~100)": "媒體審查與言論控制 (0~100)",
    "Education Policy (Left: Rote | Right: Critical)": "教育方針 (左: 填鴨愚民 | 右: 批判思考)",
    "Media Control ($)": "媒體識讀與控制 ($)",
    "Campaign ($)": "公關與造勢活動 ($)",
    "Incite Emotion ($)": "煽動選民情緒 ($)",
    
    "Think Tank": "智庫預測部",
    "Intelligence": "情報調查部",
    "Media Dept": "公關媒體部",
    "Counter-Intel": "反情報與隱蔽部",
    "Engineering": "工程建設部",
    
    # 提案與預覽
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
    
    # 支持度明細
    "Our Total:": "我方總和:",
    "Opp. Total:": "對手總和:",
    "Base:": "大環境:",
    "Proj:": "專案:",
    
    # 智庫評價
    "Honest and Accurate": "誠實且精準",
    "Medium Expectation Gap": "中度預期落差",
    "Warning! Opponent is manipulating expectations!": "警告！對手正在操縱預期數值！",
    "Sir, this is our contrast bonus strategy.": "長官，這是我們為了製造反差紅利的策略。",
    
    # 其他零碎詞彙
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
    """
    核心翻譯攔截器
    """
    if not isinstance(text, str):
        return text

    # 取得當前語言，預設為 EN (英文)
    lang = st.session_state.get('lang', 'EN')
    if lang == 'EN':
        # 如果是英文模式，把中文標籤替換成英文
        text = text.replace("切換至繁體中文", "Switch to Chinese")
        text = text.replace("執行系統", "Executive").replace("監管系統", "Regulator")
        return text

    # ==========================================
    # 中文模式處理流程
    # ==========================================

    # 1. 檢查是否在靜態字典中 (完美符合)
    if text in EXACT_MATCH_DICT:
        return EXACT_MATCH_DICT[text]

    # 2. 保護免翻名詞：將 GDP、ROI 等替換為亂碼標籤，避免後續被誤翻
    # 這裡順便把 H-System 和 R-System 替換成您要求的名稱
    protected_map = {
        "GDP": "__PROTECT_GDP__",
        "ROI": "__PROTECT_ROI__",
        "H-System": "執行系統",
        "R-System": "監管系統",
        "Executive": "執行系統",
        "Regulator": "監管系統"
    }
    
    for en_word, placeholder in protected_map.items():
        text = text.replace(en_word, placeholder)

    # 3. 動態字串替換 (掃描句子中包含的英文關鍵字並替換)
    for en_phrase, zh_phrase in DYNAMIC_REPLACEMENTS.items():
        text = text.replace(en_phrase, zh_phrase)

    # 4. 恢復受保護的名詞
    text = text.replace("__PROTECT_GDP__", "GDP")
    text = text.replace("__PROTECT_ROI__", "ROI")

    return text
