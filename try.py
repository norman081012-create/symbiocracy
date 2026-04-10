import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random

# ==========================================
# GAME LOGIC ENGINE (Unchanged Math)
# ==========================================
class SymbiocracyGame:
    def __init__(self):
        # Party Names
        self.name_A = "Prosperity"
        self.name_B = "Equity"

        # Game Settings
        self.year = 1
        self.total_years = 20
        self.annual_budget = 1000
        self.base_income = 100
        self.major_bonus = 200

        # Multipliers, Emotionality, and Durations (Defaults)
        self.edu_mult = 0.001
        self.bw_mult = 0.001
        self.emotionality = 0.5
        self.bw_years = 2
        self.perf_years = 6
        self.tax_impact = 200.0 

        # Initial Values
        self.A_support = 0.51
        self.B_support = 0.49
        self.A_wealth = 500 
        self.B_wealth = 500 
        self.H_index = 0.5
        self.true_H = 0.5
        self.R_value = 0.5
        self.rationality = 0.5
        
        self.baseline_true_H = 0.5

        # Decay Settings
        self.decay_min = 0.2
        self.decay_max = 1.2
        self.current_decay = random.uniform(self.decay_min, self.decay_max)
        self.last_year_decay = self.current_decay
        self.last_report = None

        # Record expiration of effects
        self.bw_expiry = {}
        self.perf_expiry = {}

        # Roles
        self.first_party = "A"
        self.current_H_party = "B"
        self.current_R_party = "A"

        self.swap_available = True 
        self.error_msg = ""
        self.current_tax = 1000

        self.history = []
        self.events = []

        self.allocate_budget()

    def allocate_budget(self):
        self.current_tax = max(0, self.annual_budget + ((self.true_H - 0.5) * self.tax_impact))
        self.A_wealth += self.base_income
        self.B_wealth += self.base_income

        if self.first_party == "A":
            self.A_wealth += self.major_bonus
        else:
            self.B_wealth += self.major_bonus

        h_funds = self.current_tax * self.H_index
        r_funds = self.current_tax * (1 - self.H_index)

        if self.current_H_party == "A":
            self.A_wealth += h_funds
            self.B_wealth += r_funds
        else:
            self.B_wealth += h_funds
            self.A_wealth += r_funds

    def process_year(self, inputs):
        exp_decay = (self.decay_min + self.decay_max) / 2
        act_decay = self.current_decay

        tot_cons = inputs['A']['cons'] + inputs['B']['cons']

        net_edu_A = (inputs['A']['edu'] - inputs['A']['anti']) if self.current_R_party == "A" else 0
        net_edu_B = (inputs['B']['edu'] - inputs['B']['anti']) if self.current_R_party == "B" else 0
        new_rat = max(0, min(1, self.rationality + (net_edu_A + net_edu_B) * self.edu_mult))

        exp_true_H = self.true_H - exp_decay + (tot_cons * 0.001)
        act_true_H = self.true_H - act_decay + (tot_cons * 0.001)

        safe_R = self.R_value if self.R_value != 0 else 0.000001
        exp_H_idx = max(0, min(1, self.H_index - exp_decay + (tot_cons / safe_R) * 0.001))
        act_H_idx = max(0, min(1, self.H_index - act_decay + (tot_cons / safe_R) * 0.001))

        exp_tax = max(0, self.annual_budget + ((exp_true_H - 0.5) * self.tax_impact))
        act_tax = max(0, self.annual_budget + ((act_true_H - 0.5) * self.tax_impact))

        exp_h_inc = exp_tax * exp_H_idx
        exp_r_inc = exp_tax * (1 - exp_H_idx)
        act_h_inc = act_tax * act_H_idx
        act_r_inc = act_tax * (1 - act_H_idx)

        maj_A = self.major_bonus if self.first_party == "A" else 0
        maj_B = self.major_bonus if self.first_party == "B" else 0

        exp_inc_A = self.base_income + maj_A + (exp_h_inc if self.current_H_party == "A" else exp_r_inc)
        exp_inc_B = self.base_income + maj_B + (exp_h_inc if self.current_H_party == "B" else exp_r_inc)
        act_inc_A = self.base_income + maj_A + (act_h_inc if self.current_H_party == "A" else act_r_inc)
        act_inc_B = self.base_income + maj_B + (act_h_inc if self.current_H_party == "B" else act_r_inc)

        perf_base = 0.2 - (self.emotionality - 0.5) * 0.4
        bw_base = 1.1 + (self.emotionality - 0.5) * 0.4

        bw_eff = (inputs['A']['brain'] - inputs['B']['brain']) * self.bw_mult * (bw_base - new_rat)

        exp_perf = (exp_true_H - self.baseline_true_H) * (new_rat + perf_base)
        act_perf = (act_true_H - self.baseline_true_H) * (new_rat + perf_base)

        exp_perf_A = exp_perf if self.first_party == "A" else -exp_perf
        act_perf_A = act_perf if self.first_party == "A" else -act_perf

        exp_bw = self.bw_expiry.get(self.year, 0.0)
        exp_pf = self.perf_expiry.get(self.year, 0.0)

        exp_net_A = exp_perf_A + bw_eff - exp_pf - exp_bw
        act_net_A = act_perf_A + bw_eff - exp_pf - exp_bw
        exp_net_B = -exp_net_A
        act_net_B = -act_net_A

        self.last_report = {
            'exp_decay': exp_decay,
            'act_decay': act_decay,
            'exp_inc_A': exp_inc_A,
            'act_inc_A': act_inc_A,
            'exp_inc_B': exp_inc_B,
            'act_inc_B': act_inc_B,
            'exp_net_A': exp_net_A,
            'act_net_A': act_net_A,
            'exp_net_B': exp_net_B,
            'act_net_B': act_net_B,
            'blame_party': self.first_party,
            'election_just_happened': False,
            'new_major': None
        }

        self.rationality = new_rat
        self.true_H = act_true_H
        self.H_index = act_H_idx

        self.A_wealth -= sum(inputs['A'].values())
        self.B_wealth -= sum(inputs['B'].values())

        self.bw_expiry[self.year + self.bw_years] = bw_eff
        self.perf_expiry[self.year + self.perf_years] = act_perf_A

        self.A_support = self.A_support + act_net_A
        self.B_support = 1 - self.A_support

        self.history.append({
            'Year': self.year,
            'TrueH': self.true_H,
            'Rationality': self.rationality,
            'A_Wealth': self.A_wealth,
            'B_Wealth': self.B_wealth,
            'A_Support': self.A_support
        })

        self.year += 1
        if (self.year - 1) % 4 == 0 and self.year <= self.total_years:
            self.events.append({'year': self.year - 1, 'type': 'Election'})
            new_first_party = "A" if self.A_support > self.B_support else "B"

            if new_first_party != self.first_party:
                self.baseline_true_H = self.true_H

            self.first_party = new_first_party
            self.swap_available = True

            if self.first_party == "A":
                self.current_R_party = "A"
                self.current_H_party = "B"
            else:
                self.current_R_party = "B"
                self.current_H_party = "A"
                
            self.last_report['election_just_happened'] = True
            self.last_report['new_major'] = self.first_party

        self.error_msg = ""
        self.last_year_decay = self.current_decay
        self.current_decay = random.uniform(self.decay_min, self.decay_max)

        if self.year <= self.total_years:
            self.allocate_budget()


# ==========================================
# STREAMLIT UI APP & TRANSLATIONS
# ==========================================
st.set_page_config(page_title="Symbiocracy Simulator", layout="wide")

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
This is a political sandbox roleplaying game. You can rename the parties (e.g., "Democracy" vs. "Republic" or "Capitalists" vs. "Socialists"), inhabit their ideologies, and see how they interact under systemic pressure.

**The Ultimate Goal:** There is no single way to win. Over the course of the simulation (default 20 years, adjustable in Global Settings), you decide your victory condition. Do you want to amass the most private wealth? Do you want to maintain a stable, unshakeable dynasty? Or do you genuinely want to maximize societal satisfaction (True-H)? At the end of the simulation, a comprehensive historical report will reveal the true legacy of your political era.

**The Core Conflict (Roles):**
* 👑 **Governing Party:** The party currently in power. Receives an automatic +200 wealth bonus each year.
* 🟢 **Household Role (H-Role):** Controls the immediate economic output. Reaps the direct financial benefits when the H-Index is high.
* 🔵 **Regulator Role (R-Role):** Controls the societal narrative. Possesses the *exclusive* power to use Education and Anti-Education to shape public Rationality.

**Your Arsenal (Actions & Mechanics):**
* 📚 **Edu / Anti-Edu (R-Role Only):** Directly alters public **Rationality**. High Rationality forces politicians to deliver real results; low Rationality makes the public highly gullible.
* 📺 **Brainwashing:** Grants a temporary, artificial spike in Support. *Strategic Tip:* Exponentially more effective and cheaper when public Rationality is low and Voter Emotion is high.
* 🏗️ **Construction:** Builds real infrastructure. It boosts public Satisfaction (True-H) and drives up the H-Index, expanding the total tax pool and the Household's cut.
* 🔄 **Execute Swap:** Either party can propose to instantly trade the H-Role and R-Role if they believe it benefits their strategy. *Warning:* Once executed, roles and the R-Value are locked until the next election!
        """,
        'guide_how': """
### 📖 How to Play & UI Guide

**Step-by-Step Turn Guide:**
1. **Assess the Year:** Look at the top **Status Board**. Read the Newspaper Headline to understand the current economic climate, and check the Midpoint Decay. High decay means your Satisfaction and budget will drop drastically this year.
2. **Draft Budgets and decide R valure:** Both parties allocate their accumulated wealth into their respective input boxes (Edu, Anti, Brain, Cons). But Only the ruling party can decide R value.
3. **Negotiate:** Discuss strategy with the opposing party. Decide if executing a **Swap** is necessary for either of you to survive the year.
4. **Check the Math:** *Do not click Confirm yet!* Click **"Calculate Forecast"** and open the **"View Forecast Calculation Breakdown"** tab. This shows exactly how your proposed spending will change Income and Approval Ratings.
5. **Revise & Execute:** Adjust your spending based on the forecast. Once both parties agree on their final numbers, click **Confirm & End Year** to lock in the results and advance time.
        """,
        'guide_deep': """
### ⚙️ Deep Dive: The Mechanics of Support & Expiry
**1. The Baseline Reset Mechanism**
Voters are both forgetful and pragmatic. The game relies on a hidden variable called `baseline_true_H` (Baseline Satisfaction). When a party takes office, the current satisfaction is recorded as its new baseline. You are judged purely on how much you improve or ruin the country *after* taking power.

**2. Rationality vs Emotionality**
* **High Rationality:** Voters accurately translate actual living conditions (True-H) into political judgment.
* **Low Rationality:** Voters become dull. Your support will rise at a crawl even with real infrastructure investments.
* **High Emotion:** Voters stop caring about actual Satisfaction almost entirely. Under these specific conditions, a party can rely purely on aggressive "Brainwashing."

**3. The Expiry Mechanism**
* **Performance Expiry (Default 6 Years):** If you gain a massive surge in support in Year 1, that specific support bonus begins to expire and will be deducted from your total starting in Year 7.
* **Brainwashing Expiry (Default 2 Years):** Brainwashing fades very quickly. If you rely on it, you must keep spending to maintain the illusion.
        """,
        'governing': "Governing",
        'tax_revenue': "Tax Revenue",
        'election_this_year': "⚠️ Election This Year!",
        'election_next_year': "⏳ 1 Year to Election!",
        'rationality_level': "Rationality Level",
        'midpoint_decay': "Midpoint Decay",
        'swap_instruction': "(Both parties can toggle Execute Swap if it benefits their strategy)",
        'accumulated_wealth': "💰 Accumulated Wealth",
        'r_value_gov': "R-Value (Ruling Only):",
        'r_value_lock': "R-Value (LOCKED):",
        'execute_swap': "Execute Swap (Locks R-Value & Roles)",
        'execute_swap_lock': "Execute Swap (LOCKED)",
        'show_real_decay': "Show Real Decay",
        'current_real_decay': "Current Real Decay:",
        'hidden': "*** HIDDEN ***",
        'confirm_btn': "Confirm & End Year",
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
        'btn_submit_prop': "Submit Proposal to Opposition",
        'btn_submit_react': "Submit Reaction",
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
        'yr': "Year"
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
**歡迎來到 Symbiocracy (共生民主)！**
這是一個政治沙盒角色扮演遊戲。你可以將政黨改名，帶入他們的意識形態，並觀察在系統壓力下他們如何互動。

**終極目標：** 遊戲沒有單一的獲勝方式。你是想累積最多的私人財富？還是想維持一個穩定、不可動搖的王朝？亦或是你真心想最大化社會滿意度 (True-H)？

**核心衝突 (角色分配)：**
* 👑 **執政黨 (Governing Party):** 當前掌權的政黨。每年自動獲得 +200 財富津貼。
* 🟢 **Household 角色 (H-Role):** 控制即時的經濟產出。當 H-Index (預算比例) 高時，能獲得直接的財務利益。
* 🔵 **Regulator 角色 (R-Role):** 控制社會敘事。擁有使用「教育」和「反智」來塑造公眾理智度的*專屬*權力。

**你的武器庫 (支出行動)：**
* 📚 **教育 / 反智 (僅限 R-Role):** 直接改變公眾的**理智度**。高理智度迫使政治人物交出真實政績；低理智度則讓公眾變得極易受騙。
* 📺 **洗腦 (Brainwashing):** 提供暫時性、虛假的支持度飆升。
* 🏗️ **建設 (Construction):** 建造真實的基礎設施。它能提升公眾滿意度 (True-H) 並推高 H-Index。
* 🔄 **執行交換 (Execute Swap):** 任何一方都可以提議立即交換 H-Role 和 R-Role。*警告：* 一旦執行，角色將被鎖定直到下次選舉！
        """,
        'guide_how': """
### 📖 玩法與 UI 指南
1. **評估當前年度：** 查看頂部的**狀態看板**，了解當前衰退壓力。
2. **階段 1 (執政黨提案)：** 執政黨草擬預算，並有權單方面決定 R 值 (建設摩擦力)。完成後交給在野黨。
3. **階段 2 (在野黨回應)：** 在野黨查看執政黨的佈局，並輸入自己的預算應對。
4. **階段 3 (最終審查)：** 系統將公開「預測報表」，雙方確認是否滿意。如果不滿意，可點擊「退回修改」重新談判；若達成共識，點擊確認推進時間。
        """,
        'guide_deep': """
### ⚙️ 深度機制：支持度與過期的運作原理
**1. 基準點重置機制 (Baseline Reset)**
選民是非常健忘且現實的。當政黨贏得選舉成為執政黨時，系統會紀錄當下的滿意度作為「基準點」。你無法從前朝政府獲得功勞；你純粹根據掌權*後*的改善程度來接受評判。

**2. 理智度是放大器**
滿意度轉化為政治支持度的效率，高度取決於社會的 **理智度**。低理智度會讓選民變得遲鈍，即便基礎建設再好，支持度也只會龜速爬升。

**3. 選民情緒的制衡**
在感性社會(高情緒)下，選民對實體政績的基礎要求會大幅下降，此時政黨可以放任國家衰退，純粹靠著強勢的「洗腦」來維持執政。

**4. 過期機制 (Expiry)**
政治紅利不是永久的。政績帶來的支持度飆升預設在 6 年後會被扣回；而洗腦效果消退得非常快 (預設 2 年)。
        """,
        'governing': "當前執政",
        'tax_revenue': "當前稅收",
        'election_this_year': "⚠️ 今年是選舉年！",
        'election_next_year': "⏳ 距離選舉剩 1 年！",
        'rationality_level': "社會理智度",
        'midpoint_decay': "預期衰退中值",
        'swap_instruction': "(若玩家認為有利，活躍的一方可隨時提出「執行交換」)",
        'accumulated_wealth': "💰 累積資金庫",
        'r_value_gov': "R值 (僅執政黨可調):",
        'r_value_lock': "R值 (已鎖定):",
        'execute_swap': "執行交換 (鎖定R值與角色)",
        'execute_swap_lock': "執行交換 (已鎖定)",
        'show_real_decay': "顯示實際衰退",
        'current_real_decay': "當前實際衰退值:",
        'hidden': "*** 隱藏 ***",
        'confirm_btn': "確認並結束本年",
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
        'turn_p2': "階段 3: 最終預測與審查",
        'btn_submit_prop': "將提案交給在野黨",
        'btn_submit_react': "送出回應、查看預測",
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
        'yr': "第"
    }
}

def t(key, *args):
    lang_code = st.session_state.lang
    text = I18N[lang_code].get(key, key)
    if args: return text.format(*args)
    return text

# --- INITIALIZE STATE ---
if 'game' not in st.session_state:
    st.session_state.game = SymbiocracyGame()
    st.session_state.lang = "English"
    st.session_state.turn_phase = 0 # 0: Ruling, 1: Opp, 2: Final
    st.session_state.name_a = "Prosperity"
    st.session_state.name_b = "Equity"
    st.session_state.show_decay = False
    st.session_state.do_swap = False
    st.session_state.r_val = 0.5
    st.session_state.error_msg = ""
    st.session_state.label_style = "Short"
    
    st.session_state.in_a_edu = 0.0
    st.session_state.in_a_anti = 0.0
    st.session_state.in_a_brain = 0.0
    st.session_state.in_a_cons = 0.0
    st.session_state.in_b_edu = 0.0
    st.session_state.in_b_anti = 0.0
    st.session_state.in_b_brain = 0.0
    st.session_state.in_b_cons = 0.0

game = st.session_state.game

# --- UI: GLOBAL SETTINGS ---
with st.expander(t('settings'), expanded=False):
    c_l1, c_l2 = st.columns(2)
    st.session_state.lang = c_l1.radio(t('lang'), ["English", "中文"], index=0 if st.session_state.lang=="English" else 1, horizontal=True)
    st.session_state.label_style = c_l2.radio(t('label_style'), [t('short'), t('full')], horizontal=True)
    
    c1, c2 = st.columns(2)
    st.session_state.name_a = c1.text_input(t('name_a'), st.session_state.name_a)
    st.session_state.name_b = c2.text_input(t('name_b'), st.session_state.name_b)
    
    c1, c2 = st.columns(2)
    dec_range = c1.slider(t('decay_range'), 0.0, 3.0, (game.decay_min, game.decay_max), 0.05)
    game.decay_min, game.decay_max = dec_range
    game.total_years = c2.slider(t('total_years'), 5, 100, game.total_years, 1)
    
    c1, c2 = st.columns(2)
    game.annual_budget = c1.number_input(t('base_budget'), value=game.annual_budget, step=100)
    game.major_bonus = c2.number_input(t('major_bonus'), value=game.major_bonus, step=50)

    c1, c2 = st.columns(2)
    game.tax_impact = c1.number_input(t('tax_impact'), value=game.tax_impact, step=50.0)
    game.emotionality = c2.slider(t('voter_emotion'), 0.0, 1.0, game.emotionality, 0.05)

    c1, c2 = st.columns(2)
    game.edu_mult = c1.number_input(t('edu_impact'), value=game.edu_mult, step=0.0001, format="%.4f")
    game.bw_mult = c2.number_input(t('bw_impact'), value=game.bw_mult, step=0.0001, format="%.4f")

    c1, c2 = st.columns(2)
    game.bw_years = c1.number_input(t('bw_duration'), value=game.bw_years, step=1)
    game.perf_years = c2.number_input(t('perf_duration'), value=game.perf_years, step=1)

    c1, c2 = st.columns(2)
    game.A_wealth = c1.number_input(t('set_wealth_a'), value=float(game.A_wealth))
    game.B_wealth = c2.number_input(t('set_wealth_b'), value=float(game.B_wealth))


# Check for End Game
if game.year > game.total_years:
    st.success(t('sim_fin'))
    df = pd.DataFrame(game.history)
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.set_xlabel(t('yr'), fontweight='bold')
    ax1.set_ylabel('Metrics', color='black', fontweight='bold')
    ax1.plot(df['Year'], df['TrueH'], label='Satisfaction', color='green')
    ax1.plot(df['Year'], df['Rationality'], label='Rationality', ls='--')
    ax1.plot(df['Year'], df['A_Support'], label=f"Support {st.session_state.name_a}", color='red')
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Wealth', color='purple', fontweight='bold')
    ax2.plot(df['Year'], df['A_Wealth'], color='orange', alpha=0.5, label=f"Wealth {st.session_state.name_a}")
    ax2.plot(df['Year'], df['B_Wealth'], color='purple', alpha=0.5, label=f"Wealth {st.session_state.name_b}")
    
    fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9))
    plt.title('Symbiocracy: Simulation Summary')
    st.pyplot(fig)
    
    if st.button(t('restart')):
        st.session_state.game = SymbiocracyGame()
        st.session_state.turn_phase = 0
        st.rerun()
    st.stop()


# --- HELPER FUNCTIONS ---
def generate_headline():
    if game.year == 1:
        return t('h_new')
    rep = game.last_report
    if not rep: return ""
    major_name = st.session_state.name_a if rep['blame_party'] == 'A' else st.session_state.name_b
    h1 = ""
    if rep['election_just_happened']:
        new_major_name = st.session_state.name_a if rep['new_major'] == 'A' else st.session_state.name_b
        h1 = t('h_elec', new_major_name)
    diff = rep['act_decay'] - rep['exp_decay']
    def fmt_inc(exp, act): return f"**{act:.1f}** (Exp: {exp:.1f})"
    def fmt_sup(exp, act): return f"**{act:+.2%}** (Exp: {exp:+.2%})"

    inc_A_str = fmt_inc(rep['exp_inc_A'], rep['act_inc_A'])
    inc_B_str = fmt_inc(rep['exp_inc_B'], rep['act_inc_B'])
    sup_A_str = fmt_sup(rep['exp_net_A'], rep['act_net_A'])
    sup_B_str = fmt_sup(rep['exp_net_B'], rep['act_net_B'])
    
    if diff > 0.1: 
        reason = random.choice(t('r_bad'))
        desc = t('d_cu', major_name)
        h2 = t('h_fin_c', reason, desc, st.session_state.name_a, inc_A_str, sup_A_str, st.session_state.name_b, inc_B_str, sup_B_str)
    elif diff < -0.1: 
        reason = random.choice(t('r_good'))
        desc = t('d_br', major_name)
        h2 = t('h_fin_c', reason, desc, st.session_state.name_a, inc_A_str, sup_A_str, st.session_state.name_b, inc_B_str, sup_B_str)
    else:
        h2 = t('h_fin_s', st.session_state.name_a, inc_A_str, sup_A_str, st.session_state.name_b, inc_B_str, sup_B_str)
    return h1 + h2

def do_forecast_calc():
    inputs_a = {'edu': st.session_state.in_a_edu, 'anti': st.session_state.in_a_anti, 'brain': st.session_state.in_a_brain, 'cons': st.session_state.in_a_cons}
    inputs_b = {'edu': st.session_state.in_b_edu, 'anti': st.session_state.in_b_anti, 'brain': st.session_state.in_b_brain, 'cons': st.session_state.in_b_cons}
    
    mid = (game.decay_min + game.decay_max) / 2
    r_val = st.session_state.r_val if st.session_state.r_val != 0 else 0.000001
    sim_R = game.current_H_party if st.session_state.do_swap else game.current_R_party
    sim_H = game.current_R_party if st.session_state.do_swap else game.current_H_party
    
    net_edu_A = (inputs_a['edu'] - inputs_a['anti']) if sim_R == "A" else 0
    net_edu_B = (inputs_b['edu'] - inputs_b['anti']) if sim_R == "B" else 0
    net_edu = net_edu_A + net_edu_B
    p_rat = max(0, min(1, game.rationality + net_edu * game.edu_mult))
    t_cons = inputs_a['cons'] + inputs_b['cons']
    p_true = game.true_H - mid + (t_cons * 0.001)
    p_h_idx = max(0, min(1, game.H_index - mid + (t_cons / r_val) * 0.001))
    
    p_base = 0.2 - (game.emotionality - 0.5) * 0.4
    b_base = 1.1 + (game.emotionality - 0.5) * 0.4
    bw_eff = (inputs_a['brain'] - inputs_b['brain']) * game.bw_mult * (b_base - p_rat)
    p_eff = (p_true - game.baseline_true_H) * (p_rat + p_base)
    net_a = (p_eff if game.first_party == "A" else -p_eff) + bw_eff - game.perf_expiry.get(game.year, 0) - game.bw_expiry.get(game.year, 0)
    net_b = -net_a

    p_tax = max(0, game.annual_budget + ((p_true - 0.5) * game.tax_impact))
    h_inc = p_tax * p_h_idx
    r_inc = p_tax * (1 - p_h_idx)
    
    maj_A = game.major_bonus if game.first_party == "A" else 0
    maj_B = game.major_bonus if game.first_party == "B" else 0

    inc_a = game.base_income + maj_A + (h_inc if sim_H == "A" else r_inc)
    inc_b = game.base_income + maj_B + (h_inc if sim_H == "B" else r_inc)

    return inc_a, inc_b, net_a, net_b, net_edu, p_rat, t_cons, p_true, p_tax, p_h_idx, p_eff, bw_eff, p_base, b_base, r_val, h_inc, r_inc, maj_A, maj_B


# --- UI: HEADER & STATUS ---
with st.expander(t('game_guide'), expanded=False):
    col_g1, col_g2 = st.columns([4, 1])
    guide_mode = col_g2.radio(t('detail_level'), [t('overview'), t('how_to_play'), t('deep_dive')], horizontal=False, label_visibility="collapsed")
    
    if guide_mode == t('overview'): col_g1.markdown(t('guide_overview'))
    elif guide_mode == t('how_to_play'): col_g1.markdown(t('guide_how'))
    else: col_g1.markdown(t('guide_deep'))

mid_decay = (game.decay_min + game.decay_max) / 2
elec_warning = t('election_this_year') if game.year % 4 == 0 else (t('election_next_year') if game.year % 4 == 3 else "")
major_name = st.session_state.name_a if game.first_party == 'A' else st.session_state.name_b

st.markdown(f"### 🏛️ {t('yr')} {game.year} | {t('governing')}: 👑 {major_name} | {t('tax_revenue')}: {game.current_tax:.1f} {elec_warning}")
st.info(generate_headline())
st.write(f"**{t('rationality_level')}:** {game.rationality:.4f} | **{t('midpoint_decay')}:** {mid_decay:.2f}  \n*{t('swap_instruction')}*")


# --- UI: WEALTH BARS ---
max_w = max(game.A_wealth, game.B_wealth, 1)
scale = 100 / (max_w * 1.1)
st.markdown(t('accumulated_wealth'))
wealth_html = f"""
<div style='margin-top:10px; padding:10px; background:#f1f3f5;'>
    <div style='display:flex;'><div style='width:70px; font-weight:bold; color:orange; overflow:hidden; text-overflow:ellipsis;'>{st.session_state.name_a[:8]}</div><div style='width:{max(min(game.A_wealth * scale, 100), 1)}%; background:orange; color:white; padding-right:5px; text-align:right;'>{game.A_wealth:.1f}</div></div>
    <div style='display:flex; margin-top:5px;'><div style='width:70px; font-weight:bold; color:purple; overflow:hidden; text-overflow:ellipsis;'>{st.session_state.name_b[:8]}</div><div style='width:{max(min(game.B_wealth * scale, 100), 1)}%; background:purple; color:white; padding-right:5px; text-align:right;'>{game.B_wealth:.1f}</div></div>
</div>"""
st.markdown(wealth_html, unsafe_allow_html=True)
st.write("<br>", unsafe_allow_html=True)


# --- PHASE LOGIC & VISIBILITY ---
is_a_ruling = (game.first_party == 'A')
opp_name = st.session_state.name_b if is_a_ruling else st.session_state.name_a
gov_name = st.session_state.name_a if is_a_ruling else st.session_state.name_b

show_A, show_B, dis_A, dis_B = False, False, False, False

if st.session_state.turn_phase == 0:
    st.markdown(f"#### 🚦 {t('turn_p0')} (👉 **請將設備交給: {gov_name}**)")
    if is_a_ruling: show_A = True
    else: show_B = True
elif st.session_state.turn_phase == 1:
    st.markdown(f"#### 🚦 {t('turn_p1')} (👉 **請將設備交給: {opp_name}**)")
    show_A, show_B = True, True
    if is_a_ruling: dis_A = True
    else: dis_B = True
elif st.session_state.turn_phase == 2:
    st.markdown(f"#### 🚦 {t('turn_p2')} ⚖️")
    show_A, show_B, dis_A, dis_B = True, True, True, True


# --- UI: SWAP & GLOBAL CONTROLS ---
col1, col2, col3 = st.columns([1, 1, 1])

# Only Gov can set R-val, and ONLY in Phase 0
r_disabled = (not game.swap_available) or (st.session_state.turn_phase != 0)
with col1:
    r_desc = t('r_value_gov') if not r_disabled else t('r_value_lock')
    st.session_state.r_val = st.number_input(r_desc, min_value=0.01, max_value=1.0, value=st.session_state.r_val, disabled=r_disabled)

# Swap can be triggered by whoever is active. Locked in Phase 2.
swap_disabled = (not game.swap_available) or (st.session_state.turn_phase == 2)
with col2:
    st.write("<br>", unsafe_allow_html=True)
    st.session_state.do_swap = st.checkbox(t('execute_swap') if not swap_disabled else t('execute_swap_lock'), value=st.session_state.do_swap, disabled=swap_disabled)
    
with col3:
    st.write("<br>", unsafe_allow_html=True)
    st.session_state.show_decay = st.checkbox(t('show_real_decay'), value=st.session_state.show_decay)

if st.session_state.show_decay:
    st.error(f"{t('current_real_decay')} **{game.current_decay:.4f}**")
else:
    st.markdown(f"{t('current_real_decay')} **{t('hidden')}**")

st.divider()

# --- INPUT RENDER HELPERS ---
l_edu = t('edu') if st.session_state.label_style == t('full') else ("Edu" if st.session_state.lang == "English" else "教育")
l_anti = t('anti') if st.session_state.label_style == t('full') else ("Anti" if st.session_state.lang == "English" else "反智")
l_brain = t('brain') if st.session_state.label_style == t('full') else ("Brain" if st.session_state.lang == "English" else "洗腦")
l_cons = t('cons') if st.session_state.label_style == t('full') else ("Cons" if st.session_state.lang == "English" else "建設")

sim_R = game.current_H_party if st.session_state.do_swap else game.current_R_party
sim_H = game.current_R_party if st.session_state.do_swap else game.current_H_party
max_edu = max(0, (1.0 - game.rationality) / game.edu_mult)
max_anti = max(0, game.rationality / game.edu_mult)

cost_A = st.session_state.in_a_edu + st.session_state.in_a_anti + st.session_state.in_a_brain + st.session_state.in_a_cons
cost_B = st.session_state.in_b_edu + st.session_state.in_b_anti + st.session_state.in_b_brain + st.session_state.in_b_cons

# Render Party A Inputs
if show_A:
    colA1, colA2, colA3, colA4, colA5 = st.columns([1.5, 1, 1, 1, 1])
    role_A = "H-Role" if sim_H == "A" else "R-Role"
    header_A = f"👑 **{st.session_state.name_a} ({role_A})** \nAppr: {game.A_support:.2%} | Cost: {cost_A:.0f}" if is_a_ruling else f"**{st.session_state.name_a} ({role_A})** \nAppr: {game.A_support:.2%} | Cost: {cost_A:.0f}"
    
    if is_a_ruling: colA1.success(header_A)
    else: colA1.info(header_A)

    with colA2:
        label = f"{l_edu} ({t('max')} {max_edu:.0f})" if sim_R == "A" else f"{l_edu} ({t('not_r')})"
        st.session_state.in_a_edu = st.number_input(label, min_value=0.0, max_value=float(max_edu) if sim_R=="A" else 1000000.0, value=st.session_state.in_a_edu, disabled=(sim_R!="A" or dis_A), key='a_edu')
    with colA3:
        label = f"{l_anti} ({t('max')} {max_anti:.0f})" if sim_R == "A" else f"{l_anti} ({t('not_r')})"
        st.session_state.in_a_anti = st.number_input(label, min_value=0.0, max_value=float(max_anti) if sim_R=="A" else 1000000.0, value=st.session_state.in_a_anti, disabled=(sim_R!="A" or dis_A), key='a_anti')
    with colA4:
        st.session_state.in_a_brain = st.number_input(f"{l_brain}:", value=st.session_state.in_a_brain, disabled=dis_A, key='a_brain')
    with colA5:
        st.session_state.in_a_cons = st.number_input(f"{l_cons}:", value=st.session_state.in_a_cons, disabled=dis_A, key='a_cons')
        
    if cost_A > game.A_wealth:
        st.error(f"⚠️ {st.session_state.name_a} 預算超支！ (Cost: {cost_A:.0f} > Wealth: {game.A_wealth:.0f})")

# Render Party B Inputs
if show_B:
    colB1, colB2, colB3, colB4, colB5 = st.columns([1.5, 1, 1, 1, 1])
    role_B = "H-Role" if sim_H == "B" else "R-Role"
    header_B = f"👑 **{st.session_state.name_b} ({role_B})** \nAppr: {game.B_support:.2%} | Cost: {cost_B:.0f}" if not is_a_ruling else f"**{st.session_state.name_b} ({role_B})** \nAppr: {game.B_support:.2%} | Cost: {cost_B:.0f}"
    
    if not is_a_ruling: colB1.success(header_B)
    else: colB1.info(header_B)

    with colB2:
        label = f"{l_edu} ({t('max')} {max_edu:.0f})" if sim_R == "B" else f"{l_edu} ({t('not_r')})"
        st.session_state.in_b_edu = st.number_input(label, min_value=0.0, max_value=float(max_edu) if sim_R=="B" else 1000000.0, value=st.session_state.in_b_edu, disabled=(sim_R!="B" or dis_B), key='b_edu')
    with colB3:
        label = f"{l_anti} ({t('max')} {max_anti:.0f})" if sim_R == "B" else f"{l_anti} ({t('not_r')})"
        st.session_state.in_b_anti = st.number_input(label, min_value=0.0, max_value=float(max_anti) if sim_R=="B" else 1000000.0, value=st.session_state.in_b_anti, disabled=(sim_R!="B" or dis_B), key='b_anti')
    with colB4:
        st.session_state.in_b_brain = st.number_input(f"{l_brain}:", value=st.session_state.in_b_brain, disabled=dis_B, key='b_brain')
    with colB5:
        st.session_state.in_b_cons = st.number_input(f"{l_cons}:", value=st.session_state.in_b_cons, disabled=dis_B, key='b_cons')

    if cost_B > game.B_wealth:
        st.error(f"⚠️ {st.session_state.name_b} 預算超支！ (Cost: {cost_B:.0f} > Wealth: {game.B_wealth:.0f})")


# --- UI: FORECAST & ACTIONS ---
if st.session_state.turn_phase == 2:
    inc_a, inc_b, net_a, net_b, net_edu, p_rat, t_cons, p_true, p_tax, p_h_idx, p_eff, bw_eff, p_base, b_base, r_val, h_inc, r_inc, maj_A, maj_B = do_forecast_calc()
        
    wasted_warn = ""
    if st.session_state.do_swap:
        if (st.session_state.in_a_edu > 0 or st.session_state.in_a_anti > 0) and sim_R != "A":
            wasted_warn += f"\n* ⚠️ **Warning:** {st.session_state.name_a} - {t('waste_warn')}"
        if (st.session_state.in_b_edu > 0 or st.session_state.in_b_anti > 0) and sim_R != "B":
            wasted_warn += f"\n* ⚠️ **Warning:** {st.session_state.name_b} - {t('waste_warn')}"

    st.warning(f"""
    {t('forecast_header', mid_decay)}
    * {t('expected_income', st.session_state.name_a)} **{inc_a:.1f}** | {t('support_change')} **{"+" if net_a>=0 else ""}{net_a:.2%}**
    * {t('expected_income', st.session_state.name_b)} **{inc_b:.1f}** | {t('support_change')} **{"+" if net_b>=0 else ""}{net_b:.2%}** {wasted_warn}
    """)

    with st.expander(t('view_breakdown')):
        st.markdown(f"""
        **1. {t('rationality_level')}:** New_Rationality = Current({game.rationality:.4f}) + [Net_{l_edu}({net_edu}) × {t('edu_impact')}({game.edu_mult:.4f})] = **{p_rat:.4f}**
        
        **2. Satisfaction (True-H):** New_TrueH = Current({game.true_H:.4f}) - {t('midpoint_decay')}({mid_decay:.2f}) + [Total_{l_cons}({t_cons}) × 0.001] = **{p_true:.4f}**
        
        **3. Budget & Tax Allocation:** * Expected Tax = Base({game.annual_budget}) + [ (New_TrueH({p_true:.4f}) - 0.5) × {t('tax_impact')}({game.tax_impact:.1f}) ] = **{p_tax:.1f}** * New_H_Index = Current({game.H_index:.4f}) - {t('midpoint_decay')}({mid_decay:.2f}) + [Total_{l_cons}({t_cons}) / R_Value({r_val:.2f}) × 0.001] = **{p_h_idx:.4f}**
        * {t('h_inc')} = Tax({p_tax:.1f}) × H_Index({p_h_idx:.4f}) = **{h_inc:.1f}**
        * {t('r_inc')} = Tax({p_tax:.1f}) × (1 - H_Index) = **{r_inc:.1f}**
        * {st.session_state.name_a} {t('total_inc')} = Base({game.base_income}) + {t('bonus')}({maj_A}) + Role Income({h_inc:.1f} if sim_H == "A" else {r_inc:.1f}) = **{inc_a:.1f}**
        * {st.session_state.name_b} {t('total_inc')} = Base({game.base_income}) + {t('bonus')}({maj_B}) + Role Income({h_inc:.1f} if sim_H == "B" else {r_inc:.1f}) = **{inc_b:.1f}**
        
        **4. Political Support ({st.session_state.name_a}):** * Performance_Effect = [New_TrueH({p_true:.4f}) - Baseline({game.baseline_true_H:.4f})] × [New_Rationality({p_rat:.4f}) + Emotion_Perf_Base({p_base:.2f})] = {p_eff:.4f}  
        * {l_brain}_Effect = [Net_Brain({st.session_state.in_a_brain - st.session_state.in_b_brain}) × {t('bw_impact')}({game.bw_mult:.4f})] × [Emotion_BW_Ceiling({b_base:.2f}) - New_Rationality({p_rat:.4f})] = {bw_eff:.4f}  
        * Total_Change = (Perf_Effect) + {l_brain}_Effect - Expiring_Buffs = **{net_a:.2%}**
        """)

# --- ACTION BUTTONS ---
def commit_turn():
    game.R_value = st.session_state.r_val if st.session_state.r_val != 0 else 0.000001
    
    if st.session_state.do_swap and game.swap_available:
        game.current_H_party, game.current_R_party = game.current_R_party, game.current_H_party
        game.swap_available = False
        game.events.append({'year': game.year, 'type': 'Swap'})

    inputs = {
        'A': {'edu': st.session_state.in_a_edu if sim_R == "A" else 0, 'anti': st.session_state.in_a_anti if sim_R == "A" else 0, 'brain': st.session_state.in_a_brain, 'cons': st.session_state.in_a_cons},
        'B': {'edu': st.session_state.in_b_edu if sim_R == "B" else 0, 'anti': st.session_state.in_b_anti if sim_R == "B" else 0, 'brain': st.session_state.in_b_brain, 'cons': st.session_state.in_b_cons}
    }
    game.process_year(inputs)
    
    # Reset inputs for next year
    st.session_state.in_a_edu = st.session_state.in_a_anti = st.session_state.in_a_brain = st.session_state.in_a_cons = 0.0
    st.session_state.in_b_edu = st.session_state.in_b_anti = st.session_state.in_b_brain = st.session_state.in_b_cons = 0.0
    st.session_state.do_swap = False
    st.session_state.turn_phase = 0

# --- Turn-Based Phase Control ---
st.write("<br>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
if st.session_state.turn_phase == 0:
    if c2.button(t('btn_submit_prop'), type="primary", use_container_width=True):
        if cost_A > game.A_wealth or cost_B > game.B_wealth:
            st.error("⚠️ 預算超支！請調整金額後再送出。")
        else:
            st.session_state.turn_phase = 1
            st.rerun()
elif st.session_state.turn_phase == 1:
    if c2.button(t('btn_submit_react'), type="primary", use_container_width=True):
        if cost_A > game.A_wealth or cost_B > game.B_wealth:
            st.error("⚠️ 預算超支！請調整金額後再送出。")
        else:
            st.session_state.turn_phase = 2
            st.rerun()
elif st.session_state.turn_phase == 2:
    if c1.button(t('btn_revise'), use_container_width=True):
        st.session_state.turn_phase = 0
        st.rerun()
    if c2.button(t('confirm_btn'), type="primary", use_container_width=True):
        if cost_A > game.A_wealth or cost_B > game.B_wealth:
            st.error("⚠️ 預算超支！請調整金額後再送出。")
        else:
            commit_turn()
            st.rerun()
