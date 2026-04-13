# ==========================================
# phase1.py
# ==========================================
import streamlit as st
import formulas
import engine

def render_thinktank_eval(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    if not plan:
        st.info("尚未發布草案。")
        return
        
    my_is_h = (view_party.name == game.h_role_party.name)
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    
    # 執行系統假設投入所有收到的錢 (plan['proj_fund']) 來做預估
    est_gdp, est_h_inc, est_r_inc, h_idx, c_net = formulas.calc_economic_preview(
        cfg, view_party.current_forecast, game.gdp, game.current_budget_pool, 
        plan['proj_fund'], plan['strictness'], game.h_role_party.depts['build'].eff
    )
    
    my_inc = est_h_inc if my_is_h else est_r_inc
    opp_inc = est_r_inc if my_is_h else est_h_inc
    my_roi = (my_inc / plan['proj_fund'] * 100) if plan['proj_fund'] > 0 else 0
    opp_roi = (opp_inc / plan['proj_fund'] * 100) if plan['proj_fund'] > 0 else 0
    
    # 簡單模擬支持度變化 (依據 ROI 或其他自訂公式，此處給予範例值)
    sup_shift = (my_roi - opp_roi) * 0.05
    gdp_pct = ((est_gdp - game.gdp) / max(1.0, game.gdp)) * 100.0

    st.markdown(f"**1. 我方預估收益:** `{my_inc:.0f}` (ROI: `{my_roi:.1f}%`)")
    st.markdown(f"**2. 對方預估收益:** `{opp_inc:.0f}` (ROI: `{opp_roi:.1f}%`)")
    st.markdown(f"**3. 支持度預估:** `{sup_shift:+.2f}%`")
    st.markdown(f"**4. 預期 GDP:** `{game.gdp:.0f} ➔ {est_gdp:.0f} (+{gdp_pct:.2f}%)`")
    
    diff = abs(plan['claimed_decay'] - view_party.current_forecast)
    if diff < 0.1: 
        light, msg = "🟢", "「對方公告的數據與本院預測高度吻合，可信度極高。」"
    elif diff < 0.3: 
        light, msg = "🟡", "「對方數據略有偏差，可能隱藏了部分風險，請謹慎評估。」"
    else: 
        light, msg = "🔴", "「嚴重警告！對方公告值與本院預估落差巨大，極大機率為政治操作！」"
    
    st.info(f"**5. 衰退值查核:** 公告 `{plan['claimed_decay']:.2f}` VS 估計 `{view_party.current_forecast:.2f}`\n\n{light} 智庫判讀: {msg}")

def render(game, view_party, cfg):
    st.subheader(f"🤝 Phase 1: 監管系統委託執行系統建設提案 (輪數: {game.proposal_count})")
    
    if game.p1_step in ['draft_r', 'draft_h', 'ultimatum_draft_r']:
        active_role = 'R' if game.p1_step in ['draft_r', 'ultimatum_draft_r'] else 'H'
        
        if view_party.name != (game.r_role_party.name if active_role == 'R' else game.h_role_party.name):
            st.warning(f"⏳ 等待對手公布草案...")
        else:
            st.markdown(f"### 📝 {view_party.name} ({'監管系統' if active_role == 'R' else '執行系統'}黨) 草案擬定室")
            
            opp_role = 'H' if active_role == 'R' else 'R'
            opp_plan = game.p1_proposals.get(opp_role)
            
            claimed_decay = st.number_input("📢 公告衰退值", value=float(view_party.current_forecast), step=0.01)
            proj_fund = st.slider("💰 投標資金 (最高不超過當年標案池)", 0.0, float(game.current_budget_pool), float(game.current_budget_pool * 0.5), 10.0)
            strictness = st.slider("⚖️ 標案實質成本 (0~3，留點賺頭給對手)", 0.0, 3.0, 1.0, 0.1)

            plan_dict = {
                'claimed_decay': claimed_decay, 'proj_fund': proj_fund, 
                'strictness': strictness, 'author': active_role
            }

            if st.button("📤 送出草案", type="primary"):
                game.p1_proposals[active_role] = plan_dict
                if game.p1_step == 'draft_r': game.p1_step = 'draft_h'; game.proposing_party = game.h_role_party
                else: game.p1_step = 'voting_pick'; game.proposing_party = game.ruling_party
                st.rerun()

            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1: render_thinktank_eval("🛡️ 依據當前草案之智庫評估", plan_dict, game, view_party, cfg)
            with c2: render_thinktank_eval("📜 對手既有草案參考", opp_plan, game, view_party, cfg)

    elif game.p1_step == 'voting_pick':
        st.markdown(f"### 🗳️ 執政黨定奪 ({game.ruling_party.name})")
        if view_party.name != game.ruling_party.name:
            st.warning("⏳ 等待執政黨定奪...")
        else:
            c1, c2 = st.columns(2)
            for idx, key in enumerate(['R', 'H']):
                plan = game.p1_proposals.get(key)
                with [c1, c2][idx]:
                    render_thinktank_eval(f"{key} 系統草案評估", plan, game, view_party, cfg)
                    if plan and st.button(f"✅ 選擇 {key} 方案", key=f"pick_{key}", use_container_width=True):
                        game.p1_selected_plan = plan; game.p1_step = 'voting_confirm'
                        game.proposing_party = game.party_B if game.ruling_party.name == game.party_A.name else game.party_A; st.rerun()

    elif game.p1_step == 'voting_confirm':
        if view_party.name != game.proposing_party.name: st.warning("⏳ 等待對手覆議...")
        else:
            render_thinktank_eval('📜 待覆議草案內容', game.p1_selected_plan, game, view_party, cfg)
            c1, c2 = st.columns(2)
            if c1.button("✅ 同意法案", use_container_width=True, type="primary"):
                st.session_state.turn_data.update(game.p1_selected_plan)
                st.session_state.news_flash = f"預算案三讀通過！"
                game.phase = 2; game.proposing_party = game.ruling_party; st.rerun()
            if c2.button("❌ 拒絕並重談", use_container_width=True):
                game.proposal_count += 1; game.p1_step = 'draft_r'; game.proposing_party = game.r_role_party; st.rerun()
