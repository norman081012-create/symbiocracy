# ==========================================
# i18n.py
# Responsible for multi-language text switching dictionary for the entire system
# ==========================================
import streamlit as st

TRANSLATIONS = {
    # Translations are now natively in English directly in the UI components
}

def t(zh_text, en_text=None):
    # Simply returning the English string directly
    lang = st.session_state.get('lang', 'ZH')
    if en_text is not None: return en_text
    return zh_text
