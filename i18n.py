# ==========================================
# i18n.py
# 負責全系統的多語系文字切換 (預設英文)
# ==========================================
import streamlit as st

def t(zh_text, en_text):
    """根據當前語言回傳對應字串，預設為英文 (EN)"""
    lang = st.session_state.get('lang', 'EN')
    return zh_text if lang == 'ZH' else en_text
