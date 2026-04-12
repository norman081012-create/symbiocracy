# ==========================================
# interface.py
# 負責 儀表板(儀錶盤)、通知欄與動態推演
# ==========================================
import streamlit as st
import pandas as pd
import content
import formulas

def render_dashboard(game, view_party, cfg, is_preview=False, preview_data=None):
    st.markdown(f"### {content.get_election_icon(game.year, cfg['ELECTION_CYCLE'])}")
    
    show_last = st.toggle("顯示去年對比", value=False) if game.year > 1 else False
    rep = game.last_year_report
    
    # 數據準備
    d_gdp = preview_data['gdp'] if is_preview else game.gdp
    d_san = preview_data['san'] if is_preview else game.sanity
    d_emo = preview_data['emo'] if is_preview else game.emotion
    d_h_fund = preview_data['h_fund'] if is_preview else game.h_fund
    d_budg = preview_data['budg'] if is_preview else game.total_budget

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("#### 🌐 國家總體現況")
        san_val = d_san * 100
        san_str = f"{san_val:.1f} ({san_val - (rep['old_san']*100 if rep and show_last else san_val):+.1f})" if show_last else f"{san_val:.1f}"
        st.write(f"**公民識讀:** {content.get_civic_index_text(d_san)}")
        st.write(f"**選民情緒:** {content.get_emotion_text(d_emo)}")
        
        gdp_base = rep['old_gdp'] if rep and show_last else game.gdp
        st.write(f"**當前 GDP:** `{d_gdp:.0f}` ({d_gdp - gdp_base:+.0f})")
        if rep and show_last:
            st.caption(f"判定: {content.get_performance_eval(game.gdp, rep['target_gdp'])}")

    with c2:
        st.markdown("#### 💰 執行系統資源")
        budg_base = rep['old_budg'] if rep and show_last else game.total_budget
        st.write(f"**預算池:** `{d_budg:.0f}` ({d_budg - budg_base:+.0f})")
        st.write(f"**獎勵基金:** `{d_h_fund:.0f}`")
        if rep and show_last:
            st.caption(f"判定: {content.get_performance_eval(game.h_fund, rep['target_h_fund'])}")

    with c3:
        if not is_preview:
            st.markdown("#### 🕵️ 智庫機密通報")
            fc = view_party.current_forecast
            acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
            st.info(f"經濟預估: {content.get_economic_forecast_text(fc)} (-{fc:.2f})\n\n準確度: {acc}%")
        else:
            st.markdown("#### 🔮 智庫實時預演")
            my_is_h = (view_party.name == game.h_role_party.name)
            my_inc = preview_data['h_net'] if my_is_h else preview_data['r_net']
            my_roi = preview_data['h_roi'] if my_is_h else preview_data['r_roi']
            my_sup = preview_data['h_sup'] if my_is_h else preview_data['r_sup']
            st.success(f"🟢 我方預計: `${my_inc:.0f}`\n\n(ROI: {my_roi:.1f}%) | 支持: {my_sup:+.2f}%")

    with c4:
        if not is_preview:
            st.markdown("#### 📊 智庫檢討")
            if rep:
                diff = abs(rep['view_party_forecast'] - rep['real_decay'])
                st.write(f"評語: {content.get_thinktank_eval(view_party.predict_ability, diff)}")
            else: st.info("新任期暫無數據")
        else:
            my_is_h = (view_party.name == game.h_role_party.name)
            opp_inc = preview_data['r_net'] if my_is_h else preview_data['h_net']
            opp_roi = preview_data['r_roi'] if my_is_h else preview_data['h_roi']
            opp_sup = preview_data['r_sup'] if my_is_h else preview_data['h_sup']
            st.error(f"🔴 對手預計: `${opp_inc:.0f}`\n\n(ROI: {opp_roi:.1f}%) | 支持: {opp_sup:+.2f}%")

def render_message_board(game, phase):
    with st.container():
        st.markdown("---")
        if phase == 1:
            if game.year == 1:
                st.info("🏛️ **年度通報**: 歡迎進入共生民主模擬器。首年國家百廢待舉，請監管系統先行切分標案利益，執行系統隨後選擇。")
            else:
                strategy = "建議策略: 監管系統應在標案利潤與嚴格度間取得平衡，避免激怒執行系統引發倒閣。" if game.proposing_party.name == game.r_role_party.name else "建議策略: 執行系統應檢視標案是否具備足夠 ROI，若利潤太薄，可考慮使用最後通牒。"
                st.info(f"🏛️ **年度通報**: {strategy}")
        
        if st.session_state.get('news_flash'):
            st.warning(f"🗞️ **新聞快訊**: {st.session_state.news_flash}")
