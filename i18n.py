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
        'h_media_mult': "H-Role Media Multiplier:",
        'edu_decay': "Annual Edu Decay:",
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
This is a political sandbox roleplaying game. You can rename the parties (e.g., "Democracy" vs. "Republic" or "Capitalists" vs. "Socialists"), inhabit their ideologies, and see how they interact under systemic pressure.

**The Core Conflict (Roles):**
* 👑 **Governing Party:** The party currently in power. Receives an automatic +200 wealth bonus each year.
* 🟢 **Household Role (H-Role):** Controls the immediate economic output and the **news media**. They reap the financial benefits when H-Index is high. Their brainwashing effect is **multiplied by 1.2x** by default.
* 🔵 **Regulator Role (R-Role):** Controls the societal narrative. Possesses the *exclusive* power to use Education and Anti-Education. **Note:** Public Rationality decays automatically every year, requiring constant educational investment.

**Your Arsenal (Actions & Mechanics):**
* 📚 **Edu / Anti-Edu (R-Role Only):** Combats the natural decay of public Rationality.
* 📺 **Brainwashing:** Grants a temporary spike in Support, and allows you to steal performance credit in low-rationality societies.
* 🏗️ **Construction:** Builds real infrastructure. It boosts public Satisfaction (True-H) and drives up the H-Index.
* 🔄 **Execute Swap:** - **Governing Party:** Absolute power to force a swap.
  - **Opposition Party:** Can only propose a swap, subject to governing party approval.
        """,
        'guide_how': """
### 📖 How to Play & UI Guide

**Step-by-Step Turn Guide:**
1. **Phase 1 (Governing Party):** Set budget and decide whether to force a Swap.
2. **Phase 2 (Opposition Party):** Set budget. If the governing party didn't force a swap, the opposition can propose one.
3. **Phase 3 (Final Review):** The governing party sets the R-Value, approves/rejects any opposition swap proposals, and confirms the year.

* **R-Value (Friction):** Set only by the Governing Party. **Recommended range: 0.5 to 2.0.**
  - **Higher R-Value:** Makes Construction sluggish, limiting the H-Role's ability to profit.
  - **Lower R-Value:** High construction efficiency, acting as an incentive for the H-Role to cooperate.
        """,
        'guide_deep': """
### ⚙️ Deep Dive: The Mechanics of Support & Expiry

**1. The Battle for Credit: Rationality vs. Brainwashing**
When public satisfaction (True-H) rises, support is **not simply given to the biggest spender**. It is filtered by Rationality:
* **High Rationality:** Voters reward the party that actually spent money on Construction.
* **Low Rationality:** Credit can be stolen by the party that spends heavily on Brainwashing (especially the H-Role with media advantage).
* **Punishment:** If satisfaction drops, the Governing Party absorbs 100% of the negative support impact.
        """,
        'governing': "Governing",
        'tax_revenue': "Tax Revenue",
        'election_this_year': "⚠️ Election This Year!",
        'election_next_year': "⏳ 1 Year to Election!",
        'rationality_level': "Rationality Level",
        'midpoint_decay': "Midpoint Decay",
        'swap_instruction': "(Both parties can toggle Execute Swap if it benefits their strategy)",
        'accumulated_wealth': "💰 Wealth",
        'r_value_gov': "R-Value (Ruling Only):",
        'r_value_lock': "R-Value (LOCKED):",
        'execute_swap': "Execute Swap (Locks R-Value & Roles)",
        'execute_swap_lock': "Execute Swap (LOCKED)",
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
        'waste_warn': "Funds placed in Edu/Anti will be wasted due to the proposed Swap.",
        'forecast_header': "Forecast Results (Midpoint Decay: {0:.2f}):",
        'expected_income': "Expected {0} Income:",
        'support_change': "Support Change:",
        'view_breakdown': "🧮 View Calculation Breakdown",
        'h_inc': "Household Income",
        'r_inc': "Regulator Income",
        'total_inc': "Total Income",
        'bonus': "Bonus",
        'sim_fin': "=== Simulation Finished! ===",
        'restart': "Restart Game",
        'turn_p0': "Phase 1: Ruling Party Drafts Proposal",
        'turn_p1': "Phase 2: Opposition Reacts",
        'turn_p2': "Phase 3: Final Review",
        'btn_submit_prop': "Send to Opposition",
        'btn_submit_react': "Send Reaction",
        'btn_revise': "Revise Proposal",
        'wait_opp': "Waiting for Opposition...",
        'h_new': "📰 **Headline:** *New Government Takes Office! Welcome to Year 1.*",
        'h_elec': "📰 **Headline:** Election Concluded! **{0}** secures the majority!\n\n",
        'h_fin_c': "📰 **Financial Report:** {0}. {1} Consequently, **{2}** secured a revenue of {3} with a support shift of {4}, while **{5}** secured {6} with a support shift of {7}.",
        'h_fin_s': "📰 **Financial Report:** Stability maintained. Real outcomes closely aligned with forecasts. **{0}** gained {1} in revenue (Support Shift: {2}), and **{3}** gained {4} (Support Shift: {5}).",
        'r_bad': ["Severe geopolitical tension", "An unforeseen virus outbreak", "Devastating earthquakes"],
        'r_good': ["A major technological breakthrough", "An unprecedented economic boom", "Global peace and stability"],
        'd_cu': "Voters are disappointed in {0}, actively punishing them in the polls.",
        'd_cb': "Voter expectations for {0} turned into bitter disappointment.",
        'd_ca': "Adding fuel to the fire! Absolute anger erupts towards {0}.",
        'd_cd': "Public dissatisfaction with {0} continues to grow.",
        'd_br': "Voters are relieved, softening their stance and rewarding {0}.",
        'd_bs': "Pessimism turned to a pleasant surprise, boosting {0}'s image.",
        'd_be': "Exceeding all expectations! Pure euphoria surrounds {0}.",
        'd_bstr': "Public confidence in {0} strengthens.",
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
        'h_media_mult': "H黨媒體洗腦倍率:",
        'edu_decay': "每年理智度衰退:",
        'set_wealth_a': "設定A黨財富:",
        'set_wealth_b': "設定B黨財富:",
        'game_guide': "📖 遊戲指南",
        'detail_level': "詳細程度:",
        'overview': "簡介 (Overview)",
        'how_to_play': "玩法 (How to Play)",
        'deep_dive': "深度機制 (Deep Dive)",
        'guide_overview': """
### 🎮 簡介與角色扮演策略
**歡迎來到 Symbiocracy (共生民主)！**
這是一個政治沙盒角色扮演遊戲。你可以將政黨改名，帶入他們的意識形態，並觀察在系統壓力下他們如何互動。

**核心衝突 (角色分配)：**
* 👑 **執政黨 (Governing Party):** 當前掌權的政黨。每年自動獲得 +200 財富津貼。
* 🟢 **Household 角色 (H-Role):** 控制即時的經濟與**新聞媒體權**。H-Index 越高分成越多，且**其洗腦效果預設為 1.2 倍**，因為他們掌握了日常的話語權。
* 🔵 **Regulator 角色 (R-Role):** 控制長期社會敘事。擁有使用「教育」和「反智」的專屬權力。注意，**社會理智度每年會自然衰退**，R 角色必須持續投入教育才能維持清醒的社會。

**你的武器庫 (支出行動)：**
* 📚 **教育 / 反智 (僅限 R-Role):** 對抗理智度的自然衰退。
* 📺 **洗腦 (Brainwashing):** 創造虛假的支持度，並能在低理智社會中**搶奪對手的建設功勞**。
* 🏗️ **建設 (Construction):** 建造基礎設施提升滿意度 (True-H)。
* 🔄 **不信任案 (Swap):** - **執政黨發動：** 擁有絕對主導權，在野黨無法拒絕。
  - **在野黨發動：** 僅為「提議」，執政黨在最終審查時可以選擇否決。
        """,
        'guide_how': """
### 📖 玩法與 UI 指南

**三階段回合制：**
1. **階段 1 (執政黨)：** 草擬預算，並決定是否發動不信任案 (強制 Swap)。
2. **階段 2 (在野黨)：** 提出對應預算。若執政黨未發動 Swap，在野黨可以選擇是否發動「提議 Swap」。
3. **階段 3 (最終審查)：** 執政黨設定 R 值，決定是否接受在野黨的 Swap 提議，並最終確認執行。

* **R 值 (摩擦力):** 僅由執政黨設定。**建議範圍落在 0.5 ~ 2 之間**（超過亦有效果但邊際差異會變小）。
  - **R值越高：** 系統摩擦力大，H-Role 透過建設推高 H-Index 的難度大增，獲利變得極度困難。
  - **R值越低：** 建設效率極高，這能作為一種誘因，吸引 H-Role 願意留在該位置與系統合作，而非消極怠工。
        """,
        'guide_deep': """
### ⚙️ 深度機制：支持度與過期的運作原理

**政績不再是執政黨全拿：理智度與洗腦的功勞爭奪戰**
當公眾滿意度 (True-H) 上升時，支持度的分配**不再單純看誰投的錢多**，而是會被「理智度」與「洗腦度」狠狠矯正一次：
* **高理智社會：** 選民眼睛是雪亮的。誰實打實地砸錢在「建設 (Cons)」，誰就能分到大部分的政績紅利。
* **低理智社會：** 進入愚民政治。此時砸錢建設的一方可能拿不到功勞，功勞會被投入大量「洗腦 (Brain)」且掌握媒體優勢（H黨）的一方整碗端走。
* **扣分機制：** 如果國家滿意度衰退（整體 True-H 下降），選民會怪罪掌舵者，由**執政黨承擔全部的支持度流失**。
        """,
        'governing': "當前執政",
        'tax_revenue': "當前稅收",
        'election_this_year': "⚠️ 今年是選舉年！",
        'election_next_year': "⏳ 距離選舉剩 1 年！",
        'rationality_level': "社會理智度",
        'midpoint_decay': "預期衰退中值",
        'swap_instruction': "(若玩家認為有利，兩黨皆可隨時提出「執行交換」)",
        'accumulated_wealth': "💰 累積資金庫",
        'r_value_gov': "R值 (僅執政黨可調):",
        'r_value_lock': "R值 (已鎖定):",
        'execute_swap': "執行交換 (鎖定R值與角色)",
        'execute_swap_lock': "執行交換 (已鎖定)",
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
        'forecast_header': "預測結果 (預期衰退: {0:.2f}):",
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
        'btn_submit_react': "送出回應",
        'btn_revise': "退回修改提案",
        'wait_opp': "等待在野黨回應中...",
        'h_new': "📰 **頭條：** *新政府上任！歡迎來到第 1 年。*",
        'h_elec': "📰 **頭條：** 選舉結束！**{0}** 取得多數席位！\n\n",
        'h_fin_c': "📰 **財報：** {0}。{1} 因此，**{2}** 獲得了 {3} 的收入與 {4} 的支持度變化，而 **{5}** 獲得了 {6} 的收入與 {7} 的支持度變化。",
        'h_fin_s': "📰 **財報：** 局勢穩定。實際結果與預期吻合。**{0}** 獲得了 {1} 的收入 (支持度變化: {2})，而 **{3}** 獲得了 {4} (支持度變化: {5})。",
        'r_bad': ["嚴重的地緣政治緊張", "不可預見的病毒爆發", "毀滅性的大地震"],
        'r_good': ["重大的科技突破", "史無前例的經濟繁榮", "全球和平與穩定"],
        'd_cu': "選民對 {0} 感到失望，並在民調中懲罰了他們",
        'd_cb': "選民對 {0} 的期望轉為苦澀的失望",
        'd_ca': "火上加油！民眾對 {0} 的憤怒徹底爆發",
        'd_cd': "民眾對 {0} 的不滿持續發酵",
        'd_br': "選民鬆了一口氣，軟化了對 {0} 的態度並給予回報",
        'd_bs': "悲觀情緒轉為驚喜，大幅提升了 {0} 的形象",
        'd_be': "超越所有期望！純粹的狂歡圍繞著 {0}",
        'd_bstr': "大眾對 {0} 的信心進一步增強",
        'yr': "第",
        'warn_exp': "⚠️ 預算超支！"
    }
}

def t(key, *args):
    lang_code = st.session_state.get('lang', 'English')
    text = I18N[lang_code].get(key, key)
    if args: return text.format(*args)
    return text
