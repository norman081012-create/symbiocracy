# ==========================================
# i18n.py
# ==========================================
import streamlit as st

ZH_DICT = {
    "🎛️ Control Panel": "🎛️ 控制面板",
    "📝 Live Parameters": "📝 即時參數設定",
    "🌐 Switch to Chinese": "🌐 切換至繁體中文",
    "🌐 Switch to English": "🌐 Switch to English",
    "👁️ God Mode": "👁️ 上帝模式",
    "🔄 Restart Game": "🔄 重新開始遊戲",
    "🏛️ Symbiocracy Simulator - Game Setup": "🏛️ 共生體制模擬器 - 遊戲設定",
    "Choose Game Mode": "選擇遊戲模式",
    "Choose Your Party": "選擇你的政黨",
    "Start Simulation 🚀": "開始模擬 🚀",
    
    "National Status": "國家總體狀態",
    "Civic Literacy": "公民素養",
    "Voter Emotion": "選民情緒",
    "Executive Resources": "執行系統 (Executive) 資源池",
    "Total Budget Pool": "國家總預算池",
    "Reward Fund": "專案獎金池",
    "Think Tank Intel": "智庫情報分析",
    "Financial Report": "財務收支報告",
    "Available Net Assets": "可用淨資產",
    "Last Year Cash Flow": "去年淨現金流",
    
    "Think Tank Analysis Report": "📝 智庫分析報告",
    "Switch to Think Tank Estimate": "切換至智庫預估數值",
    "Simulate Role Swap": "模擬對方視角 (換位思考)",
    "Our Est. Net Profit": "我方預估淨利",
    "Opp. Est. Net Profit": "對手預估淨利",
    "Total Expected Support": "預估獲得總支持度",
    "Our Side": "我方",
    "Opp. Side": "對手",
    "Expected GDP Shift": "預期 GDP 變化",
    "Drop Analysis": "衰退宣告分析",
    "Unit Cost Analysis": "單位成本分析",
    "Claimed Decay": "宣告衰退率",
    "Total Plan Reward (Max=Budget-Salaries)": "專案總獎金 (上限=預算扣除薪資)",
    "Plan Total Benefit (Construction Volume)": "專案總效益 (建設規模/產值)",
    "Total Req. Cost": "專案總需成本",
    "Reg-Pays": "監管方墊付款",
    "Exec-Pays": "執行方自籌款",
    
    "Executive": "執行方 (Executive)",
    "Regulator": "監管方 (Regulator)",
    "Perf.": "政績",
    "Macro Perf.": "監管政績",
    "Proj Perf.": "執行政績",
    "Regulator Perf.": "監管政績",
    "Executive Perf.": "執行政績",
    "Spin": "公關",
    
    "Party Overview": "政黨狀態總覽",
    "Party Funds:": "政黨資金:",
    "Support:": "支持度:",
    "Est.": "預估",
    
    "Phase 1: Regulator Proposal": "第一階段：監管系統 (Regulator) 提案",
    "Regulator Draft Room": "監管方提案室",
    "Executive Draft Room": "執行方提案室",
    "⚖️ Judicial Fine Multiplier": "⚖️ 司法罰款倍率",
    "🔄 Auto-Fill Intel": "🔄 自動帶入智庫數據",
    "📤 Submit Draft": "📤 送出草案",
    "💥 Issue Ultimatum": "💥 下達最後通牒",
    "📜 Current Draft Preview": "📜 當前草案預覽",
    "📜 Opponent Draft Ref.": "📜 對手草案參考",
    "✅ Select this draft": "✅ 選擇此草案",
    "✅ Agree to Bill": "✅ 同意法案並簽署",
    "❌ Reject & Renegotiate": "❌ 拒絕並重新談判",
    "✅ Accept Ultimatum": "✅ 接受最後通牒",
    
    "Phase 2: Execution & Ops - Turn:": "第二階段：資源分配與執行 - 輪到：",
    "Operations Allocation": "資源與行動分配",
    "Intel Div.": "情報調查處",
    "Stealth & Counter-Intel Div.": "反情報與隱蔽處",
    "PR & Media Div.": "黨媒公關處",
    "Edu. Div.": "教育處",
    "Finance & Construction (EV)": "財政與工程建設 (EV)",
    "Allocate Real EV to Project": "分配真實 EV 至專案",
    "Inject Fake EV (Cost Ratio:": "注入假 EV (豆腐渣工程) 成本比:",
    "Upgrade Dept. (Target Level)": "升級部門 (目標等級)",
    "Financial Checkout": "財務結算",
    "Confirm Actions": "確認行動並執行",
    
    "Symbiocracy Times - Annual Report": "共生體制時報 - 年度結算",
    "🎲 Initiate Financial Audit": "🎲 啟動財務查核",
    "Execute Audit!": "執行查核！",
    "Front Page": "頭版頭條",
    "Economic Indicators": "經濟指標",
    "Financial Summary": "財政總結",
    "Electoral Shift": "選舉板塊位移",
    "Next Year": "進入下一年",
    
    "Game Over! Final Symbiocracy Summary": "🏁 遊戲結束！共生體制最終歷史結算"
}

def t(text):
    if not isinstance(text, str): return text
    lang = st.session_state.get('lang', 'EN')
    if lang == 'EN':
        return text

    # Exact Match
    if text in ZH_DICT: 
        return ZH_DICT[text]
    
    # Partial matching for dynamic strings
    for en_key, zh_val in ZH_DICT.items():
        if en_key in text and len(en_key) > 4:
            text = text.replace(en_key, zh_val)
            
    return text
