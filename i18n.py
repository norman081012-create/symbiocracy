# ==========================================
# i18n.py
# ==========================================
import streamlit as st

def t(zh_text, en_text=None):
    if en_text is not None:
        return en_text
    return zh_text
