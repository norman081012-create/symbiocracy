# ==========================================
# formulas.py
# 負責核心無狀態的純數學模型計算
# ==========================================
import math

def get_ability_maintenance(ability, cfg):
    # 維護費為當前等級的 10%
    return ability * 0.1

def calculate_upgrade_cost(current, target):
    # 升級成本呈現指數上升：1-2是2，2-3是4，3-4是8...
    # 公式: sum(2^x) 從 current 到 target-1
    if target <= current: return 0
    cost = 0
    c_int = int(current)
    t_int = int(target)
    for x in range(c_int, t_int):
        cost += (2 ** x)
    # 處理小數點(若有)的粗略估算
    return cost

def calc_economic_physics(cfg, gdp, decay_val, h_invest, build_abi):
    # 1. 衰退與阻力（本年環境）
    r_decay = decay_val * cfg['DECAY_COEFF']
    l_gdp = r_decay * gdp
    resistance = r_decay * cfg['M_RESISTANCE'] * 100 # 基準化阻力
    
    # 2. 實質產出與 GDP 更新（本年結算）
    gross = h_invest * build_abi
    c_net = max(0.0, gross - resistance)
    new_gdp = max(0.0, gdp + c_net - l_gdp)
    
    return new_gdp, c_net, l_gdp, gross, resistance

def calculate_preview(cfg, game, c_funds, c_diff, forecast_decay, view_party):
    # 預估 Phase 2 執行黨會投入的合理資金 (假設投入自己黨產的一半)
    est_h_invest = game.h_role_party.wealth * 0.5 
    
    new_gdp, c_net, l_gdp, gross, res = calc_economic_physics(cfg, game.gdp, forecast_decay, est_h_invest, game.h_role_party.build_ability)
    
    # 計算 H 達標率
    target_req = c_funds * max(0.1, c_diff)
    h_rate = min(1.0, c_net / target_req) if target_req > 0 else 1.0
    
    # 計算明年收益 (H領達標, R領失敗退款+標案殘值)
    my_is_h = (view_party.name == game.h_role_party.name)
    residual = game.project_pool - c_funds
    
    h_project_inc = c_funds * h_rate
    r_project_inc = c_funds * (1.0 - h_rate) + residual
    
    # 隔年發放的基礎金估算 (先不含明年的T，僅算專案本身回收)
    est_h_inc = h_project_inc
    est_r_inc = r_project_inc
    
    gdp_pct = ((new_gdp - game.gdp) / max(1.0, game.gdp)) * 100.0
    
    # 簡易支持度估算 (依照表現)
    sup_shift = (h_rate - 0.5) * 5.0 # 達標率大於 50% 加分，否則扣分
    
    return {
        'est_gdp': new_gdp, 'gdp_pct': gdp_pct,
        'h_inc': est_h_inc, 'r_inc': est_r_inc,
        'my_inc': est_h_inc if my_is_h else est_r_inc,
        'opp_inc': est_r_inc if my_is_h else est_h_inc,
        'h_roi': (est_h_inc / max(1.0, est_h_invest)) * 100.0 if est_h_invest > 0 else 0,
        'r_roi': (est_r_inc / max(1.0, game.total_budget)) * 100.0,
        'sup_shift': sup_shift if my_is_h else -sup_shift,
        'c_net': c_net, 'h_rate': h_rate
    }

def calc_support_shift(cfg, hp, rp, act_h_rate, gdp_pct, ha, ra):
    # 依據實際達標率與 GDP 成長率進行支持度轉移
    h_perf_score = act_h_rate * 100.0
    r_perf_score = max(0, gdp_pct * 10) # 經濟成長對 R 的監管算分
    
    h_media_pow = ha.get('media', 0) * hp.media_ability * cfg['H_MEDIA_BONUS']
    r_media_pow = ra.get('media', 0) * rp.media_ability
    
    h_blame = max(0, (1.0 - act_h_rate) * cfg['PERF_IMPACT_BASE'] * max(1.0, r_media_pow * 0.01))
    
    hp_shift = (ha.get('camp', 0) * 0.5 - h_blame) * cfg['SUPPORT_CONVERSION_RATE']
    return {'actual_shift': hp_shift}
