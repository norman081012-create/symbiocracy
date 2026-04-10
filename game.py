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
# STREAMLIT UI APP & TRANSLATION DICT
# ==========================================
TEXTS = {
    'en': {
        'settings': "⚙️ Global Settings (Adjust Anytime)",
        'style': "UI Label Style:",
        'short': "Short",
        'full': "Full",
        'name_a': "Name A:",
        'name_b': "Name B:",
        'decay_r': "Decay Range:",
        'tot_yr': "Total Years:",
        'base_b': "Base Budget:",
        'maj_b': "Major Bonus:",
        'tax_i': "Sat. Tax Impact:",
        'voter_e': "Voter Emotion:",
        'edu_i': "Edu Impact:",
        'bw_i': "BW Impact:",
        'bw_d': "BW Duration:",
        'perf_d': "Perf Duration:",
        'set_w_a': "Set Wealth A:",
        'set_w_b': "Set Wealth B:",
        'guide': "📖 Game Guide",
        'dlvl': "Detail Level:",
        'overview': "Overview",
        'how_to': "How to Play",
        'gov': "Governing",
        'tax_rev': "Tax Revenue",
        'rat_lvl': "Rationality Level",
        'mid_decay': "Midpoint Decay",
        'swap_hint': "(Both parties can toggle Execute Swap if it benefits their strategy)",
        'acc_wealth': "💰 Accumulated Wealth",
        'r_val': "R-Value:",
        'r_val_gov': "R-Value (Governing Party Only):",
        'r_val_lock': "R-Value (LOCKED):",
        'exec_swap': "Execute Swap (Locks R-Value & Roles)",
        'exec_swap_lock': "Execute Swap (LOCKED until Election)",
        'show_decay': "Show Real Decay",
        'real_decay': "Current Real Decay:",
        'hidden': "*** HIDDEN ***",
        'edu_max': "Edu (Max {0})",
        'edu_not_r': "Edu (Not R-Role)",
        'anti_max': "Anti (Max {0})",
        'anti_not_r': "Anti (Not R-Role)",
        'calc_f': "Calculate Forecast",
        'conf_end': "Confirm & End Year",
        'err_exp': "⚠️ Error: Expenditure exceeds wealth!",
        'warn_exp': "⚠️ Warning: Projected expenditure exceeds current wealth!",
        'for_res': "**Forecast Results (Midpoint Decay: {0:.2f}):**",
        'exp_inc': "Expected {0} Income:",
        'sup_chg': "Support Change:",
        'view_brk': "🧮 View Forecast Calculation Breakdown",
        'sim_fin': "=== Simulation Finished! ===",
        'restart': "Restart Game",
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
        'elec_warn': "⚠️ Election This Year!",
        'elec_1yr': "⏳ 1 Year to Election!",
        'yr': "Year"
    },
    'zh': {
        'settings': "⚙️ 全域設定 (隨時可調)",
        'style': "介面標籤樣式:",
        'short': "簡稱 (Short)",
        'full': "全名 (Full)",
        'name_a': "A黨名稱:",
        'name_b': "B黨名稱:",
        'decay_r': "衰退範圍:",
        'tot_yr': "總年數:",
        'base_b': "基礎預算:",
        'maj_b': "大黨津貼:",
        'tax_i': "滿意度稅收影響:",
        'voter_e': "選民情緒:",
        'edu_i': "教育影響力:",
        'bw_i': "洗腦影響力:",
        'bw_d': "洗腦持續年數:",
        'perf_d': "政績持續年數:",
        'set_w_a': "設定A黨資金:",
        'set_w_b': "設定B黨資金:",
        'guide': "📖 遊戲指南",
        'dlvl': "詳細程度:",
        'overview': "簡介 (Overview)",
        'how_to': "玩法 (How to Play)",
        'gov': "執政黨",
        'tax_rev': "當前稅收",
        'rat_lvl': "理智度",
        'mid_decay': "預期衰退中位數",
        'swap_hint': "(若符合自身策略，任一黨皆可提出「執行交換」)",
        'acc_wealth': "💰 累積資金",
        'r_val': "R值:",
        'r_val_gov': "R值 (僅執政黨可調):",
        'r_val_lock': "R值 (已鎖定):",
        'exec_swap': "執行交換 (鎖定R值與角色)",
        'exec_swap_lock': "執行交換 (鎖定至下次選舉)",
        'show_decay': "顯示實際衰退值",
        'real_decay': "當前實際衰退值:",
        'hidden': "*** 隱藏 ***",
        'edu_max': "教育 (最大 {0})",
        'edu_not_r': "教育 (非R角色)",
        'anti_max': "反智 (最大 {0})",
        'anti_not_r': "反智 (非R角色)",
        'calc_f': "計算預測",
        'conf_end': "確認並結束本年",
        'err_exp': "⚠️ 錯誤：支出超過現有資金！",
        'warn_exp': "⚠️ 警告：預測支出超過現有資金！",
        'for_res': "**預測結果 (衰退中位數: {0:.2f}):**",
        'exp_inc': "預期 {0} 收入:",
        'sup_chg': "支持度變化:",
        'view_brk': "🧮 查看預測計算明細",
        'sim_fin': "=== 模擬結束！ ===",
        'restart': "重新開始遊戲",
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
        'elec_warn': "⚠️ 今年是選舉年！",
        'elec_1yr': "⏳ 距離選舉剩 1 年！",
        'yr': "第"
    }
}

st.set_page_config(page_title="Symbiocracy Simulator", layout="wide")

# Init Language State First
if 'lang' not in st.session_state:
    st.session_state.lang = "English"

def t(key, *args):
    lang_code = 'en' if st.session_state.lang == "English" else 'zh'
    text = TEXTS[lang_code].get(key, key)
    if args:
        return text.format(*args)
    return text

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
    
    if diff > 0.1: # Crisis
        reason = random.choice(t('r_bad'))
        desc = t('d_cu', major_name)
        h2 = t('h_fin_c', reason, desc, st.session_state.name_a, inc_A_str, sup_A_str, st.session_state.name_b, inc_B_str, sup_B_str)
    elif diff < -0.1: # Boom
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
    inc_a = game.base_income + (game.major_bonus if game.first_party=="A" else 0) + (h_inc if sim_H=="A" else r_inc)
    inc_b = game.base_income + (game.major_bonus if game.first_party=="B" else 0) + (h_inc if sim_H=="B" else r_inc)

    return inc_a, inc_b, net_a, net_b, net_edu, p_rat, t_cons, p_true, p_tax, p_h_idx, p_eff, bw_eff, p_base, b_base, r_val


# --- UI: GLOBAL SETTINGS ---
with st.expander(t('settings'), expanded=False):
    st.session_state.lang = st.radio("Language / 語言:", ["English", "中文"], horizontal=True)
    st.session_state.label_style = st.radio(t('style'), [t('short'), t('full')], horizontal=True)
    
    c1, c2 = st.columns(2)
    st.session_state.name_a = c1.text_input(t('name_a'), st.session_state.name_a)
    st.session_state.name_b = c2.text_input(t('name_b'), st.session_state.name_b)
    
    c1, c2 = st.columns(2)
    dec_range = c1.slider(t('decay_r'), 0.0, 3.0, (game.decay_min, game.decay_max), 0.05)
    game.decay_min, game.decay_max = dec_range
    game.total_years = c2.slider(t('tot_yr'), 5, 100, game.total_years, 1)
    
    c1, c2 = st.columns(2)
    game.annual_budget = c1.number_input(t('base_b'), value=game.annual_budget, step=100)
    game.major_bonus = c2.number_input(t('maj_b'), value=game.major_bonus, step=50)

    c1, c2 = st.columns(2)
    game.tax_impact = c1.number_input(t('tax_i'), value=game.tax_impact, step=50.0)
    game.emotionality = c2.slider(t('voter_e'), 0.0, 1.0, game.emotionality, 0.05)

    c1, c2 = st.columns(2)
    game.edu_mult = c1.number_input(t('edu_i'), value=game.edu_mult, step=0.0001, format="%.4f")
    game.bw_mult = c2.number_input(t('bw_i'), value=game.bw_mult, step=0.0001, format="%.4f")

    c1, c2 = st.columns(2)
    game.bw_years = c1.number_input(t('bw_d'), value=game.bw_years, step=1)
    game.perf_years = c2.number_input(t('perf_d'), value=game.perf_years, step=1)

    c1, c2 = st.columns(2)
    game.A_wealth = c1.number_input(t('set_w_a'), value=float(game.A_wealth))
    game.B_wealth = c2.number_input(t('set_w_b'), value=float(game.B_wealth))


# --- UI: GAME GUIDE ---
with st.expander(t('guide'), expanded=False):
    col_g1, col_g2 = st.columns([3, 1])
    guide_mode = col_g2.radio(t('dlvl'), [t('overview'), t('how_to')], horizontal=True, label_visibility="collapsed")
    
    if guide_mode == t('overview'):
        col_g1.markdown(t('guide_overview'))
    else:
        col_g1.markdown(t('guide_how'))

# --- UI: HEADER & STATUS ---
mid_decay = (game.decay_min + game.decay_max) / 2
elec_warning = t('elec_warn') if game.year % 4 == 0 else (t('elec_1yr') if game.year % 4 == 3 else "")
major_name = st.session_state.name_a if game.first_party == 'A' else st.session_state.name_b

st.markdown(f"### 🏛️ {t('yr')} {game.year} | {t('gov')}: 👑 {major_name} | {t('tax_rev')}: {game.current_tax:.1f} {elec_warning}")
st.success(generate_headline())
st.write(f"**{t('rat_lvl')}:** {game.rationality:.4f} | **{t('mid_decay')}:** {mid_decay:.2f}  \n*{t('swap_hint')}*")


# --- UI: WEALTH BARS ---
max_w = max(game.A_wealth, game.B_wealth, 1)
scale = 100 / (max_w * 1.1)
st.markdown(t('acc_wealth'))
wealth_html = f"""
<div style='margin-top:10px; padding:10px; background:#f1f3f5;'>
    <div style='display:flex;'><div style='width:70px; font-weight:bold; color:orange; overflow:hidden; text-overflow:ellipsis;'>{st.session_state.name_a[:8]}</div><div style='width:{max(min(game.A_wealth * scale, 100), 1)}%; background:orange; color:white; padding-right:5px; text-align:right;'>{game.A_wealth:.1f}</div></div>
    <div style='display:flex; margin-top:5px;'><div style='width:70px; font-weight:bold; color:purple; overflow:hidden; text-overflow:ellipsis;'>{st.session_state.name_b[:8]}</div><div style='width:{max(min(game.B_wealth * scale, 100), 1)}%; background:purple; color:white; padding-right:5px; text-align:right;'>{game.B_wealth:.1f}</div></div>
</div>"""
st.markdown(wealth_html, unsafe_allow_html=True)


# --- UI: SWAP & INPUTS ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    r_desc = t('r_val_gov') if game.swap_available else t('r_val_lock')
    st.session_state.r_val = st.number_input(r_desc, value=st.session_state.r_val, disabled=not game.swap_available)
with col2:
    st.write("<br>", unsafe_allow_html=True)
    st.session_state.do_swap = st.checkbox(t('exec_swap') if game.swap_available else t('exec_swap_lock'), value=st.session_state.do_swap, disabled=not game.swap_available)
with col3:
    st.write("<br>", unsafe_allow_html=True)
    st.session_state.show_decay = st.checkbox(t('show_decay'), value=st.session_state.show_decay)

if st.session_state.show_decay:
    st.error(f"{t('real_decay')} **{game.current_decay:.4f}**")
else:
    st.markdown(f"{t('real_decay')} **{t('hidden')}**")

# Language logic for labels
if st.session_state.lang == "English":
    l_edu = "Education" if st.session_state.label_style == "Full" else "Edu"
    l_anti = "Anti-Education" if st.session_state.label_style == "Full" else "Anti"
    l_brain = "Brainwashing" if st.session_state.label_style == "Full" else "Brain"
    l_cons = "Construction" if st.session_state.label_style == "Full" else "Cons"
else:
    l_edu = "教育 (Education)" if st.session_state.label_style == "全名 (Full)" else "教育 (Edu)"
    l_anti = "反智 (Anti-Edu)" if st.session_state.label_style == "全名 (Full)" else "反智 (Anti)"
    l_brain = "洗腦 (Brainwash)" if st.session_state.label_style == "全名 (Full)" else "洗腦 (Brain)"
    l_cons = "建設 (Construction)" if st.session_state.label_style == "全名 (Full)" else "建設 (Cons)"

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
    label = f"{l_edu} (Max {max_edu:.0f})" if sim_R == "A" else t('edu_not_r')
    st.session_state.in_a_edu = st.number_input(label, min_value=0.0, max_value=float(max_edu) if sim_R=="A" else 1000000.0, value=st.session_state.in_a_edu, disabled=sim_R!="A", key='a_edu')
with colA3:
    label = f"{l_anti} (Max {max_anti:.0f})" if sim_R == "A" else t('anti_not_r')
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
    label = f"{l_edu} (Max {max_edu:.0f})" if sim_R == "B" else t('edu_not_r')
    st.session_state.in_b_edu = st.number_input(label, min_value=0.0, max_value=float(max_edu) if sim_R=="B" else 1000000.0, value=st.session_state.in_b_edu, disabled=sim_R!="B", key='b_edu')
with colB3:
    label = f"{l_anti} (Max {max_anti:.0f})" if sim_R == "B" else t('anti_not_r')
    st.session_state.in_b_anti = st.number_input(label, min_value=0.0, max_value=float(max_anti) if sim_R=="B" else 1000000.0, value=st.session_state.in_b_anti, disabled=sim_R!="B", key='b_anti')
with colB4:
    st.session_state.in_b_brain = st.number_input(f"{l_brain}:", value=st.session_state.in_b_brain, key='b_brain')
with colB5:
    st.session_state.in_b_cons = st.number_input(f"{l_cons}:", value=st.session_state.in_b_cons, key='b_cons')


# --- UI: ACTIONS & FORECAST ---
if st.session_state.error_msg:
    st.error(st.session_state.error_msg)

c1, c2 = st.columns(2)
if c2.button(t('conf_end'), type="primary", use_container_width=True):
    cost_A = st.session_state.in_a_edu + st.session_state.in_a_anti + st.session_state.in_a_brain + st.session_state.in_a_cons
    cost_B = st.session_state.in_b_edu + st.session_state.in_b_anti + st.session_state.in_b_brain + st.session_state.in_b_cons
    
    if cost_A > game.A_wealth or cost_B > game.B_wealth:
        st.session_state.error_msg = t('err_exp')
        st.rerun()
    
    st.session_state.error_msg = ""
    game.R_value = st.session_state.r_val if st.session_state.r_val != 0 else 0.000001
    
    if st.session_state.do_swap and game.swap_available:
        game.current_H_party, game.current_R_party = game.current_R_party, game.current_H_party
        game.swap_available = False
        game.events.append({'year': game.year, 'type': 'Swap'})

    inputs = {
        'A': {'edu': st.session_state.in_a_edu, 'anti': st.session_state.in_a_anti, 'brain': st.session_state.in_a_brain, 'cons': st.session_state.in_a_cons},
        'B': {'edu': st.session_state.in_b_edu, 'anti': st.session_state.in_b_anti, 'brain': st.session_state.in_b_brain, 'cons': st.session_state.in_b_cons}
    }
    game.process_year(inputs)
    
    st.session_state.in_a_edu = st.session_state.in_a_anti = st.session_state.in_a_brain = st.session_state.in_a_cons = 0.0
    st.session_state.in_b_edu = st.session_state.in_b_anti = st.session_state.in_b_brain = st.session_state.in_b_cons = 0.0
    st.session_state.do_swap = False
    
    st.rerun()

inc_a, inc_b, net_a, net_b, net_edu, p_rat, t_cons, p_true, p_tax, p_h_idx, p_eff, bw_eff, p_base, b_base, r_val = do_forecast_calc()

cost_A = st.session_state.in_a_edu + st.session_state.in_a_anti + st.session_state.in_a_brain + st.session_state.in_a_cons
cost_B = st.session_state.in_b_edu + st.session_state.in_b_anti + st.session_state.in_b_brain + st.session_state.in_b_cons
if cost_A > game.A_wealth or cost_B > game.B_wealth:
    st.warning(t('warn_exp'))

st.warning(f"""
{t('for_res', mid_decay)}
* {t('exp_inc', st.session_state.name_a)} **{inc_a:.1f}** | {t('sup_chg')} **{"+" if net_a>=0 else ""}{net_a:.2%}**
* {t('exp_inc', st.session_state.name_b)} **{inc_b:.1f}** | {t('sup_chg')} **{"+" if net_b>=0 else ""}{net_b:.2%}**
""")

with st.expander(t('view_brk')):
    st.markdown(f"""
    **1. Rationality Level:** New_Rationality = Current({game.rationality:.4f}) + [Net_{l_edu}({net_edu}) × Edu_Impact({game.edu_mult:.4f})] = **{p_rat:.4f}**
    
    **2. Satisfaction (True-H):** New_TrueH = Current({game.true_H:.4f}) - Decay_Midpoint({mid_decay:.2f}) + [Total_{l_cons}({t_cons}) × 0.001] = **{p_true:.4f}**
    
    **3. Budget & Tax Allocation:** Expected Tax = Base({game.annual_budget}) + [ (New_TrueH({p_true:.4f}) - 0.5) × Sat. Tax Impact({game.tax_impact:.1f}) ] = **{p_tax:.1f}** New_H_Index = Current({game.H_index:.4f}) - Decay_Midpoint({mid_decay:.2f}) + [Total_{l_cons}({t_cons}) / R_Value({r_val:.2f}) × 0.001] = **{p_h_idx:.4f}**
    
    **4. Political Support ({st.session_state.name_a}):** Performance_Effect = [New_TrueH({p_true:.4f}) - Baseline({game.baseline_true_H:.4f})] × [New_Rationality({p_rat:.4f}) + Emotion_Perf_Base({p_base:.2f})] = {p_eff:.4f}  
    {l_brain}_Effect = [Net_Brain({st.session_state.in_a_brain - st.session_state.in_b_brain}) × BW_Impact({game.bw_mult:.4f})] × [Emotion_BW_Ceiling({b_base:.2f}) - New_Rationality({p_rat:.4f})] = {bw_eff:.4f}  
    Total_Change = (Perf_Effect) + {l_brain}_Effect - Expiring_Buffs = **{net_a:.2%}**
    """)
