# ==========================================
# manager.py
# 負責處理遊戲年度轉換與狀態更新
# ==========================================
import streamlit as st
import formulas

def process_year_end(game, cfg, ra, ha, d):
    # 1. 計算貪污與監測
    rp, hp = game.r_role_party, game.h_role_party
    confiscated = 0.0; caught = False
    corr_amt = d.get('total_funds', 0) * (ha['corr'] / 100.0)
    act_build = d.get('total_funds', 0) - corr_amt
    
    if ha['corr'] > 0:
        eff_inv = rp.investigate_ability * cfg['R_INV_BONUS']
        catch_prob = min(1.0, (eff_inv / cfg['MAX_ABILITY']) * (corr_amt / max(1.0, hp.wealth)) * 10.0)
        if random.random() < catch_prob:
            caught = True; confiscated = corr_amt; corr_amt = 0 
    
    # 2. GDP 與 基金結算
    h_bst = (act_build * d.get('h_ratio', 1.0) * hp.build_ability) / max(0.1, d.get('r_value', 1.0)**2)
    new_h_fund = max(0.0, game.h_fund + h_bst - (game.current_real_decay * (d.get('r_value', 1.0)**2) * 0.2 * game.h_fund))
    gdp_bst = (act_build * hp.build_ability) / cfg['BUILD_DIFF']
    new_gdp = max(0.0, game.gdp + gdp_bst - (game.current_real_decay * 1000))
    
    # 3. 執行系統達標獎勵 (剩餘法定款回收)
    h_bonus_overflow = 0.0
    if new_h_fund >= d.get('target_h_fund', 600):
        h_bonus_overflow = (new_h_fund - d.get('target_h_fund', 600)) * 0.5
    
    # 4. 收益與支持度
    budg = cfg['BASE_TOTAL_BUDGET'] + (new_gdp * cfg['HEALTH_MULTIPLIER'])
    h_shr = new_h_fund / max(1.0, budg) if budg > 0 else 0.5
    hp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == hp.name else 0) + (budg * h_shr) - d.get('h_pays',0) + corr_amt + h_bonus_overflow - (confiscated * cfg['CORRUPTION_PENALTY'] if caught else 0)
    rp_inc = cfg['DEFAULT_BONUS'] + (cfg['RULING_BONUS'] if game.ruling_party.name == rp.name else 0) + (budg * (1 - h_shr)) - d.get('r_pays',0)
    
    shift = formulas.calc_support_shift(cfg, hp, rp, new_h_fund, new_gdp, d.get('target_h_fund', 600), d.get('target_gdp', 5000), game.gdp, ha['media'], ra['media'])
    
    # 5. 競選量計算
    a_vol = ra['media'] * rp.media_ability * cfg['R_INV_BONUS'] if rp.name == game.party_A.name else ha['media'] * hp.media_ability * cfg['H_MEDIA_BONUS']
    b_vol = ra['media'] * rp.media_ability * cfg['R_INV_BONUS'] if rp.name == game.party_B.name else ha['media'] * hp.media_ability * cfg['H_MEDIA_BONUS']
    a_camp, b_camp = formulas.calculate_campaign_effect(a_vol, b_vol, cfg['CAMPAIGN_MAGNITUDE'])
    
    # 更新政黨狀態
    game.party_A.support += a_camp; game.party_B.support += b_camp
    hp.support += shift['actual_shift']; rp.support -= shift['actual_shift']
    
    # 紀錄財報
    game.last_year_report = {
        'old_gdp': game.gdp, 'old_san': game.sanity, 'old_budg': game.total_budget,
        'target_gdp': d.get('target_gdp'), 'target_h_fund': d.get('target_h_fund'),
        'h_perf': shift['h_perf'], 'h_inc': hp_inc, 'r_inc': rp_inc,
        'h_sup_shift': shift['actual_shift'], 'r_sup_shift': -shift['actual_shift'],
        'est_h_inc': d.get('h_net_est', 0), 'est_r_inc': d.get('r_net_est', 0),
        'est_h_sup_shift': d.get('h_sup_est', 0), 'est_r_sup_shift': d.get('r_sup_est', 0),
        'real_decay': game.current_real_decay, 'view_party_forecast': game.proposing_party.current_forecast,
        'h_party_name': hp.name, 'caught_corruption': caught
    }
    
    # 更新社會數值
    game.gdp, game.h_fund, game.total_budget = new_gdp, new_h_fund, budg + confiscated
    game.sanity = max(0.0, min(1.0, game.sanity - (game.emotion * 0.002) + ((ra['edu_up']+ha['edu_up']) * 0.005) - ((ra['edu_down']+ha['edu_down']) * 0.005)))
    game.emotion = max(0.0, min(100.0, game.emotion + (ha['incite'] + ra['incite']) * 0.1 - (((new_gdp - game.gdp)/max(1.0, game.gdp))*100) - (game.sanity * 20.0)))
    
    # 政黨屬性更新
    hp.wealth += hp_inc; rp.wealth += rp_inc
    return hp_inc, rp_inc
