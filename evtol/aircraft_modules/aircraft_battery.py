# aircraft_battery.py
#
# Battery module for aircraft model
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import copy # deepcopy
import json # json parsing
import math # log10, pi
import sys  # not needed when using as a package

# constants
W_P_KW = 1000.0
S_P_HR = 3600.0
KG_2_LB = 2.20462
M_2_FT = 3.28084
M_P_S_2_KTS = 1.9438
N_P_M2_2_LB_P_FT2 = 0.0209

# battery charging time estimator (based on CC–CV Model)
# estimates total charge time [hr] from SOC_start to SOC_target
# using the analytical expressions from Donateo et al., "Fuel economy of hybrid electric flight", (2017) 
# where:
#   t_CC = (SOC_CC - SOC_start) * (C / I_cc)
#   t_CV = (SOC_target - SOC_CC) * (C / I_cc) * ln(1/k) / (1 - k)
#
# Inputs:
#   E_pack_kwh        : pack energy capacity [kWh]
#   P_charger_ac_kw   : charger AC power [kW]
#   eta_charger_dc    : charger AC->DC efficiency (0–1)
#   c_rate_max        : max allowed charge C-rate (e.g., 1.0C)
#   v_pack_nom_v      : nominal pack voltage [V]
#   i_term_c          : CV termination current ratio (e.g., 0.05C) - CV phase stops when current tapers to this level
#   soc_start         : initial SOC (0–1)
#   soc_target        : target SOC (0–1)
#   soc_cc_end        : SOC where CC ends & CV begins (0.80–0.90 typical)
#   dod               : optional depth of discharge (0–1) if soc_start not given
#   Q_Ah              : optional pack capacity [Ah]; if None, inferred via E_pack_kwh and voltage
def _estimate_cccv_charge_time_hr(aircraft,
                                 E_pack_kwh,
                                 P_charger_ac_kw,
                                 eta_charger_dc=0.95,
                                 c_rate_max=1.0,
                                 v_pack_nom_v=800.0,
                                 i_term_c=0.05,
                                 soc_start=None,
                                 soc_target=1.0,
                                 soc_cc_end=0.80,
                                 dod=None,
                                 Q_Ah=None):
    
    if E_pack_kwh is None or E_pack_kwh <= 0.0:
      return None
    if P_charger_ac_kw is None or P_charger_ac_kw <= 0.0:
      return None
    if not (0.0 < eta_charger_dc <= 1.0):
      return None
    soc_target = max(0.0, min(1.0, soc_target))
    soc_cc_end = max(0.0, min(1.0, soc_cc_end))

    # infer SOC_start from DoD if not provided
    if soc_start is None:
      if dod is None:
        # if nothing provided, assume full recharge: start at 0
        soc_start = 0.0
      else:
        soc_start = max(0.0, soc_target - float(dod))
    soc_start = max(0.0, min(1.0, soc_start))

    if soc_start >= soc_target:
      return {"t_cc_hr": 0.0, "t_cv_hr": 0.0, "t_charge_hr": 0.0}

    # convert pack energy to 1C equivalent power (at 1C, charging power ≈ E_pack_kwh kW if voltage were constant)
    P_1C_kw = E_pack_kwh

    # power limited by charger
    P_dc_kw = eta_charger_dc * P_charger_ac_kw

    # power limited by C-rate
    P_c_rate_cap_kw = c_rate_max * P_1C_kw

    # actual CC power (limited by charger or C-rate)
    P_cc_kw = min(P_dc_kw, P_c_rate_cap_kw)

    # a simple indicator to clarify whether charging is charger-limited or C-rate-limited
    charger_limit_indicator_flag = "charger_limited" if P_dc_kw <= P_c_rate_cap_kw else "crate_limited"

    # compute pack capacity if not given
    if Q_Ah is None:
      Q_Ah = (E_pack_kwh * 1000.0) / max(v_pack_nom_v, 1e-6)

    # CC current [A]
    I_cc_A = (P_cc_kw * 1000.0) / max(v_pack_nom_v, 1e-6)

    # termination current [A]
    I_term_A = max(i_term_c, 1e-6) * Q_Ah
    k = max(I_term_A / max(I_cc_A, 1e-9), 1e-6)
    
    # split the SOC interval into CC and CV portions
    # CC portion spans [soc_start, min(soc_target, soc_cc_end)]
    soc_cc_stop = min(soc_target, soc_cc_end)
    dSOC_cc = max(0.0, soc_cc_stop - soc_start)
    dSOC_cv = max(0.0, soc_target - max(soc_start, soc_cc_end))

    # CC time (energy-based)
    E_cc_kwh = E_pack_kwh * dSOC_cc
    t_cc_hr = (E_cc_kwh / max(P_cc_kw, 1e-9)) if dSOC_cc > 0 else 0.0

    # CC-CV charging time 
    t_cc_hr = (dSOC_cc * Q_Ah / max(I_cc_A, 1e-9))
    if dSOC_cv <= 0.0 or k >= 1.0:
      t_cv_hr = 0.0
    else:
      t_cv_hr = (dSOC_cv * Q_Ah / max(I_cc_A, 1e-9)) * \
                (math.log(1.0 / k) / (1.0 - k))

    return {
      "t_cc_hr": t_cc_hr,
      "t_cv_hr": t_cv_hr,
      "t_charge_hr": t_cc_hr + t_cv_hr,
      "P_dc_kw": P_dc_kw,
      "P_cc_cap_kw": P_c_rate_cap_kw,
      "P_cc_kw": P_cc_kw,
      "I_cc_A": I_cc_A,
      "I_term_A": I_term_A,
      "k_ratio": k,
      "soc_start": soc_start,
      "soc_target": soc_target,
      "soc_cc_end": soc_cc_end,
      "dSOC_cc": dSOC_cc,
      "dSOC_cv": dSOC_cv,
      "charger_limit_indicator_flag": charger_limit_indicator_flag,
    }