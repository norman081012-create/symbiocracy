# ==========================================
# i18n.py
# Simplified dummy i18n to ensure completely English environment
# ==========================================
import streamlit as st

def t(zh_text, en_text=None):
    # Since all texts in code have been localized to English natively, 
    # we just return the primary argument (which is now English).
    # If en_text was still explicitly provided, we return it.
    if en_text is not None:
        return en_text
    return zh_text
