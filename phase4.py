# ==========================================
# phase4.py
# Handles Game Over and Final Summary Charts
# ==========================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import i18n
t = i18n.t

def render(game, cfg):
    st.balloons()
    st.title(t("🏁 Game Over! Symbiotic Cabinet History Final Report"))
    
    df = pd.DataFrame(game.history)
    
    # Ensure data format compatibility
    if 'Ruling' in df.columns:
        st.subheader("📊 1. Power Alternation and System Division Status")
        st.write("Examine whether the two parties exhibit a 'one-party dominance' or a rigid 'long-term refusal to alternate' phenomenon.")
        c1, c2 = st.columns(2)
        with c1:
            rule_counts = df['Ruling'].value_counts().reset_index()
            rule_counts.columns = ['Party', 'Years']
            fig_ruling = px.pie(rule_counts, names='Party', values='Years', title="Ruling Party Years Percentage", hole=0.3, color='Party', color_discrete_map={cfg['PARTY_A_NAME']: cfg['PARTY_A_COLOR'], cfg['PARTY_B_NAME']: cfg['PARTY_B_COLOR']})
            st.plotly_chart(fig_ruling, use_container_width=True)
        with c2:
            h_counts = df['H_Party'].value_counts().reset_index()
            h_counts.columns = ['Party', 'Years']
            fig_h = px.pie(h_counts, names='Party', values='Years', title="H-System (Executive) Years Percentage", hole=0.3, color='Party', color_discrete_map={cfg['PARTY_A_NAME']: cfg['PARTY_A_COLOR'], cfg['PARTY_B_NAME']: cfg['PARTY_B_COLOR']})
            st.plotly_chart(fig_h, use_container_width=True)

    st.subheader("📈 2. Macro Economy and Social Sanity Development")
    st.write("Observe if party interactions pushed the nation toward prosperity and critical thinking, or plunged it into stagnation and emotional polarization.")
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['GDP'], name="Total GDP", line=dict(color='blue', width=3)), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity'], name="Civic Literacy (0-100)", line=dict(color='purple', width=3)), secondary_y=True)
    
    for _, row in df.iterrows():
        y = row['Year']
        if row['Is_Swap']: fig1.add_vline(x=y, line_dash="dot", line_color="red", annotation_text="Swap!", annotation_position="top left")
        if row['Is_Election']: fig1.add_vline(x=y, line_dash="dash", line_color="green", annotation_text="Election", annotation_position="bottom right")

    st.plotly_chart(fig1, use_container_width=True)
    
    if 'A_Edu' in df.columns:
        st.subheader("🏛️ 3. Policy Path and Department Efficiency Evolution")
        st.write("Review the parties' preferences in educational policies (Canned vs Critical) and the average upgrade curves of internal agency abilities.")
        c3, c4 = st.columns(2)
        with c3:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=df['Year'], y=df['A_Edu'], name=f"{cfg['PARTY_A_NAME']} Party Edu Investment", marker_color=cfg['PARTY_A_COLOR']))
            fig2.add_trace(go.Bar(x=df['Year'], y=df['B_Edu'], name=f"{cfg['PARTY_B_NAME']} Party Edu Investment", marker_color=cfg['PARTY_B_COLOR']))
            fig2.update_layout(title="Historical Edu Policy Path (Neg: Canned / Pos: Critical)", barmode='group')
            st.plotly_chart(fig2, use_container_width=True)
        with c4:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df['Year'], y=df['A_Avg_Abi'], name=f"{cfg['PARTY_A_NAME']} Avg Dept Ability", line=dict(color=cfg['PARTY_A_COLOR'], width=3)))
            fig3.add_trace(go.Scatter(x=df['Year'], y=df['B_Avg_Abi'], name=f"{cfg['PARTY_B_NAME']} Avg Dept Ability", line=dict(color=cfg['PARTY_B_COLOR'], width=3)))
            fig3.update_layout(title="Internal Agency Composite Ability Evolution")
            st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("---")
    if st.button(t("🔄 Restart Game", "🔄 Restart Game"), use_container_width=True, type="primary"): 
        st.session_state.clear()
        st.rerun()
