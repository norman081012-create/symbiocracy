# interface.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import content

def render_global_settings(cfg):
    st.sidebar.title("⚙️ 全域變數控制台")
    with st.sidebar.expander("📝 動態調整遊戲參數 (即時連動)", expanded=False):
        for key, default_val in content.DEFAULT_CONFIG.items():
            if isinstance(default_val, float):
                cfg[key] = st.number_input(key, value=float(cfg[key]), step=0.1, format="%.2f")
            elif isinstance(default_val, int):
                cfg[key] = st.number_input(key, value=int(cfg[key]), step=1)
            elif isinstance(default_val, str):
                cfg[key] = st.text_input(key, value=str(cfg[key]))

def add_event_vlines(fig, history_df):
    """通用輔助函數：在圖表上畫出選舉年與 Swap 的垂直線"""
    for _, row in history_df.iterrows():
        y = row['Year']
        if row['Is_Swap']:
            fig.add_vline(x=y, line_dash="dot", line_color="red", annotation_text="Swap!", annotation_position="top left")
        if row['Is_Election']:
            fig.add_vline(x=y, line_dash="dash", line_color="green", annotation_text="選舉", annotation_position="bottom right")

def render_endgame_charts(history_data, cfg):
    st.balloons()
    st.title("🏁 遊戲結束！歷史軌跡總結算")
    df = pd.DataFrame(history_data)

    # ================= Chart 1: GDP vs Sanity =================
    st.subheader("📊 1. 總體經濟與社會理智度走勢")
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['GDP'], name="總 GDP", line=dict(color='blue', width=3)), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity'], name="理智度", line=dict(color='purple', width=3)), secondary_y=True)
    fig1.update_yaxes(title_text="GDP (資金)", secondary_y=False)
    fig1.update_yaxes(title_text="Sanity (0~1)", secondary_y=True, range=[0, 1.1])
    add_event_vlines(fig1, df)
    st.plotly_chart(fig1, use_container_width=True)

    # ================= Chart 2: Support vs Wealth =================
    st.subheader(f"📊 2. {cfg['PARTY_A_NAME']} 支持度與雙方資金角力")
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['A_Wealth'], name=f"{cfg['PARTY_A_NAME']} 存款", line=dict(color='cyan', dash='dash')), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['B_Wealth'], name=f"{cfg['PARTY_B_NAME']} 存款", line=dict(color='orange', dash='dash')), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df['Year'], y=df['A_Support'], name=f"{cfg['PARTY_A_NAME']} 民意支持度", line=dict(color='green', width=4)), secondary_y=True)
    fig2.update_yaxes(title_text="財富總額", secondary_y=False)
    fig2.update_yaxes(title_text="支持度 (%)", secondary_y=True, range=[0, 100])
    add_event_vlines(fig2, df)
    st.plotly_chart(fig2, use_container_width=True)

    # ================= Chart 3: Party Abilities =================
    st.subheader("📊 3. 兩黨各項硬實力成長軌跡")
    fig3 = go.Figure()
    abilities = [('Build', '建設'), ('Inv', '調查'), ('Edu', '教育'), ('Prop', '宣傳'), ('Blame', '甩鍋')]
    colors = ['#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']
    
    for i, (key, label) in enumerate(abilities):
        fig3.add_trace(go.Scatter(x=df['Year'], y=df[f'A_{key}'], name=f"A黨-{label}", line=dict(color=colors[i])))
        fig3.add_trace(go.Scatter(x=df['Year'], y=df[f'B_{key}'], name=f"B黨-{label}", line=dict(color=colors[i], dash='dot')))
    
    fig3.update_layout(yaxis_title="能力等級")
    add_event_vlines(fig3, df)
    st.plotly_chart(fig3, use_container_width=True)
