import random

class SymbiocracyGame:
    def __init__(self):
        # 初始化數據
        self.name_A = "Prosperity"
        self.name_B = "Equity"
        self.year = 1
        self.total_years = 20
        self.annual_budget = 1000
        self.base_income = 100
        self.major_bonus = 200
        self.edu_mult = 0.001
        self.bw_mult = 0.001
        self.emotionality = 0.5
        self.bw_years = 2
        self.perf_years = 6
        self.tax_impact = 200.0 
        self.A_support = 0.51
        self.B_support = 0.49
        self.A_wealth = 500 
        self.B_wealth = 500 
        self.H_index = 0.5
        self.true_H = 0.5
        self.R_value = 0.5
        self.rationality = 0.5
        self.baseline_true_H = 0.5
        self.decay_min = 0.2
        self.decay_max = 1.2
        self.current_decay = random.uniform(self.decay_min, self.decay_max)
        self.last_year_decay = self.current_decay
        self.last_report = None
        self.bw_expiry = {}
        self.perf_expiry = {}
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

        # 理智度更新
        sim_R = self.current_R_party 
        net_edu_A = (inputs['A']['edu'] - inputs['A']['anti']) if sim_R == "A" else 0
        net_edu_B = (inputs['B']['edu'] - inputs['B']['anti']) if sim_R == "B" else 0
        new_rat = max(0, min(1, self.rationality + (net_edu_A + net_edu_B) * self.edu_mult))

        # 滿意度更新
        act_true_H = self.true_H - act_decay + (tot_cons * 0.001)
        exp_true_H = self.true_H - exp_decay + (tot_cons * 0.001)

        # H-Index 更新
        safe_R = self.R_value if self.R_value != 0 else 0.000001
        act_H_idx = max(0, min(1, self.H_index - act_decay + (tot_cons / safe_R) * 0.001))
        exp_H_idx = max(0, min(1, self.H_index - exp_decay + (tot_cons / safe_R) * 0.001))

        # 稅收與收入計算
        act_tax = max(0, self.annual_budget + ((act_true_H - 0.5) * self.tax_impact))
        exp_tax = max(0, self.annual_budget + ((exp_true_H - 0.5) * self.tax_impact))

        act_h_inc = act_tax * act_H_idx
        act_r_inc = act_tax * (1 - act_H_idx)
        exp_h_inc = exp_tax * exp_H_idx
        exp_r_inc = exp_tax * (1 - exp_H_idx)

        maj_A = self.major_bonus if self.first_party == "A" else 0
        maj_B = self.major_bonus if self.first_party == "B" else 0

        act_inc_A = self.base_income + maj_A + (act_h_inc if self.current_H_party == "A" else act_r_inc)
        act_inc_B = self.base_income + maj_B + (act_h_inc if self.current_H_party == "B" else act_r_inc)
        exp_inc_A = self.base_income + maj_A + (exp_h_inc if self.current_H_party == "A" else exp_r_inc)
        exp_inc_B = self.base_income + maj_B + (exp_h_inc if self.current_H_party == "B" else exp_r_inc)

        # 支持度計算
        perf_base = 0.2 - (self.emotionality - 0.5) * 0.4
        bw_base = 1.1 + (self.emotionality - 0.5) * 0.4
        bw_eff = (inputs['A']['brain'] - inputs['B']['brain']) * self.bw_mult * (bw_base - new_rat)

        act_perf = (act_true_H - self.baseline_true_H) * (new_rat + perf_base)
        exp_perf = (exp_true_H - self.baseline_true_H) * (new_rat + perf_base)

        act_perf_A = act_perf if self.first_party == "A" else -act_perf
        exp_perf_A = exp_perf if self.first_party == "A" else -exp_perf

        exp_bw = self.bw_expiry.get(self.year, 0.0)
        exp_pf = self.perf_expiry.get(self.year, 0.0)

        act_net_A = act_perf_A + bw_eff - exp_pf - exp_bw
        exp_net_A = exp_perf_A + bw_eff - exp_pf - exp_bw

        # 寫入報告
        self.last_report = {
            'exp_decay': exp_decay,
            'act_decay': act_decay,
            'exp_inc_A': exp_inc_A,
            'act_inc_A': act_inc_A,
            'exp_inc_B': exp_inc_B,
            'act_inc_B': act_inc_B,
            'exp_net_A': exp_net_A,
            'act_net_A': act_net_A,
            'exp_net_B': -exp_net_A,
            'act_net_B': -act_net_A,
            'blame_party': self.first_party,
            'election_just_happened': False,
            'new_major': None
        }

        # 更新狀態
        self.rationality = new_rat
        self.true_H = act_true_H
        self.H_index = act_H_idx
        self.A_wealth += act_inc_A - sum(inputs['A'].values())
        self.B_wealth += act_inc_B - sum(inputs['B'].values())

        # 過期紀錄
        self.bw_expiry[self.year + self.bw_years] = bw_eff
        self.perf_expiry[self.year + self.perf_years] = act_perf_A

        self.A_support = max(0, min(1, self.A_support + act_net_A))
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
        # 選舉邏輯
        if (self.year - 1) % 4 == 0 and self.year <= self.total_years:
            new_first = "A" if self.A_support > 0.5 else "B"
            if new_first != self.first_party:
                self.baseline_true_H = self.true_H
            self.first_party = new_first
            self.swap_available = True
            self.current_R_party = self.first_party
            self.current_H_party = "B" if self.first_party == "A" else "A"
            self.last_report['election_just_happened'] = True
            self.last_report['new_major'] = self.first_party

        self.current_decay = random.uniform(self.decay_min, self.decay_max)
