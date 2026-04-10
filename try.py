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
        'ctrl_a': "Control Party A:",
        'ctrl_b': "Control Party B:",
        'human': "Human",
        'bot': "Bot",
        'label_style': "UI Label Style:",
        'short': "Short",
        'full': "Full",
        'name_a': "Name Prosperity:",
        'name_b': "Name Equity:",
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
        'set_wealth_a': "Set Wealth Prosperity:",
        'set_wealth_b': "Set Wealth Equity:",
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

**Understanding the UI Glossary:**
* **Global Settings (Adjust Anytime):** The hidden gears of the simulation. Here you can change party names, the total length of the game, the annual budget, and the psychological makeup of the voters (Voter Emotion, Edu/BW Impact).
* **Current Tax Revenue:** The actual money generated this year to be split between the H-Role and R-Role. It is calculated by taking the Base Budget and adding/subtracting the economic impact of public Satisfaction (True-H).
* **R-Value (Friction):** Set only by the Governing Party. A *lower* R-Value makes Construction incredibly highly efficient at boosting the H-Index (benefiting the Household). A *higher* R-Value makes it sluggish.
* **The Baseline Reset (Elections):** Held every 4 years. The party with >50% Support takes the Governing (👑) seat. Crucially, the "Baseline Satisfaction" resets to the current True-H. You get zero credit for the previous administration's work; you are judged purely on how much you improve or ruin the country *after* taking power.
        """,
        'guide_deep': """
### ⚙️ Deep Dive: The Mechanics of Support & Expiry

Here is a breakdown of the core mechanism that drives political support:

**1. What matters is the sense of improvement: The Baseline Reset Mechanism**
Voters are both forgetful and pragmatic. The game relies on a hidden variable called `baseline_true_H` (Baseline Satisfaction):
* **Reset on taking office:** When a party wins the election and takes the Governing (👑) seat, the system records the current satisfaction level as its new "baseline."
* **Support Formula:** `Performance_Effect = (Current Satisfaction - Baseline Satisfaction) * (Weight Coefficient)`
* **Implication:** If you take office when the country is already in great shape (e.g., 0.8) and let it fall to 0.7, voters will think you performed terribly. On the other hand, if you inherit a disaster at 0.1 and manage to raise it to 0.2, voters may see you as a savior.

**2. Rationality is the amplifier: It filters how Satisfaction becomes Support**
How efficiently satisfaction is converted into political support depends heavily on the society’s **Rationality Level**:
* **High Rationality:** Voters accurately translate actual living conditions (True-H) into political judgment. In the formula, rationality acts as a positive multiplier for the `Performance_Effect`.
* **Low Rationality:** Voters become dull. Even if you drastically improve True-H through real infrastructure investments, if the society's Rationality has been pushed very low, voters will barely notice, and your support will rise at a crawl.

**3. Voter Emotionality acts as a counterweight: Emotion vs. Rationality**
In the calculation, the `perf_base` (the base weight of actual performance) is directly modified by the **Voter Emotion** slider:
* **Rational Society (Low Emotion):** Voters maintain a higher baseline expectation for performance. Even if Rationality isn't exceptionally high, they will still react angrily when Satisfaction falls. This makes "doing nothing to save money" an extremely risky strategy for the ruling party.
* **Emotional Society (High Emotion):** The `perf_base` plummets. This means that if Rationality is also suppressed, voters may stop caring about actual Satisfaction almost entirely. Under these specific conditions, a party can allow the country to decay while staying in power purely through aggressive "Brainwashing."

**4. Time matters: The Expiry Mechanism**
Political credit does not last forever. Both voter gratitude and manipulation have an expiration date:
* **Performance Expiry (Default 6 Years):** If you gain a massive surge in support in Year 1 by sharply improving satisfaction through construction, that specific support bonus begins to expire and will be deducted from your total starting in Year 7.
* **Brainwashing Expiry (Default 2 Years):** Brainwashing is a powerful, instant injection of support, but it fades very quickly. If you rely on it, you must keep spending to maintain the illusion.
* **Dynamic Challenge:** To maintain power, the ruling party cannot rest on its past achievements. It must continuously invest to keep True-H climbing above the baseline. Otherwise, once old bonuses (from Performance or Brainwashing) begin to expire, support can collapse off a cliff.
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
        'yr': "Year",
        'err_exp': "⚠️ Budget Exceeded!"
    },
    '中文': {
        'settings': "⚙️ 全域設定 (隨時可調)",
        'lang': "語言:",
        'ctrl_a': "A黨控制模式:",
        'ctrl_b': "B黨控制模式:",
        'human': "玩家",
        'bot': "電腦",
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
        'err_exp': "⚠️ 預算超支！"
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
    st.session_state.ctrl_a = "Human"
    st.session_state.ctrl_b = "Bot"
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

# ==========================================
# BOT STRATEGY ENGINE
# ==========================================
def execute_bot_turn(party):
    """
    Executes the bot's logic for the given party ('A' or 'B').
    The bot analyzes the current state and allocates its wealth.
    """
    is_ruling = (game.first_party == party)
    holds_R_role = (game.current_R_party == party)
    wealth = game.A_wealth if party == "A" else game.B_wealth
    
    # Base allocations
    edu = 0.0
    anti = 0.0
    brain = 0.0
    cons = 0.0
    
    # 1. Determine R-Value and Swap if Ruling/Proposing
    # If the bot is proposing (Phase 0) or reacting (Phase 1)
    if st.session_state.turn_phase == 0 and is_ruling:
        # Bot is ruling. It sets the R-value based on whether it holds the H-Role
        if not holds_R_role: # Bot holds H-Role
            st.session_state.r_val = random.uniform(0.1, 0.4) # Low R-value favors H-Role
        else: # Bot holds R-Role
            st.session_state.r_val = random.uniform(0.6, 0.9) # High R-value hinders H-Role
            
    # Swap Logic: Bot proposes a swap if it's struggling (Support < 45% and not ruling)
    if game.swap_available and not is_ruling and (game.A_support if party=="A" else game.B_support) < 0.45:
        # 30% chance to desperately trigger a swap to disrupt the game
        if random.random() < 0.3:
            st.session_state.do_swap = True

    # 2. Wealth Allocation Strategy
    # Bot only spends a portion of its wealth to save for future turns
    budget_to_spend = wealth * random.uniform(0.4, 0.8) 
    remaining_budget = budget_to_spend

    # STRATEGY A: Regulator (R-Role) Logic
    if holds_R_role:
        if game.rationality > 0.6:
            # If rationality is high, try to lower it (Anti-Edu) so Brainwashing works later
            alloc = min(remaining_budget * 0.4, (game.rationality / game.edu_mult))
            anti = alloc
            remaining_budget -= alloc
        elif game.rationality < 0.3:
            # If rationality is very low, capitalize heavily on Brainwashing
            alloc = remaining_budget * 0.6
            brain = alloc
            remaining_budget -= alloc
        else:
            # Balanced approach
            alloc = remaining_budget * 0.2
            brain = alloc
            remaining_budget -= alloc

    # STRATEGY B: Household (H-Role) Logic
    else:
        # If the bot holds the H-Role, its main way to gain Support/Money is Construction
        if game.true_H < 0.4:
            # Crisis mode: Country is failing, must build to survive
            alloc = remaining_budget * 0.7
            cons = alloc
            remaining_budget -= alloc
        else:
            # Stable mode: Build a bit to keep money flowing
            alloc = remaining_budget * 0.4
            cons = alloc
            remaining_budget -= alloc

    # STRATEGY C: General Support Boosting (Available to both)
    # If the bot is close to an election (Year % 4 == 3) or losing badly, spam Brainwash
    is_election_near = (game.year % 4 == 3)
    if is_election_near or ((game.A_support if party=="A" else game.B_support) < 0.48):
        alloc = remaining_budget * 0.8
        brain += alloc
        remaining_budget -= alloc

    # Dump whatever small amount is left into Construction for good measure
    cons += remaining_budget

    # 3. Apply to Session State
    if party == "A":
        st.session_state.in_a_edu = round(edu, 1)
        st.session_state.in_a_anti = round(anti, 1)
        st.session_state.in_a_brain = round(brain, 1)
        st.session_state.in_a_cons = round(cons, 1)
    else:
        st.session_state.in_b_edu = round(edu, 1)
        st.session_state.in_b_anti = round(anti, 1)
        st.session_state.in_b_brain = round(brain, 1)
        st.session_state.in_b_cons = round(cons, 1)

# --- BOT TURN TRIGGER LOGIC ---
# This checks if the current phase belongs to a Bot and executes their move
current_acting_party = game.first_party if st.session_state.turn_phase == 0 else ("B" if game.first_party == "A" else "A")
acting_party_ctrl = st.session_state.ctrl_a if current_acting_party == "A" else st.session_state.ctrl_b

if acting_party_ctrl == "Bot":
    if st.session_state.turn_phase == 0:
        # Phase 0: Bot is Ruling Party
        execute_bot_turn(current_acting_party)
        st.session_state.turn_phase = 1 # Pass to Phase 1
        st.rerun()
    elif st.session_state.turn_phase == 1:
        # Phase 1: Bot is Opposition Party
        execute_bot_turn(current_acting_party)
        st.session_state.turn_phase = 2 # Pass to Phase 2 (Final Review)
        st.rerun()
