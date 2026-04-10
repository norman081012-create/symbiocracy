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

        self.last_year_decay = self.current_decay
        self.current_decay = random.uniform(self.decay_min, self.decay_max)

        if self.year <= self.total_years:
            self.allocate_budget()


# ==========================================
# STREAMLIT UI APP
# ==========================================
st.set_page_config(page_title="Symbiocracy Simulator", layout="wide")

# --- INITIALIZE STATE ---
if 'game' not in st.session_state:
    st.session_state.game = SymbiocracyGame()
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

# Check for End Game
if game.year > game.total_years:
    st.success("=== Simulation Finished! ===")
    df = pd.DataFrame(game.history)
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.set_xlabel('Year', fontweight='bold')
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
    
    if st.button("Restart Game"):
        st.session_state.game = SymbiocracyGame()
        st.rerun()
    st.stop()


# --- HELPER FUNCTIONS ---
def generate_headline():
    if game.year == 1:
        return f"📰 **Headline:** *New Government Takes Office! Welcome to Year 1.*"
    
    rep = game.last_report
    if not rep: return ""
    
    major_name = st.session_state.name_a if rep['blame_party'] == 'A' else st.session_state.name_b
    
    h1 = ""
    if rep['election_just_happened']:
        new_major_name = st.session_state.name_a if rep['new_major'] == 'A' else st.session_state.name_b
        h1 = f"📰 **Headline:** Election Concluded! **{new_major_name}** secures the majority!\n\n"
    
    diff = rep['act_decay'] - rep['exp_decay']
    reasons_bad = ["Severe geopolitical tension", "An unforeseen virus outbreak", "Devastating earthquakes"]
    reasons_good = ["A major technological breakthrough", "An unprecedented economic boom", "Global peace and stability"]
    
    def fmt_inc(exp, act): return f"**{act:.1f}** (Expected: {exp:.1f})"
    def fmt_sup(exp, act): return f"**{act:+.2%}** (Expected: {exp:+.2%})"

    inc_A_str = fmt_inc(rep['exp_inc_A'], rep['act_inc_A'])
    inc_B_str = fmt_inc(rep['exp_inc_B'], rep['act_inc_B'])
    sup_A_str = fmt_sup(rep['exp_net_A'], rep['act_net_A'])
    sup_B_str = fmt_sup(rep['exp_net_B'], rep['act_net_B'])
    
    if diff > 0.1: # Crisis
        reason = random.choice(reasons_bad)
        desc = f"Voters are disappointed in {major_name}, actively punishing them in the polls."
        h2 = f"📰 **Financial Report:** {reason}. {desc} Consequently, **{st.session_state.name_a}** secured a revenue of {inc_A_str} with a support shift of {sup_A_str}, while **{st.session_state.name_b}** secured {inc_B_str} with a support shift of {sup_B_str}."
    elif diff < -0.1: # Boom
        reason = random.choice(reasons_good)
        desc = f"Voters are relieved, softening their stance and rewarding {major_name}."
        h2 = f"📰 **Financial Report:** {reason}. {desc} Consequently, **{st.session_state.name_a}** secured a revenue of {inc_A_str} with a support shift of {sup_A_str}, while **{st.session_state.name_b}** secured {inc_B_str} with a support shift of {sup_B_str}."
    else:
        h2 = f"📰 **Financial Report:** Stability maintained. Real outcomes closely aligned with forecasts. **{st.session_state.name_a}** gained {inc_A_str} in revenue (Support Shift: {sup_A_str}), and **{st.session_state.name_b}** gained {inc_B_str} (Support Shift: {sup_B_str})."
        
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


# --- UI: GLOBAL SETTINGS ---
with st.expander("⚙️ Global Settings (Adjust Anytime)", expanded=False):
    st.session_state.label_style = st.radio("UI Label Style:", ["Short", "Full"], horizontal=True)
    
    c1, c2 = st.columns(2)
    st.session_state.name_a = c1.text_input("Name A:", st.session_state.name_a)
    st.session_state.name_b = c2.text_input("Name B:", st.session_state.name_b)
    
    c1, c2 = st.columns(2)
    dec_range = c1.slider("Decay Range:", 0.0, 3.0, (game.decay_min, game.decay_max), 0.05)
    game.decay_min, game.decay_max = dec_range
    game.total_years = c2.slider("Total Years:", 5, 100, game.total_years, 1)
    
    c1, c2 = st.columns(2)
    game.annual_budget = c1.number_input("Base Budget:", value=game.annual_budget, step=100)
    game.major_bonus = c2.number_input("Major Bonus:", value=game.major_bonus, step=50)

    c1, c2 = st.columns(2)
    game.tax_impact = c1.number_input("Sat. Tax Impact:", value=game.tax_impact, step=50.0)
    game.emotionality = c2.slider("Voter Emotion:", 0.0, 1.0, game.emotionality, 0.05)

    c1, c2 = st.columns(2)
    game.edu_mult = c1.number_input("Edu Impact:", value=game.edu_mult, step=0.0001, format="%.4f")
    game.bw_mult = c2.number_input("BW Impact:", value=game.bw_mult, step=0.0001, format="%.4f")

    c1, c2 = st.columns(2)
    game.bw_years = c1.number_input("BW Duration:", value=game.bw_years, step=1)
    game.perf_years = c2.number_input("Perf Duration:", value=game.perf_years, step=1)

    c1, c2 = st.columns(2)
    game.A_wealth = c1.number_input("Set Wealth A:", value=float(game.A_wealth))
    game.B_wealth = c2.number_input("Set Wealth B:", value=float(game.B_wealth))


# --- UI: GAME GUIDE ---
with st.expander("📖 Game Guide", expanded=False):
    col_g1, col_g2 = st.columns([3, 1])
    guide_mode = col_g2.radio("Detail Level:", ["Overview", "How to Play"], horizontal=True, label_visibility="collapsed")
    
    if guide_mode == "Overview":
        col_g1.markdown("""
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
        """)
    else:
        col_g1.markdown("""
        ### 📖 How to Play & UI Guide
        
        **Step-by-Step Turn Guide:**
        1. **Assess the Year:** Look at the top **Status Board**. Read the Newspaper Headline to understand the current economic climate, and check the Midpoint Decay. High decay means your Satisfaction and budget will drop drastically this year.
        2. **Negotiate:** Discuss strategy with the opposing party. Decide if executing a **Swap** is necessary for either of you to survive the year.
        3. **Draft Budgets:** Both parties allocate their accumulated wealth into their respective input boxes (Edu, Anti, Brain, Cons).
        4. **Check the Math:** *Do not click Confirm yet!* Click **"Calculate Forecast"** and open the **"View Forecast Calculation Breakdown"** tab. This shows exactly how your proposed spending will change Income and Approval Ratings.
        5. **Revise & Execute:** Adjust your spending based on the forecast. Once both parties agree on their final numbers, click **Confirm & End Year** to lock in the results and advance time.
        
        **Understanding the UI Glossary:**
        * **Global Settings (Adjust Anytime):** The hidden gears of the simulation. Here you can change party names, the total length of the game, the annual budget, and the psychological makeup of the voters (Voter Emotion, Edu/BW Impact).
        * **Current Tax Revenue:** The actual money generated this year to be split between the H-Role and R-Role. It is calculated by taking the Base Budget and adding/subtracting the economic impact of public Satisfaction (True-H).
        * **R-Value (Friction):** Set only by the Governing Party. A *lower* R-Value makes Construction incredibly highly efficient at boosting the H-Index (benefiting the Household). A *higher* R-Value makes it sluggish.
        * **The Baseline Reset (Elections):** Held every 4 years. The party with >50% Support takes the Governing (👑) seat. Crucially, the "Baseline Satisfaction" resets to the current True-H. You get zero credit for the previous administration's work; you are judged purely on how much you improve or ruin the country *after* taking power.
        """)

# --- UI: HEADER & STATUS ---
mid_decay = (game.decay_min + game.decay_max) / 2
elec_warning = "⚠️ Election This Year!" if game.year % 4 == 0 else ("⏳ 1 Year to Election!" if game.year % 4 == 3 else "")
major_name = st.session_state.name_a if game.first_party == 'A' else st.session_state.name_b

st.markdown(f"### 🏛️ Year {game.year} | Governing: 👑 {major_name} | Tax Revenue: {game.current_tax:.1f} {elec_warning}")
st.success(generate_headline())
st.write(f"**Rationality Level:** {game.rationality:.4f} | **Midpoint Decay:** {mid_decay:.2f}  \n*(Both parties can toggle Execute Swap if it benefits their strategy)*")


# --- UI: WEALTH BARS ---
max_w = max(game.A_wealth, game.B_wealth, 1)
scale = 100 / (max_w * 1.1)
st.markdown("**💰 Accumulated Wealth**")
st.progress(max(min(game.A_wealth * scale / 100, 1.0), 0.01), text=f"{st.session_state.name_a}: {game.A_wealth:.1f}")
st.progress(max(min(game.B_wealth * scale / 100, 1.0), 0.01), text=f"{st.session_state.name_b}: {game.B_wealth:.1f}")


# --- UI: SWAP & INPUTS ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    r_desc = "R-Value (Governing Party Only):" if game.swap_available else "R-Value (LOCKED):"
    st.session_state.r_val = st.number_input(r_desc, value=st.session_state.r_val, disabled=not game.swap_available)
with col2:
    st.write("<br>", unsafe_allow_html=True)
    st.session_state.do_swap = st.checkbox("Execute Swap (Locks R-Value & Roles)", value=st.session_state.do_swap, disabled=not game.swap_available)
with col3:
    st.write("<br>", unsafe_allow_html=True)
    st.session_state.show_decay = st.checkbox("Show Real Decay", value=st.session_state.show_decay)

if st.session_state.show_decay:
    st.error(f"Current Real Decay: **{game.current_decay:.4f}**")


# Determine Labels based on Settings Toggle
l_edu = "Education" if st.session_state.label_style == "Full" else "Edu"
l_anti = "Anti-Education" if st.session_state.label_style == "Full" else "Anti"
l_brain = "Brainwashing" if st.session_state.label_style == "Full" else "Brain"
l_cons = "Construction" if st.session_state.label_style == "Full" else "Cons"

sim_R = game.current_H_party if st.session_state.do_swap else game.current_R_party
sim_H = game.current_R_party if st.session_state.do_swap else game.current_H_party

max_edu = max(0, (1.0 - game.rationality) / game.edu_mult)
max_anti = max(0, game.rationality / game.edu_mult)

st.divider()

# Party A Inputs
colA1, colA2, colA3, colA4, colA5 = st.columns([1.5, 1, 1, 1, 1])
role_A = "H-Role" if sim_H == "A" else "R-Role"
colA1.success(f"👑 **{st.session_state.name_a} ({role_A})** \nAppr: {game.A_support:.2%}")

with colA2:
    label = f"{l_edu} (Max {max_edu:.0f})" if sim_R == "A" else f"{l_edu} (Not R-Role)"
    st.session_state.in_a_edu = st.number_input(label, min_value=0.0, max_value=float(max_edu) if sim_R=="A" else 1000000.0, value=st.session_state.in_a_edu, disabled=sim_R!="A", key='a_edu')
with colA3:
    label = f"{l_anti} (Max {max_anti:.0f})" if sim_R == "A" else f"{l_anti} (Not R-Role)"
    st.session_state.in_a_anti = st.number_input(label, min_value=0.0, max_value=float(max_anti) if sim_R=="A" else 1000000.0, value=st.session_state.in_a_anti, disabled=sim_R!="A", key='a_anti')
with colA4:
    st.session_state.in_a_brain = st.number_input(f"{l_brain}:", value=st.session_state.in_a_brain, key='a_brain')
with colA5:
    st.session_state.in_a_cons = st.number_input(f"{l_cons}:", value=st.session_state.in_a_cons, key='a_cons')


# Party B Inputs
colB1, colB2, colB3, colB4, colB5 = st.columns([1.5, 1, 1, 1, 1])
role_B = "H-Role" if sim_H == "B" else "R-Role"
colB1.info(f"**{st.session_state.name_b} ({role_B})** \nAppr: {game.B_support:.2%}")

with colB2:
    label = f"{l_edu} (Max {max_edu:.0f})" if sim_R == "B" else f"{l_edu} (Not R-Role)"
    st.session_state.in_b_edu = st.number_input(label, min_value=0.0, max_value=float(max_edu) if sim_R=="B" else 1000000.0, value=st.session_state.in_b_edu, disabled=sim_R!="B", key='b_edu')
with colB3:
    label = f"{l_anti} (Max {max_anti:.0f})" if sim_R == "B" else f"{l_anti} (Not R-Role)"
    st.session_state.in_b_anti = st.number_input(label, min_value=0.0, max_value=float(max_anti) if sim_R=="B" else 1000000.0, value=st.session_state.in_b_anti, disabled=sim_R!="B", key='b_anti')
with colB4:
    st.session_state.in_b_brain = st.number_input(f"{l_brain}:", value=st.session_state.in_b_brain, key='b_brain')
with colB5:
    st.session_state.in_b_cons = st.number_input(f"{l_cons}:", value=st.session_state.in_b_cons, key='b_cons')


# --- UI: ACTIONS & FORECAST ---
if st.session_state.error_msg:
    st.error(st.session_state.error_msg)

c1, c2 = st.columns(2)
if c2.button("Confirm & End Year", type="primary", use_container_width=True):
    cost_A = st.session_state.in_a_edu + st.session_state.in_a_anti + st.session_state.in_a_brain + st.session_state.in_a_cons
    cost_B = st.session_state.in_b_edu + st.session_state.in_b_anti + st.session_state.in_b_brain + st.session_state.in_b_cons
    
    if cost_A > game.A_wealth or cost_B > game.B_wealth:
        st.session_state.error_msg = "⚠️ Error: Expenditure exceeds wealth!"
        st.rerun()
    
    st.session_state.error_msg = ""
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
    
    # Reset inputs
    st.session_state.in_a_edu = st.session_state.in_a_anti = st.session_state.in_a_brain = st.session_state.in_a_cons = 0.0
    st.session_state.in_b_edu = st.session_state.in_b_anti = st.session_state.in_b_brain = st.session_state.in_b_cons = 0.0
    st.session_state.do_swap = False
    
    st.rerun()

# Always render live forecast below
inc_a, inc_b, net_a, net_b, net_edu, p_rat, t_cons, p_true, p_tax, p_h_idx, p_eff, bw_eff, p_base, b_base, r_val, h_inc, r_inc, maj_A, maj_B = do_forecast_calc()

cost_A = st.session_state.in_a_edu + st.session_state.in_a_anti + st.session_state.in_a_brain + st.session_state.in_a_cons
cost_B = st.session_state.in_b_edu + st.session_state.in_b_anti + st.session_state.in_b_brain + st.session_state.in_b_cons
if cost_A > game.A_wealth or cost_B > game.B_wealth:
    st.warning("⚠️ Warning: Projected expenditure exceeds current wealth!")
    
wasted_warn = ""
if st.session_state.do_swap:
    if (st.session_state.in_a_edu > 0 or st.session_state.in_a_anti > 0) and sim_R != "A":
        wasted_warn += f"\n* ⚠️ **Warning:** {st.session_state.name_a} will waste funds placed in Edu/Anti due to the proposed Swap."
    if (st.session_state.in_b_edu > 0 or st.session_state.in_b_anti > 0) and sim_R != "B":
        wasted_warn += f"\n* ⚠️ **Warning:** {st.session_state.name_b} will waste funds placed in Edu/Anti due to the proposed Swap."

st.warning(f"""
**Forecast Results (Midpoint Decay: {mid_decay:.2f}):**
* Expected {st.session_state.name_a} Income: **{inc_a:.1f}** | Support Change: **{"+" if net_a>=0 else ""}{net_a:.2%}**
* Expected {st.session_state.name_b} Income: **{inc_b:.1f}** | Support Change: **{"+" if net_b>=0 else ""}{net_b:.2%}** {wasted_warn}
""")

with st.expander("🧮 View Forecast Calculation Breakdown"):
    st.markdown(f"""
    **1. Rationality Level:** New_Rationality = Current({game.rationality:.4f}) + [Net_{l_edu}({net_edu}) × Edu_Impact({game.edu_mult:.4f})] = **{p_rat:.4f}**
    
    **2. Satisfaction (True-H):** New_TrueH = Current({game.true_H:.4f}) - Decay_Midpoint({mid_decay:.2f}) + [Total_{l_cons}({t_cons}) × 0.001] = **{p_true:.4f}**
    
    **3. Budget & Tax Allocation:** * Expected Tax = Base({game.annual_budget}) + [ (New_TrueH({p_true:.4f}) - 0.5) × Sat. Tax Impact({game.tax_impact:.1f}) ] = **{p_tax:.1f}** * New_H_Index = Current({game.H_index:.4f}) - Decay_Midpoint({mid_decay:.2f}) + [Total_{l_cons}({t_cons}) / R_Value({r_val:.2f}) × 0.001] = **{p_h_idx:.4f}**
    * H-Role Income = Tax({p_tax:.1f}) × H_Index({p_h_idx:.4f}) = **{h_inc:.1f}**
    * R-Role Income = Tax({p_tax:.1f}) × (1 - H_Index) = **{r_inc:.1f}**
    * {st.session_state.name_a} Total Income = Base({game.base_income}) + Bonus({maj_A}) + Role Income({h_inc:.1f} if H else {r_inc:.1f}) = **{inc_a:.1f}**
    * {st.session_state.name_b} Total Income = Base({game.base_income}) + Bonus({maj_B}) + Role Income({h_inc:.1f} if H else {r_inc:.1f}) = **{inc_b:.1f}**
    
    **4. Political Support ({st.session_state.name_a}):** * Performance_Effect = [New_TrueH({p_true:.4f}) - Baseline({game.baseline_true_H:.4f})] × [New_Rationality({p_rat:.4f}) + Emotion_Perf_Base({p_base:.2f})] = {p_eff:.4f}  
    * {l_brain}_Effect = [Net_Brain({st.session_state.in_a_brain - st.session_state.in_b_brain}) × BW_Impact({game.bw_mult:.4f})] × [Emotion_BW_Ceiling({b_base:.2f}) - New_Rationality({p_rat:.4f})] = {bw_eff:.4f}  
    * Total_Change = (Perf_Effect) + {l_brain}_Effect - Expiring_Buffs = **{net_a:.2%}**
    """)
