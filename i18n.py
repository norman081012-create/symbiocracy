import streamlit as st

I18N = {
    'English': {
        'settings': "⚙️ Global Settings (Adjust Anytime)",
        'lang': "Language:",
        'label_style': "UI Label Style:",
        'short': "Short",
        'full': "Full",
        'name_a': "Name A:",
        'name_b': "Name B:",
        'decay_range': "Decay Range:",
        'total_years': "Total Years:",
        'base_budget': "Base Budget:",
        'major_bonus': "Major Bonus:",
        'tax_impact': "Sat. Tax Impact:",
        'voter_emotion': "Voter Emotion:",
        'edu_impact': "Edu Impact:",
        'bw_impact': "BW Impact:",
        'bw_duration': "BW Duration:",
        'perf_duration': "Perf Duration:",
        'set_wealth_a': "Set Wealth A:",
        'set_wealth_b': "Set Wealth B:",
        'game_guide': "📖 Game Guide",
        'detail_level': "Detail Level:",
        'overview': "Overview",
        'how_to_play': "How to Play",
        'deep_dive': "Deep Dive",
        'guide_overview': """
### 🎮 The Simple Overview (Roleplay & Strategy)
**Welcome to Symbiocracy!**
This is a political sandbox roleplaying game. You can rename the parties, inhabit their ideologies, and see how they interact under systemic pressure.

**The Ultimate Goal:** There is no single way to win. You decide your victory condition: Amass wealth, maintain a dynasty, or maximize societal satisfaction (True-H).

**The Core Conflict (Roles):**
* 👑 **Governing Party:** The party currently in power. Receives an automatic wealth bonus.
* 🟢 **Household Role (H-Role):** Controls economic output. Reaps direct financial benefits when the H-Index is high.
* 🔵 **Regulator Role (R-Role):** Controls societal narrative. Possesses exclusive power over Education/Anti-Education.
* 🛡️ **Sovereign System (S-System):** A background system taking 10% of tax revenue to provide a fixed baseline of stability, preventing state collapse during political deadlocks.

**Your Arsenal:**
* 📚 **Edu / Anti-Edu (R-Role Only):** Alters public Rationality.
* 📺 **Brainwashing:** Temporary spike in Support.
* 🏗️ **Construction:** Boosts public Satisfaction (True-H) and H-Index.
* 🔄 **Execute Swap:** A bilateral check against malicious or incompetent behavior. Can trade H and R roles.
        """,
        'guide_how': """
### 📖 How to Play & UI Guide
1. **Assess the Year:** Check the Status Board and Newspaper.
2. **Phase 1 (Ruling):** Draft budget, set R-value, and optionally propose a Swap.
3. **Phase 2 (Opposition):** Set budget. If Ruling proposed a Swap, it's locked. Otherwise, Opposition can propose one.
4. **Phase 3 (Review):** If Opposition proposed a Swap, Ruling decides to accept or reject. Calculate Forecast and End Year.
        """,
        'guide_deep': """
### ⚙️ Deep Dive: The Mechanics
* **Baseline Reset:** Voters judge you based on improvements *after* taking office.
* **Rationality:** Amplifies how Satisfaction becomes Support.
* **Voter Emotion:** High emotion makes voters ignore real Satisfaction in favor of Brainwashing.
* **Expiry Mechanism:** Performance and Brainwashing bonuses expire over time.
        """,
        'governing': "Governing",
        'tax_revenue': "Tax Revenue",
        'election_this_year': "⚠️ Election This Year!",
        'election_next_year': "⏳ 1 Year to Election!",
        'rationality_level': "Rationality Level",
        'midpoint_decay': "Midpoint Decay",
        'swap_instruction': "(A bilateral check mechanism against governing or regulating failures)",
        'accumulated_wealth': "💰 Accumulated Wealth",
        'r_value_gov': "R-Value (Ruling Only):",
        'r_value_lock': "R-Value (LOCKED):",
        'r_explanation': "💡 **R-Value Range (1~1000):** A higher R-value makes it significantly harder for the H-Role to profit and build. A lower R-value (e.g., 1~2) makes it easier for the H-Role to profit, heavily incentivizing them to stay in the H-Role and cooperate rather than defect.",
        'execute_swap': "Propose Swap (No Confidence)",
        'execute_swap_opp': "Propose Swap (No Confidence) against Ruling Party",
        'execute_swap_lock': "Swap Executed (Locked)",
        'opp_proposed_swap': "⚠️ Opposition proposed a Swap in the previous phase! Do you accept?",
        'opp_proposed_swap_accept': "Accept Opposition's Swap Proposal",
        'ruling_locked_swap': "🔒 The Ruling Party initiated a Swap. This cannot be canceled.",
        'show_real_decay': "Show Real Decay",
        'current_real_decay': "Current Real Decay:",
        'hidden': "*** HIDDEN ***",
        'confirm_btn': "Confirm & End Year",
        'calc_btn': "Calculate Forecast",
        'edu': "Education",
        'anti': "Anti-Education",
        'brain': "Brainwashing",
        'cons': "Construction",
        'max': "Max",
        'not_r': "Not R-Role",
        'waste_warn': "Funds placed in Edu/Anti will be wasted due to Swap.",
        'forecast_header': "Forecast Results:",
        'expected_income': "Expected {0} Income:",
        'support_change': "Support Change:",
        'view_breakdown': "🧮 View Breakdown",
        'h_inc': "Household Income",
        'r_inc': "Regulator Income",
        'total_inc': "Total Income",
        'bonus': "Bonus",
        'sim_fin': "=== Simulation Finished! ===",
        'restart': "Restart Game",
        'turn_p0': "Phase 1: Ruling Party Drafts Proposal",
        'turn_p1': "Phase 2: Opposition Reacts",
        'turn_p2': "Phase 3: Final Review",
        'btn_submit_prop': "Submit Proposal to Opposition",
        'btn_submit_react': "Submit Reaction",
        'btn_revise': "Revise Proposal (Back to Phase 1)",
        'wait_opp': "Waiting for Opposition...",
        'yr': "Year",
        'warn_exp': "⚠️ Budget Exceeded!"
    },
    '中文': {
        'settings': "⚙️ 全域設定 (隨時可調)",
        'lang': "語言:",
        'label_style': "UI 標籤樣式:",
        'short': "簡稱",
        'full': "全名",
        'name_a': "A黨名稱:",
        'name_b': "B黨名稱:",
        'decay_range': "衰退範圍:",
        'total_years': "總年數:",
        'base_budget': "基礎預算:",
        'major_bonus': "執政津貼:",
        'tax_impact': "滿意度稅收影響:",
        'voter_emotion': "選民情緒:",
        'edu_impact': "教育影響力:",
        'bw_impact': "洗腦影響力:",
        'bw_duration': "洗腦持續時間:",
        'perf_duration': "政績持續時間:",
        'set_wealth_a': "設定A黨財富:",
        'set_wealth_b': "設定B黨財富:",
        'game_guide': "📖 遊戲指南",
        'detail_level': "詳細程度:",
        'overview': "簡介 (Overview)",
        'how_to_play': "玩法 (How to Play)",
        'deep_dive': "深度機制 (Deep Dive)",
        'guide_overview': """
### 🎮 簡介與角色扮演策略
這是一個政治沙盒遊戲。你可以決定自己的勝利條件：累積私人財富、維持執政王朝，或最大化社會滿意度。

**核心衝突 (角色分配)：**
* 👑 **執政黨:** 當前掌權的政黨。每年自動獲得財富津貼。
* 🟢 **Household 角色 (H-Role):** 控制即時經濟產出。H-Index 高時能獲得直接財務利益。
* 🔵 **Regulator 角色 (R-Role):** 控制社會敘事。擁有專屬權力使用教育與反智。
* 🛡️ **S System (主權系統):** 系統底層防線，強制抽取10%稅收以提供國家生存與基礎安全，防止政治僵局導致國家崩盤。

**你的武器庫：**
* 📚 **教育/反智 (僅限 R-Role):** 改變公眾理智度。
* 📺 **洗腦:** 提供暫時性支持度飆升。
* 🏗️ **建設:** 提升公眾滿意度與 H-Index。
* 🔄 **執行交換 (Swap):** 雙向制衡機制，用以防範 R 方（規則制定）或 H 方（治理）發生惡意或無能的失職。
        """,
        'guide_how': """
### 📖 玩法指南
1. **階段 1 (執政黨提案):** 分配預算、設定 R 值。執政黨可選擇發起 Swap。
2. **階段 2 (在野黨回應):** 分配預算。若執政黨已發起 Swap，則在野黨無法取消（強制鎖定）；若無，在野黨可在此時發起 Swap。
3. **階段 3 (最終審查):** 若在野黨發起了 Swap，執政黨需決議是否接受。雙方確認無誤後結束本年。
        """,
        'guide_deep': """
### ⚙️ 深度機制
* **基準點重置:** 選民只在乎你就任後的「進步幅度」。
* **理智度與情緒:** 理智度越高越看重真實政績；情緒越高越容易被洗腦操弄。
* **過期機制:** 政績與洗腦帶來的支持度都有保存期限。
        """,
        'governing': "當前執政",
        'tax_revenue': "當前稅收",
        'election_this_year': "⚠️ 今年是選舉年！",
        'election_next_year': "⏳ 距離選舉剩 1 年！",
        'rationality_level': "社會理智度",
        'midpoint_decay': "預期衰退中值",
        'swap_instruction': "(作為防止R方或H方惡意或無能的雙向制衡機制)",
        'accumulated_wealth': "💰 累積資金庫",
        'r_value_gov': "R值 (僅執政黨可調):",
        'r_value_lock': "R值 (已鎖定):",
        'r_explanation': "💡 **R值設定 (有效範圍 1~1000)：** R值越高，代表 H（執行方）要推動建設與獲利的難度越高、摩擦力越大；R值越低（例如 1~2），H 越容易獲利，也因此更有誘因留在 H 位置乖乖合作，避免跳船。",
        'execute_swap': "發起 Swap (不信任案)",
        'execute_swap_opp': "對執政黨發起 Swap (不信任案)",
        'execute_swap_lock': "Swap 已執行 (已鎖定)",
        'opp_proposed_swap': "⚠️ 在野黨在上一階段提出了 Swap (不信任案)！您是否要接受？",
        'opp_proposed_swap_accept': "接受在野黨的 Swap 提案",
        'ruling_locked_swap': "🔒 執政黨已強勢發起 Swap，此回合在野黨無法取消。",
        'show_real_decay': "顯示實際衰退",
        'current_real_decay': "當前實際衰退值:",
        'hidden': "*** 隱藏 ***",
        'confirm_btn': "確認並結束本年",
        'calc_btn': "計算預測",
        'edu': "教育",
        'anti': "反智",
        'brain': "洗腦",
        'cons': "建設",
        'max': "最大",
        'not_r': "非 R 角色",
        'waste_warn': "因執行交換，投入教育/反智的資金將會被浪費。",
        'forecast_header': "預測結果:",
        'expected_income': "預期 {0} 收入:",
        'support_change': "支持度變化:",
        'view_breakdown': "🧮 查看計算明細",
        'h_inc': "Household 收入",
        'r_inc': "Regulator 收入",
        'total_inc': "總收入",
        'bonus': "津貼",
        'sim_fin': "=== 模擬結束！ ===",
        'restart': "重新開始遊戲",
        'turn_p0': "階段 1: 執政黨草擬提案",
        'turn_p1': "階段 2: 在野黨回應",
        'turn_p2': "階段 3: 最終審查",
        'btn_submit_prop': "將提案交給在野黨",
        'btn_submit_react': "送出回應給執政黨",
        'btn_revise': "退回修改提案 (回到階段1)",
        'wait_opp': "等待在野黨回應中...",
        'yr': "第",
        'warn_exp': "⚠️ 預算超支！"
    }
}

def t(key, *args):
    lang_code = st.session_state.get('lang', 'English')
    text = I18N[lang_code].get(key, key)
    if args: return text.format(*args)
    return text
