import config
import formulas
import engine
import random

def sync_party_names(game, cfg):
    game.party_A.name = cfg['PARTY_A_NAME']; game.party_B.name = cfg['PARTY_B_NAME']

def render_global_settings(cfg, game):
    st.sidebar.title("⚙️ 全域變數控制台")
    with st.sidebar.expander("📝 動態調整遊戲參數", expanded=False):
    st.sidebar.title("🎛️ 控制台")
    with st.sidebar.expander("📝 參數調整(即時)", expanded=False):
        for key, default_val in config.DEFAULT_CONFIG.items():
            label = config.CONFIG_TRANSLATIONS.get(key, key)
            if 'COLOR' in key: cfg[key] = st.color_picker(label, value=cfg[key], key=f"cfg_{key}")
@@ -38,15 +39,14 @@ def render_dashboard(game, view_party, cfg, is_preview=False, preview_data=None)
    with c1:
        st.markdown("### 🌐 國家總體現況")
        san_chg = (disp_san - rep['old_san']) * 100 if rep else 0
        st.markdown(f"**公民識讀:** `{config.get_civic_index_text(disp_san)}` *(變動: {san_chg:+.1f})*")
        st.markdown(f"**資訊辨識:** `{config.get_civic_index_text(disp_san)}` *(變動: {san_chg:+.1f})*")
        emo_chg = disp_emo - rep['old_emo'] if rep else 0
        st.markdown(f"**選民情緒:** `{config.get_emotion_text(disp_emo)}` *(變動: {emo_chg:+.1f})*")
        if is_preview:
            st.markdown(f"**預估 GDP:** `{disp_gdp:.0f}` *(變動: {disp_gdp - game.gdp:+.0f})*")
        else:
            t_gdp = st.session_state.turn_data.get('target_gdp', 0) if game.year > 1 else 0
            st.markdown(f"**當前 GDP:** `{disp_gdp:.1f}` *(變動: {disp_gdp - rep['old_gdp'] if rep else 0:+.0f})*")
            st.caption(f"目標: {t_gdp:.0f} | 表現: {config.get_target_eval_text(disp_gdp, t_gdp)}")

    with c2:
        st.markdown("### 💰 執行系統資源")
@@ -56,34 +56,44 @@ def render_dashboard(game, view_party, cfg, is_preview=False, preview_data=None)
            st.markdown(f"**總預算池:** `{disp_budg:.0f}` *(變動: {disp_budg - rep['old_budg'] if rep else 0:+.0f})*")
            t_h = st.session_state.turn_data.get('target_h_fund', 0) if game.year > 1 else 0
            st.markdown(f"**獎勵基金:** `{disp_h_fund:.0f}` *(佔比: {current_h_ratio:.1f}%)*")
            if not is_preview: st.caption(f"目標: {t_h:.0f} | 表現: {config.get_target_eval_text(disp_h_fund, t_h)}")

    with c3:
        st.markdown("### 🕵️ 智庫機密通報")
        st.markdown("### 🕵️ 智庫")
        fc = view_party.current_forecast
        acc = min(100, int((view_party.predict_ability / cfg['MAX_ABILITY']) * 100))
        st.info(f"經濟預估: **{config.get_economic_forecast_text(fc)}**\n*(預估衰退值: -{fc:.2f})*\n準確度: {acc}%")
        
        st.info(f"經濟預估: {config.get_economic_forecast_text(fc)}\n\n(預估衰退值: -{fc:.2f})\n\n準確度: {acc}%")
        if rep:
            st.markdown("**=== 判讀結果 ===**")
            st.markdown("**去年真實VS 預估衰退**")
            diff = abs(rep['view_party_forecast'] - rep['real_decay'])
            st.write(f"結果: {config.get_thinktank_eval(view_party.predict_ability, diff)}")
            st.write(f"真: {rep['real_decay']:.2f} | 估: {rep['view_party_forecast']:.2f}")
            eval_txt = config.get_thinktank_eval(view_party.predict_ability, diff)
            st.markdown(f"**判讀結果:** {eval_txt}")
            st.markdown(f"**去年真實VS預估衰退:** 真: -{rep['real_decay']:.2f} / 估: -{rep['view_party_forecast']:.2f}")

    with c4:
        st.markdown("### 📊 智庫行動預測" if game.phase == 2 else "### 📊 智庫行動預測(鎖定)")
        if is_preview:
            my_is_h = view_party.name == game.h_role_party.name
            my_net = preview_data['h_inc'] if my_is_h else preview_data['r_inc']
            opp_net = preview_data['r_inc'] if my_is_h else preview_data['h_inc']
            my_roi = preview_data['h_roi'] if my_is_h else preview_data['r_roi']
            opp_roi = preview_data['r_roi'] if my_is_h else preview_data['h_roi']
            st.success(f"🟢 **我方收益:** {my_net:.0f} (ROI: {my_roi:.1f}%)\n\n支持度: {preview_data['my_sup_shift']:+.2f}%")
            st.error(f"🔴 **對手收益:** {opp_net:.0f} (ROI: {opp_roi:.1f}%)\n\n支持度: {preview_data['opp_sup_shift']:+.2f}%")
        if game.phase == 1:
            st.markdown("### 📊 財報")
            total_maint = sum([formulas.get_ability_maintenance(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.edu_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
            st.write(f"可用淨資產: {int(view_party.wealth + total_maint)} - 維護成本: {int(total_maint)} = **{int(view_party.wealth)}**")
            
            if rep:
                my_is_h = view_party.name == rep['h_party_name']
                real_inc = rep['h_inc'] if my_is_h else rep['r_inc']
                est_inc = rep['est_h_inc'] if my_is_h else rep['est_r_inc']
                pol_cost = view_party.last_acts.get('policy', 0)
                
                st.write(f"淨利: 真:{real_inc:.0f} (去年估:{est_inc:.0f})")
                st.write(f"去年政治成本: {pol_cost:.0f} 維護成本: {total_maint:.0f}")
                final_profit = real_inc - pol_cost - total_maint
                st.write(f"{cfg['CALENDAR_NAME']} {game.year-1} 年度收益: {real_inc:.0f} - {pol_cost:.0f} - {total_maint:.0f} = **{final_profit:.0f}**")
            else: st.write("尚無去年財報資料。")
        else:
            st.write("進入 Phase 2 調整拉桿以檢視。")

            st.markdown("### 📊 智庫/情報預測")
            if is_preview:
                my_is_h = view_party.name == game.h_role_party.name
                my_net = preview_data['h_inc'] if my_is_h else preview_data['r_inc']
                opp_net = preview_data['r_inc'] if my_is_h else preview_data['h_inc']
                my_roi = preview_data['h_roi'] if my_is_h else preview_data['r_roi']
                st.success(f"🟢 **我方預估收益:** {my_net:.0f} (ROI: {my_roi:.1f}%)\n\n支持度變化: {preview_data['my_sup_shift']:+.2f}%")
                st.error(f"🔴 **對手預估收益:** {opp_net:.0f}\n\n支持度變化: {preview_data['opp_sup_shift']:+.2f}%")
    st.markdown("---")

def render_message_board(game):
@@ -92,49 +102,11 @@ def render_message_board(game):
        st.session_state.news_flash = None

    if game.phase == 1:
        if game.year == 1: st.info("🏛️ **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商。")
        if game.year == 1: st.info("📢 **【年度通報】** 新的一年開始了，國家百廢待舉，請盡快展開預算與目標協商。")
        elif game.last_year_report:
            rep = game.last_year_report
            gdp_diff = ((game.gdp - rep['old_gdp']) / max(1.0, rep['old_gdp'])) * 100
            gdp_str = f"成長 {gdp_diff:.1f}%" if gdp_diff >= 0 else f"衰退 {abs(gdp_diff):.1f}%"
            h_str = "達標" if rep['h_perf'] >= 0 else f"落後 {abs(rep['h_perf']):.1f}%"
            st.info(f"🏛️ **【年度通報】** 回顧去年，GDP {gdp_str}，執行系統目標 {h_str}。請擬定今年的預算草案。")
            st.info(f"📢 **【年度通報】** 新的一年開始了，請盡快展開預算與目標協商。")
    elif game.phase == 2:
        st.info("🛠️ **【策略建議】** 法案已通過，請分配黨產資金進行內部升級、競選造勢與媒體攻防。")

def get_maint_cost(ability, cfg):
    return max(0, (ability - 3.0) * cfg['MAINTENANCE_RATE'])

def render_strategic_intelligence_center(party, cfg, is_self=True, blur=0.0):
    total_maint = sum([get_maint_cost(a, cfg) for a in [party.build_ability, party.investigate_ability, party.edu_ability, party.media_ability, party.predict_ability]])
    total_cost = party.last_acts['policy'] + party.last_acts['legal'] + total_maint
    
    if is_self:
        st.markdown("##### 📊 內部審計局")
        st.write(f"**可用淨資產:** `{party.wealth:.0f}` - `維護成本 {total_maint:.0f}` = **{party.wealth - total_maint:.0f}**")
        
        if party.last_income_real > 0 or party.last_pol_cost > 0 or total_maint > 0:
            net_income = party.last_income_real - party.last_pol_cost - party.last_maint_cost
            st.write(f"**淨利:** 真:{party.last_income_real:.0f} (去年估:{party.last_income_est:.0f}) | 去年政治成本: {party.last_pol_cost:.0f} | 維護成本: {party.last_maint_cost:.0f}")
            st.write(f"**{cfg['CALENDAR_NAME']}(去年)年度收益:** `{party.last_income_real:.0f} - {party.last_pol_cost:.0f} - {party.last_maint_cost:.0f} = {net_income:.0f}`")
    else:
        st.markdown("##### 🕵️ 國家情報局 (對手情資還原)")
        import random
        rng = random.Random(f"intel_{party.name}")
        est_wealth = rng.uniform(max(0, party.wealth * (1 - blur)), party.wealth * (1 + blur))
        est_cost = rng.uniform(max(0, total_cost * (1 - blur)), total_cost * (1 + blur))
        st.write(f"**估算可用資產:** `約 {est_wealth:.0f}` - `維護估算 {total_maint*(1-blur):.0f}` = **約 {est_wealth - total_maint*(1-blur):.0f}**")
        st.progress(1.0 - blur, text=f"情報準確度: {int((1.0 - blur)*100)}%")

def get_poll_str(party):
    if not party.poll_history: return "??? (需作民調)"
    latest = party.poll_history[-1]['result']
    for t in ['大', '中', '小']:
        polls = [p['result'] for p in party.poll_history if p['type'] == t]
        if polls:
            avg = sum(polls) / len(polls)
            return f"{latest:.1f}%(最新民調) ({len(polls)}次{t}型民調平均: {avg:.1f}%)"
    return f"{latest:.1f}%(最新民調)"
        st.info("📢 **【年度通報】** 法案已通過，請分配黨產資金進行內部升級、競選造勢與媒體攻防。")

def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
    st.header("👤 玩家頁面")
@@ -153,86 +125,85 @@ def render_party_cards(game, view_party, god_mode, is_election_year, cfg):
            is_h = (game.h_role_party.name == party.name)
            role_badge = "🛡️ [執行系統]" if is_h else "⚖️ [監管系統]"
            is_winner = (game.ruling_party.name == party.name)
            crown = "👑" if is_winner else ""
            crown = "👑 當權派" if is_winner else "🎯 在野派"
            logo = config.get_party_logo(party.name)

            eye = "👁️ " if party.name == view_party.name else ""
            st.markdown(f"## {eye}{logo} {party.name} {crown}")
            st.markdown(f"#### {role_badge}")

            if is_election_year or god_mode: 
                disp_sup = f"📊 支持度: {party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
                disp_sup = f"{party.support:.1f}%" + (" 🏆(當選!)" if is_winner else " 💀(落選)")
            else:
                disp_sup = f"📊 支持度: {get_poll_str(party)}"
                if party.latest_poll is not None:
                    best_type = None
                    for t in ['大型', '中型', '小型']:
                        if len(party.poll_history[t]) > 0:
                            best_type = t
                            break
                    if best_type:
                        avg = sum(party.poll_history[best_type]) / len(party.poll_history[best_type])
                        count = len(party.poll_history[best_type])
                        disp_sup = f"{party.latest_poll:.1f}%(最新民調) ({count}次{best_type}民調平均: {avg:.1f}%)"
                    else:
                        disp_sup = f"{party.latest_poll:.1f}%(最新民調)"
                else:
                    disp_sup = "??? (需作民調)"
            
            st.markdown(f"### 📊 支持度: {disp_sup}")

            blur = 1.0 - (view_party.investigate_ability / cfg['MAX_ABILITY']) if not god_mode else 0.0
            if party.name == view_party.name and not is_election_year:
                b1, b2, b3 = st.columns(3)
                if b1.button("小民調 ($5)", key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5); st.rerun()
                if b2.button("中民調 ($10)", key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10); st.rerun()
                if b3.button("大民調 ($20)", key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20); st.rerun()

            if party.name == view_party.name: 
                st.markdown(f"## 👁️ {party.name} {crown} {role_badge}")
                st.markdown(f"### {disp_sup}")
                st.markdown("#### 🏛️ 戰略情報中心")
                render_strategic_intelligence_center(party, cfg, is_self=True)
                
                if not is_election_year:
                    st.markdown("<div style='text-align: center'>", unsafe_allow_html=True)
                    st.caption("*(民調可做多次增加準確性)*")
                    b_cols = st.columns([1, 2, 2, 2, 1])
                    if b_cols[1].button("小民調 ($5)", key=f"p1_{party.name}"): engine.execute_poll(game, view_party, 5, "小"); st.rerun()
                    if b_cols[2].button("中民調 ($10)", key=f"p2_{party.name}"): engine.execute_poll(game, view_party, 10, "中"); st.rerun()
                    if b_cols[3].button("大民調 ($20)", key=f"p3_{party.name}"): engine.execute_poll(game, view_party, 20, "大"); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            else: 
                st.markdown(f"## {party.name} {crown} {role_badge}")
                st.markdown(f"### {disp_sup}")
                st.markdown("#### 🏛️ 戰略情報中心")
                render_strategic_intelligence_center(party, cfg, is_self=False, blur=blur)
def render_sidebar_intel_audit(game, view_party, cfg):
    opp = game.party_B if view_party.name == game.party_A.name else game.party_A
    st.markdown("---")
    st.title("🕵️ 情報處")
    blur = max(0.0, 1.0 - (view_party.investigate_ability / max(0.1, opp.stealth_ability))) if not st.session_state.get('god_mode') else 0.0
    acc = int((1.0 - blur)*100)
    st.progress(1.0 - blur, text=f"準確度: {acc}%")
    rng = random.Random(f"intel_{opp.name}_{game.year}")
    
    with st.expander("對手各項能力", expanded=True):
        st.write(f"建設能力: {opp.build_ability*(1+rng.uniform(-blur, blur)):.1f}")
        st.write(f"調查能力: {opp.investigate_ability*(1+rng.uniform(-blur, blur)):.1f}")
        st.write(f"教育能力: {opp.edu_ability*(1+rng.uniform(-blur, blur)):.1f}")
        st.write(f"媒體操控: {opp.media_ability*(1+rng.uniform(-blur, blur)):.1f}")
        st.write(f"隱密能力: {opp.stealth_ability*(1+rng.uniform(-blur, blur)):.1f}")
    with st.expander("對手去年各項花費"):
        st.write(f"政策投入: {opp.last_acts.get('policy',0)*(1+rng.uniform(-blur, blur)):.0f}")

    st.markdown("---")
    st.title("📈 審計處")
    total_maint = sum([formulas.get_ability_maintenance(a, cfg) for a in [view_party.build_ability, view_party.investigate_ability, view_party.edu_ability, view_party.media_ability, view_party.predict_ability, view_party.stealth_ability]])
    with st.expander("自身各項能力及維護費", expanded=True):
        st.write(f"建設:{view_party.build_ability:.1f} | 調查:{view_party.investigate_ability:.1f}")
        st.write(f"教育:{view_party.edu_ability:.1f} | 媒體:{view_party.media_ability:.1f}")
        st.write(f"預測:{view_party.predict_ability:.1f} | 隱密:{view_party.stealth_ability:.1f}")
        st.write(f"**明年維護費估算:** -${total_maint:.0f}")
    with st.expander("自身去年各項花費"):
        st.write(f"政治花費: ${view_party.last_acts.get('policy',0):.0f}")

def render_proposal_component(title, plan, game, view_party, cfg):
    st.markdown(f"#### {title}")
    st.markdown(f"**公告衰退:** {plan['claimed_decay']:.2f} | **目標 GDP 成長:** {plan['target_gdp_growth']}%")
    st.markdown(f"**標案利潤:** {plan['r_value']:.2f} | **標案達標付款:** {plan['target_h_fund']}")
    
    st.markdown(f"""
    <div style="font-family: sans-serif; margin: 10px 0;">
        <span style="font-size: 1.2em;">監管出資 </span>
        <span style="font-size: 1.5em; font-weight: bold;">{plan['r_pays']}</span>
        <span style="font-size: 1.0em;"> ({(plan['r_pays']/max(1, plan['total_funds'])*100):.1f}%)</span>
        <span style="font-size: 1.2em;"> / </span>
        <span style="font-size: 1.8em; font-weight: bold; color: #E63946;">總額: {plan['total_funds']}</span>
        <span style="font-size: 1.2em;"> / </span>
        <span style="font-size: 1.2em;">執行出資 </span>
        <span style="font-size: 1.5em; font-weight: bold;">{plan['h_pays']}</span>
        <span style="font-size: 1.0em;"> ({(plan['h_pays']/max(1, plan['total_funds'])*100):.1f}%)</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    p_gdp_pct, p_h_g, p_h_n, p_r_g, p_r_n, p_h_sup, p_r_sup, p_est_gdp, p_est_h_fund, p_h_roi, p_r_roi = formulas.calculate_preview(
        cfg, game, plan['total_funds'], plan['h_ratio'], plan['r_value'], 
        view_party.current_forecast, game.h_role_party.build_ability, plan['r_pays'], plan['h_pays']
    )
    
    my_is_h = (view_party.name == game.h_role_party.name)
    my_net, my_sup, my_roi = (p_h_n, p_h_sup, p_h_roi) if my_is_h else (p_r_n, p_r_sup, p_r_roi)
    opp_net, opp_sup, opp_roi = (p_r_n, p_r_sup, p_r_roi) if my_is_h else (p_h_n, p_h_sup, p_h_roi)
    
    st.markdown("📊 **👁️ 本黨智庫推演報告:**")
    st.info(f"""
    1. 我方預估收益: `{my_net:.0f}` (ROI: {my_roi:.1f}%)
    2. 對方預估收益: `{opp_net:.0f}` (ROI: {opp_roi:.1f}%)
    3. 支持度預估: 變動 `{my_sup:+.2f}%` (對手: `{opp_sup:+.2f}%`)
    4. GDP 預估: `{game.gdp:.0f} ➔ {p_est_gdp:.0f}` ({p_gdp_pct:+.2f}%)
    """)
    st.write(f"公告衰退: {plan['claimed_decay']:.2f} | 目標 GDP 成長: {plan['target_gdp_growth']}%")
    st.write(f"總額: {plan['total_funds']} (監管出資: {plan['r_pays']} | 執行出資: {plan['h_pays']})")

def ability_slider(label, key, current_val, wealth, cfg):
    maint = max(0, (current_val - 3.0) * cfg['MAINTENANCE_RATE'])
    default_val = min(int(maint), int(wealth))
    invest = st.slider(f"{label} (當前: {current_val*10:.0f}%)", 0, int(wealth), default_val, key=key)
    
    gain = formulas.calc_log_gain(invest - maint)
    next_val = max(3.0, current_val + gain) if invest >= maint else max(3.0, current_val - ((maint - invest) * 0.02))
    next_maint = max(0, (next_val - 3.0) * cfg['MAINTENANCE_RATE'])
    t_val = st.slider(f"{label} (當前: {current_val:.1f})", 3.0, 10.0, float(current_val), 0.1, key=key)
    cost = formulas.calculate_upgrade_cost(current_val, t_val)
    maint = formulas.get_ability_maintenance(t_val, cfg)

    if invest < maint:
        st.caption(f"📉 投入不足維護 (${int(maint)})，降至: {next_val*10:.1f}% | 明年維護 ${int(next_maint)}")
    if t_val > current_val:
        st.caption(f"📈 升級花費: ${int(cost)} | 明年維護 ${int(maint)}")
    elif t_val < current_val:
        st.caption(f"📉 免費降級 | 明年維護降至 ${int(maint)}")
    else:
        st.caption(f"📈 已達維護 (${int(maint)})，升至: {min(100.0, next_val*10):.1f}% | 明年維護 ${int(next_maint)}")
    return invest
        st.caption(f"穩定維持 | 明年維護 ${int(maint)}")
    return t_val, cost

def add_event_vlines(fig, history_df):
    for _, row in history_df.iterrows():
@@ -245,12 +216,12 @@ def render_endgame_charts(history_data, cfg):
    st.title("🏁 遊戲結束！共生內閣軌跡總結算")
    df = pd.DataFrame(history_data)

    st.subheader("📊 1. 總體經濟與公民識讀指數走勢")
    st.subheader("📊 1. 總體經濟與資訊辨識指數走勢")
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['GDP'], name="總 GDP", line=dict(color='blue', width=3)), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity']*100, name="公民識讀 (0-100)", line=dict(color='purple', width=3)), secondary_y=True)
    fig1.add_trace(go.Scatter(x=df['Year'], y=df['Sanity']*100, name="資訊辨識 (0-100)", line=dict(color='purple', width=3)), secondary_y=True)
    fig1.update_yaxes(title_text="GDP (資金)", secondary_y=False)
    fig1.update_yaxes(title_text="識讀指數", secondary_y=True, range=[0, 100])
    fig1.update_yaxes(title_text="辨識指數", secondary_y=True, range=[0, 100])
    add_event_vlines(fig1, df)
    st.plotly_chart(fig1, use_container_width=True)
