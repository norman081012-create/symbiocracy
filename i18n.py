# ==========================================
# i18n.py
# ==========================================
import streamlit as st

TRANSLATIONS = {
    "EN": {
        "sys_exec": "Executive",
        "sys_reg": "Regulator",
        "role_exec": "🛡️ Executive",
        "role_reg": "⚖️ Regulator",
        "btn_roll_dice": "Execute Regulatory Check",
        "caught_amount": "Confiscated Funds",
        "safe_amount": "Evaded Funds",
        "fine_paid": "Fines Paid"
    },
    "ZH": {
        "sys_exec": "執行系統",
        "sys_reg": "監管系統",
        "role_exec": "🛡️ 執行系統",
        "role_reg": "⚖️ 監管系統",
        "btn_roll_dice": "執行監管擲骰",
        "caught_amount": "遭沒收金額",
        "safe_amount": "成功圖利金額",
        "fine_paid": "支付罰款"
    }
}

def t(text, fallback=None):
    # 取得目前的語系，預設為 EN
    lang = st.session_state.get('lang', 'EN')
    
    # 如果傳入的 text 存在於我們的自訂字典中，就回傳翻譯
    if text in TRANSLATIONS.get(lang, {}):
        return TRANSLATIONS[lang][text]
        
    # 如果字典裡沒有，但您原本就傳了包含中文或英文的字串，我們這裡做簡單的關鍵字替換
    # 這樣可以盡量相容您原本散落在各檔案的寫法
    if lang == 'ZH':
        text = text.replace("H-System", "執行系統").replace("R-System", "監管系統")
        text = text.replace("Executive", "執行系統").replace("Regulator", "監管系統")
    else:
        text = text.replace("執行系統", "Executive").replace("監管系統", "Regulator")
        text = text.replace("H-System", "Executive").replace("R-System", "Regulator")
        
    return text
