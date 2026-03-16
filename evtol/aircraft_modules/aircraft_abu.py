# aircraft_abu.py
#
# ABU module for aircraft model
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

# ABU Evaluator 1 - Assisted Takeoff
# quantify benefits of ABUs detaching after takeoff 
# ABU is treated as a self-contained unit with the same specifications for all evaluation scenarios
def evaluate_abu_detach_candidates(aircraft, candidates, abu_spec=None):    
    """
    candidates: list of dicts describing detach points.
      Example:
        [
          {"name": "after_accel_climb",
           "segments": ["depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb"]}
        ]
    """

    ## default ABU specifications
    if abu_spec is None:
      abu_spec = {
        "n_abus": 1,                          # number of ABUs attached (default 1)
        "E_mission_kwh_per_abu": 4.0,         # usable ABU energy reserved to assist aircraft [kWh]
        "E_ops_kwh_per_abu": 1.0,             # energy reserved for ABU's own safe ops after detach [kWh]
        "m_struct_kg_per_abu": 20.0,          # ABU structural mass [kg]
        "m_integration_kg_per_abu": 2.0,      # ABU integration hardware mass [kg]
      }

    n_abus = int(abu_spec.get("n_abus", 1))
    E_mission_per_abu_kwh = float(abu_spec.get("E_mission_kwh_per_abu", 0.0))
    E_ops_per_abu_kwh = float(abu_spec.get("E_ops_kwh_per_abu", 0.0))
    m_struct_per_abu_kg = float(abu_spec.get("m_struct_kg_per_abu", 0.0))
    m_integration_per_abu_kg = float(abu_spec.get("m_integration_kg_per_abu", 0.0))

    ## helpers
    # get per-segment energy (kWh)
    def _get_seg_energy_kwh(seg_name):
      try:
        val = getattr(aircraft, f"{seg_name}_energy_kw_hr")
        return 0.0 if val is None else float(val)
      except AttributeError:
        return 0.0

    # convert energy (kWh) to battery mass (kg) 
    def _energy_kwh_to_batt_kg(e_kwh):
      if e_kwh <= 0.0:
        return 0.0
      usable_wh_per_kg = (
        aircraft.power.batt_spec_energy_w_h_p_kg
        * (1.0 - aircraft.power.batt_inaccessible_energy_frac)
        * aircraft.power.batt_int_factor
      )
      if usable_wh_per_kg <= 0.0:
        return 0.0
      return (e_kwh * 1000.0) / usable_wh_per_kg

    # estimate ABU rotor+hub mass using NDARC Section 19.2 AFDD00 rotor + hub mass model
    def _calc_single_lift_rotor_hub_mass_kg():
      """
      Quick patch: temporarily override lift_rotor_count in propulsion
      to reuse existing NDARC rotor+hub mass function.
      """
      # save original getter
      orig_getter = type(aircraft.propulsion).lift_rotor_count.fget

      try:
        # monkey patch to force number of rotors
        type(aircraft.propulsion).lift_rotor_count = property(lambda _self: n_abus)

        # call original mass function
        return aircraft._calc_lift_rotor_hub_mass_kg()

      finally:
        # restore original getter 
        type(aircraft.propulsion).lift_rotor_count = property(orig_getter)

    ## baseline values (no ABU attached)
    baseline_batt_mass_kg = aircraft._calc_battery_mass_kg()
    empty_mass_kg = aircraft._calc_empty_mass_kg()
    if baseline_batt_mass_kg is None or empty_mass_kg is None:
      return [] 

    prev_mtow_kg = aircraft.max_takeoff_mass_kg  # baseline MTOW

    # baseline total mission energy (kWh)
    aircraft._max_takeoff_mass_kg = prev_mtow_kg
    ordered_segments = [
      "depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb",
      "cruise","decel_descend","arrive_proc","trans_descend","hover_descend","arrive_taxi",
      "reserve_hover_climb","reserve_trans_climb","reserve_accel_climb","reserve_cruise",
      "reserve_decel_descend","reserve_trans_descend","reserve_hover_descend"
    ]
    baseline_total_mission_kwh = sum(_get_seg_energy_kwh(s) for s in ordered_segments)

    ## ABU per-unit mass breakdown
    # battery masses
    m_batt_mission_per_abu_kg = _energy_kwh_to_batt_kg(E_mission_per_abu_kwh)
    m_batt_ops_per_abu_kg = _energy_kwh_to_batt_kg(E_ops_per_abu_kwh)

    # rotor mass per ABU 
    rot_hub_single_kg = _calc_single_lift_rotor_hub_mass_kg()
    m_rotor_per_abu_kg = rot_hub_single_kg

    # total ABU mass per unit
    m_abu_total_per_abu_kg = (
      m_struct_per_abu_kg
      + m_integration_per_abu_kg
      + m_rotor_per_abu_kg
      + m_batt_mission_per_abu_kg
      + m_batt_ops_per_abu_kg
    )

    # total ABU fleet mass
    m_abu_total_all_kg = m_abu_total_per_abu_kg * n_abus

    # ABU aggregated energies
    E_abu_mission_total_kwh = E_mission_per_abu_kwh * n_abus
    E_abu_ops_total_kwh = E_ops_per_abu_kwh * n_abus

    ## prepare results list
    results = []

    # iterate candidates
    for cand in candidates:
      name = cand.get("name", "unnamed")
      segs = cand.get("segments", [])

      # ----------------------------
      # Stage A: Pre-detach evaluation with ABU(s) attached
      # ----------------------------
      # MTOW while ABU(s) are attached
      MTOW_attached = aircraft._max_takeoff_mass_kg + m_abu_total_all_kg
      aircraft._max_takeoff_mass_kg = MTOW_attached

      # sequentially step through the candidate's pre-detach segments
      # consume ABU mission energy 
      E_abu_remaining_kwh = E_abu_mission_total_kwh
      pre_detach_log = {}
      aircraft_energy_pre_detach_kwh = 0.0
      E_abu_used_kwh = 0.0

      # for each pre-detach segment
      for s in segs:
        seg_total_kwh = _get_seg_energy_kwh(s)
        # ABU supplies up to remaining mission energy it still has
        # if ABU mission energy exhausted before finishing candidate segments, the logic below already handles it because supplied_by_abu_kwh will be 0
        supplied_by_abu_kwh = min(seg_total_kwh, E_abu_remaining_kwh)
        # aircraft supplies the residual for this segment
        aircraft_kwh = seg_total_kwh - supplied_by_abu_kwh

        # bookkeeping
        E_abu_remaining_kwh -= supplied_by_abu_kwh
        E_abu_used_kwh += supplied_by_abu_kwh
        aircraft_energy_pre_detach_kwh += aircraft_kwh

        pre_detach_log[s] = {
          "seg_total_kwh": seg_total_kwh,
          "abu_kwh": supplied_by_abu_kwh,
          "aircraft_kwh": aircraft_kwh
        }

      # ----------------------------
      # Stage B: Determine new main battery mass and MTOW after detach
      # ----------------------------
      # mass of main battery energy offloaded to ABUs (kg)
      mass_offloaded_kg = _energy_kwh_to_batt_kg(E_abu_used_kwh)
      main_batt_new_kg = max(0.0, baseline_batt_mass_kg - mass_offloaded_kg)

      # MTOW after detaching ABUs
      MTOW_detached = MTOW_attached - baseline_batt_mass_kg - m_abu_total_all_kg + main_batt_new_kg 

      # ----------------------------
      # Stage C: Post-detach evaluation at lighter MTOW (ABUs detached)
      # ----------------------------
      aircraft._max_takeoff_mass_kg = MTOW_detached

      post_detach_log = {}
      # aircraft battery supply post-detach
      remaining_energy_kwh_post = 0.0

      # determine the remaining segments by finding the index of the detach segment and takes everything after it
      if segs:
        last_seg = segs[-1]
        if last_seg in ordered_segments:
          detach_idx = ordered_segments.index(last_seg)
          remaining_segs = ordered_segments[detach_idx + 1 :]
        else:
          remaining_segs = ordered_segments[:]
      else:
        remaining_segs = ordered_segments[:]

      # calculations for each remaining segment
      for rs in remaining_segs:
        seg_kwh = _get_seg_energy_kwh(rs) # evaluated at MTOW_detached
        post_detach_log[rs] = seg_kwh
        remaining_energy_kwh_post += seg_kwh

      # ----------------------------
      # Stage D: Feasibility and totals
      # ----------------------------
      # in this model mission energy and ops energy are separate allocations
      feasible_ops = True
      # infeasible if ABU mission energy supplied exceeded allocated mission reserve 
      if E_abu_used_kwh > E_abu_mission_total_kwh + 1e-12:
        feasible_ops = False

      # total system energy 
      total_system_kwh_after = (
        aircraft_energy_pre_detach_kwh
        + remaining_energy_kwh_post
        + E_abu_used_kwh                 # ABU mission energy actually supplied to aircraft
        + E_abu_ops_total_kwh            # ABU reserved ops energy (spent by ABU after detach)
      )

      # aircraft-only energy consumed after ABU usage (kWh) 
      # the amount of energy the aircraft must supply over the whole mission
      aircraft_total_kwh_after = aircraft_energy_pre_detach_kwh + remaining_energy_kwh_post

      # restore MTOW to baseline 
      aircraft._max_takeoff_mass_kg = prev_mtow_kg

      # ABU mass breakdown details
      abu_mass_breakdown = {
        "n_abus": n_abus,
        "m_struct_total_kg": m_struct_per_abu_kg * n_abus,
        "m_integration_total_kg": m_integration_per_abu_kg * n_abus,
        "m_rotor_total_kg": m_rotor_per_abu_kg * n_abus,
        "m_batt_mission_total_kg": m_batt_mission_per_abu_kg * n_abus,
        "m_batt_ops_total_kg": m_batt_ops_per_abu_kg * n_abus,
        "m_abu_total_per_abu_kg": m_abu_total_per_abu_kg,
        "m_abu_total_all_kg": m_abu_total_all_kg,
      }

      # append results
      results.append({
        "name": name,
        "E_abu_mission_total_kwh": E_abu_mission_total_kwh,
        "E_abu_ops_total_kwh": E_abu_ops_total_kwh,
        "E_abu_used_kwh": E_abu_used_kwh,
        "batt_mass_offloaded_kg": mass_offloaded_kg,
        "baseline_batt_mass_kg": baseline_batt_mass_kg,
        "main_batt_new_kg": main_batt_new_kg,
        "MTOW_attached_kg": MTOW_attached,
        "MTOW_detached_kg": MTOW_detached,
        "pre_detach_segment_log": pre_detach_log,
        "post_detach_segment_log": post_detach_log,
        "abu_mass_breakdown": abu_mass_breakdown,
        "feasible_ops": feasible_ops,
        "baseline_total_mission_kwh": baseline_total_mission_kwh,
        "aircraft_total_kwh_after": aircraft_total_kwh_after,
        "total_system_kwh_after": total_system_kwh_after,
      })

    # return all candidate results
    return results
  
# ABU Evaluator 2.1 - Extended Flight Time with Mid-Flight ABU Attachment (Attached full-segment)
# quantify extended flight endurance when an ABU attaches mid-flight (time/distance powered by ABU)
# ABU adds mass and provides additional energy during the segment. 
# saved baseline battery energy is converted into extra flight time and range.
# structural + integration overheads are modeled per ABU specs.
def _evaluate_extended_flight(aircraft, E_mission_kwh_per_abu_list, abu_spec=None):
    if aircraft.mission == None or aircraft.propulsion == None or aircraft.environ == None or aircraft.power == None:
      return None

    results = []

    # baseline cruise performance (no ABU)
    baseline_mtow_kg = aircraft.max_takeoff_mass_kg
    baseline_cruise_energy_kwh = aircraft._calc_cruise_energy_kw_hr()
    baseline_cruise_power_kw = aircraft._calc_cruise_avg_electric_power_kw()
    cruise_speed_m_p_s = aircraft.mission.cruise_h_m_p_s

    # battery parameters
    spec_energy_Wh_p_kg = aircraft.power.batt_spec_energy_w_h_p_kg
    batt_int_factor = aircraft.power.batt_int_factor
    batt_accessible_energy_frac = 1.0 - aircraft.power.batt_inaccessible_energy_frac

    # default ABU specifications
    if abu_spec is None:
      abu_spec = {
        "n_abus": 1,                     # number of ABUs attached (default 1)
        "E_ops_kwh_per_abu": 1.0,        # energy reserved for ABU's own safe ops [kWh]
        "struct_frac": 0.20,             # structural fraction of battery mass
        "integration_frac": 0.05,        # integration hardware fraction of battery mass
      }

    # estimate ABU rotor+hub mass using NDARC Section 19.2 AFDD00 rotor + hub mass model
    def _calc_single_lift_rotor_hub_mass_kg():
      """
      Quick patch: temporarily override lift_rotor_count in propulsion
      to reuse existing NDARC rotor+hub mass function.
      """
      # save original getter
      orig_getter = type(aircraft.propulsion).lift_rotor_count.fget

      try:
        # monkey patch to force number of rotors
        type(aircraft.propulsion).lift_rotor_count = property(lambda _self: n_abus)

        # call original mass function
        return aircraft._calc_lift_rotor_hub_mass_kg()

      finally:
        # restore original getter 
        type(aircraft.propulsion).lift_rotor_count = property(orig_getter)

    # sweep ABU mission energy levels
    for E_abu_kwh in E_mission_kwh_per_abu_list:

      # ABU energy modeling 
      n_abus = abu_spec["n_abus"]
      E_mission_kwh_per_abu = E_abu_kwh
      E_ops_kwh_per_abu = abu_spec["E_ops_kwh_per_abu"]

      # total ABU energy = mission + self-operations
      E_total_kwh_per_abu = E_mission_kwh_per_abu + E_ops_kwh_per_abu

      # compute ABU battery mass
      m_abu_batt_kg = (E_total_kwh_per_abu * 1000.0) / (
        spec_energy_Wh_p_kg * batt_accessible_energy_frac * batt_int_factor
      )

      # rotor mass per ABU 
      m_rot_hub_kg = _calc_single_lift_rotor_hub_mass_kg()

      # add structural and integration overhead
      m_abu_struct_kg = abu_spec["struct_frac"] * m_abu_batt_kg
      m_abu_integ_kg = abu_spec["integration_frac"] * m_abu_batt_kg

      # total ABU mass (battery + structure + integration + rotor) per unit
      m_abu_total_kg = m_abu_batt_kg + m_abu_struct_kg + m_abu_integ_kg + m_rot_hub_kg
      m_abu_total_all_kg = n_abus * m_abu_total_kg

      # temporarily increase MTOW during ABU-assisted cruise
      aircraft.max_takeoff_mass_kg = baseline_mtow_kg + m_abu_total_all_kg

      # compute cruise energy with ABU-attached configuration
      E_cruise_attach_kwh = aircraft._calc_cruise_energy_kw_hr()

      # ABU provides up to its mission energy capacity
      E_abu_used_kwh = min(E_mission_kwh_per_abu * n_abus, E_cruise_attach_kwh)

      # compute saved baseline battery energy
      E_saved_kwh = baseline_cruise_energy_kwh - (E_cruise_attach_kwh - E_abu_used_kwh)
      if E_saved_kwh < 0.0:
        E_saved_kwh = 0.0

      # compute extended flight time and distance (time/distance powered by ABU)
      extra_time_s = E_saved_kwh / baseline_cruise_power_kw * 3600
      extra_range_mi = extra_time_s * cruise_speed_m_p_s * 0.000621371

      # store result
      results.append({
        "n_abus": n_abus,
        "E_abu_mission_kwh": E_mission_kwh_per_abu,
        "E_abu_total_kwh": E_total_kwh_per_abu,
        "m_abu_batt_kg": m_abu_batt_kg,
        "m_abu_struct_kg": m_abu_struct_kg,
        "m_abu_integ_kg": m_abu_integ_kg,
        "m_rot_hub_kg": m_rot_hub_kg,
        "m_abu_total_all_kg": m_abu_total_all_kg,
        "E_cruise_attach_kwh": E_cruise_attach_kwh,
        "E_abu_used_kwh": E_abu_used_kwh,
        "baseline_cruise_energy_kwh": baseline_cruise_energy_kwh,
        "E_saved_kwh": E_saved_kwh,
        "extra_time_s": extra_time_s,
        "extra_range_mi": extra_range_mi
      })

    # restore original MTOW
    aircraft.max_takeoff_mass_kg = baseline_mtow_kg

    # return results for all ABU cases
    return results

# ABU Evaluator 2.2 - Extended Flight Time with Mid-Flight ABU Attachment (Detach-on-Depletion or End-of-Cruise)
# quantify extended flight endurance when ABU detaches upon depletion (time/distance powered by ABU)
# or at the end of the baseline segment (whichever comes first) 
# splits segment into two phases: attached (ABU supplies power) and post-detach (aircraft only)
# structural + integration overheads are modeled per ABU specs.
def _evaluate_extended_flight_detach_on_depletion_or_end(aircraft, E_mission_kwh_per_abu_list, abu_spec=None):
    if aircraft.mission == None or aircraft.propulsion == None or aircraft.environ == None or aircraft.power == None:
      return None

    results = []

    # baseline cruise performance (no ABU)
    baseline_mtow_kg = aircraft.max_takeoff_mass_kg
    baseline_cruise_energy_kwh = aircraft._calc_cruise_energy_kw_hr()
    baseline_cruise_power_kw = aircraft._calc_cruise_avg_electric_power_kw()
    cruise_speed_m_p_s = aircraft.mission.cruise_h_m_p_s

    # battery parameters
    spec_energy_Wh_p_kg = aircraft.power.batt_spec_energy_w_h_p_kg
    batt_int_factor = aircraft.power.batt_int_factor
    batt_accessible_energy_frac = 1.0 - aircraft.power.batt_inaccessible_energy_frac

    # default ABU specifications
    if abu_spec is None:
      abu_spec = {
        "n_abus": 1,                     # number of ABUs attached (default 1)
        "E_ops_kwh_per_abu": 1.0,        # energy reserved for ABU's own safe ops [kWh]
        "struct_frac": 0.20,             # structural fraction of battery mass
        "integration_frac": 0.05,        # integration hardware fraction of battery mass
      }

    # estimate ABU rotor+hub mass using NDARC Section 19.2 AFDD00 rotor + hub mass model
    def _calc_single_lift_rotor_hub_mass_kg():
      """
      Quick patch: temporarily override lift_rotor_count in propulsion
      to reuse existing NDARC rotor+hub mass function.
      """
      # save original getter
      orig_getter = type(aircraft.propulsion).lift_rotor_count.fget

      try:
        # monkey patch to force number of rotors
        type(aircraft.propulsion).lift_rotor_count = property(lambda _self: n_abus)

        # call original mass function
        return aircraft._calc_lift_rotor_hub_mass_kg()

      finally:
        # restore original getter 
        type(aircraft.propulsion).lift_rotor_count = property(orig_getter)

    # sweep ABU mission energies
    for E_abu_kwh in E_mission_kwh_per_abu_list:

      # ABU energy modeling 
      n_abus = abu_spec["n_abus"]
      E_mission_kwh_per_abu = E_abu_kwh
      E_ops_kwh_per_abu = abu_spec["E_ops_kwh_per_abu"]

      # total ABU energy = mission + self-operations
      E_total_kwh_per_abu = E_mission_kwh_per_abu + E_ops_kwh_per_abu

      # compute ABU battery mass
      m_abu_batt_kg = (E_total_kwh_per_abu * 1000.0) / (
        spec_energy_Wh_p_kg * batt_accessible_energy_frac * batt_int_factor
      )

      # rotor mass per ABU 
      m_rot_hub_kg = _calc_single_lift_rotor_hub_mass_kg()

      # add structural and integration overhead
      m_abu_struct_kg = abu_spec["struct_frac"] * m_abu_batt_kg
      m_abu_integ_kg = abu_spec["integration_frac"] * m_abu_batt_kg

      # total ABU mass (battery + structure + integration + rotor) per unit
      m_abu_total_kg = m_abu_batt_kg + m_abu_struct_kg + m_abu_integ_kg + m_rot_hub_kg
      m_abu_total_all_kg = n_abus * m_abu_total_kg

      # ------------------------------
      # Phase 1: Attached (ABU supplies power)
      # ------------------------------
      aircraft.max_takeoff_mass_kg = baseline_mtow_kg + m_abu_total_all_kg
      P_cruise_attach_kw = aircraft._calc_cruise_avg_electric_power_kw()
      if P_cruise_attach_kw == None:
        continue

      # time until ABU depletion (s)
      t_attached_until_depletion_s = (E_mission_kwh_per_abu * n_abus) / P_cruise_attach_kw * 3600

      # baseline cruise duration (s)
      t_baseline_cruise_s = (baseline_cruise_energy_kwh / baseline_cruise_power_kw) * 3600

      # effective attach duration = shorter of ABU depletion or baseline cruise time
      t_attached_effective_s = min(t_attached_until_depletion_s, t_baseline_cruise_s)

      # ABU energy actually used (limited by baseline cruise duration)
      E_cruise_attach_kwh = P_cruise_attach_kw * (t_attached_effective_s / 3600)
      E_abu_used_kwh = min(E_mission_kwh_per_abu * n_abus, E_cruise_attach_kwh)

      # range covered during attached phase
      range_attached_mi = t_attached_effective_s * cruise_speed_m_p_s * 0.000621371

      # ------------------------------
      # Phase 2: Post-detach (aircraft-only)
      # ------------------------------
      P_cruise_post_kw = baseline_cruise_power_kw  # same aerodynamic config

      # saved baseline energy during attached phase
      E_saved_kwh = min(
        baseline_cruise_power_kw * (t_attached_effective_s / 3600.0),
        baseline_cruise_energy_kwh
      )

      # convert saved energy into additional cruise endurance (lighter MTOW) (time/distance powered by ABU)
      extra_time_s = E_saved_kwh / P_cruise_post_kw * 3600
      extra_range_mi = extra_time_s * cruise_speed_m_p_s * 0.000621371

      # total (attached + extra)
      total_extended_time_s = t_attached_effective_s + extra_time_s
      total_extended_range_mi = range_attached_mi + extra_range_mi

      # flag if ABU still had energy left when cruise ended
      overcapacity_flag = t_attached_until_depletion_s > t_baseline_cruise_s

      # flag if ABU exactly covers baseline cruise (within tolerance)
      full_coverage_flag = abs(E_saved_kwh - baseline_cruise_energy_kwh) < 1e-3

      # store result
      results.append({
        "n_abus": n_abus,
        "E_abu_mission_kwh": E_mission_kwh_per_abu,
        "E_abu_total_kwh": E_total_kwh_per_abu,
        "m_abu_batt_kg": m_abu_batt_kg,
        "m_abu_struct_kg": m_abu_struct_kg,
        "m_abu_integ_kg": m_abu_integ_kg,
        "m_rot_hub_kg": m_rot_hub_kg,
        "m_abu_total_all_kg": m_abu_total_all_kg,
        "P_cruise_attach_kw": P_cruise_attach_kw,
        "P_cruise_post_kw": P_cruise_post_kw,
        "baseline_cruise_energy_kwh": baseline_cruise_energy_kwh,
        "E_cruise_attach_kwh": E_cruise_attach_kwh,
        "E_abu_used_kwh": E_abu_used_kwh,
        "E_saved_kwh": E_saved_kwh,
        "t_attached_until_depletion_s": t_attached_until_depletion_s,
        "t_attached_effective_s": t_attached_effective_s,
        "extra_time_s": extra_time_s,
        "total_extended_time_s": total_extended_time_s,
        "range_attached_mi": range_attached_mi,
        "extra_range_mi": extra_range_mi,
        "total_extended_range_mi": total_extended_range_mi,
        "overcapacity": overcapacity_flag,
        "full_coverage_flag": full_coverage_flag
      })

    # restore MTOW
    aircraft.max_takeoff_mass_kg = baseline_mtow_kg

    return results

# ABU Evaluator 3: Landing Safety with ABU (loiter + divert + descend to alternate)
# quantify how ABUs improve the emergency or low-energy landing situations (safety benefits for landing)
# attaches a fresh ABU at landing phase when main battery is assumed depleted.
# computes the maximum safe loiter time before diverting to an alternate landing site and performing final descent and landing.
#
# Assumptions:
# - ABU stays attached through loiter, divert cruise, hover, and final descent/landing.
# - ABU mission energy is the only usable energy for propulsion.
# - ABU ops reserve must remain unused (safety margin for its own post-touchdown ops).
# - Powers are computed at MTOW + m_ABU while attached.
#
# Inputs:
#   E_mission_kwh_per_abu_list   : list of ABU mission energies to sweep (kWh)
#   divert_distance_mi           : straight-line distance to alternate (miles)
#   t_hover_s                    : required hover/loiter time (seconds)
#   t_hover_descend_s            : approximate hover descent time (seconds)
#   abu_spec                     : ABU parameters
def _evaluate_landing_safety_loiter(aircraft,
                                    E_mission_kwh_per_abu_list,
                                    divert_distance_mi,
                                    t_hover_s,
                                    t_hover_descend_s,
                                    abu_spec=None):
    if aircraft.mission is None or aircraft.propulsion is None or aircraft.environ is None or aircraft.power is None:
      return None

    results = []

    baseline_mtow_kg = aircraft.max_takeoff_mass_kg
    V_cruise_m_p_s   = aircraft.mission.cruise_h_m_p_s

    # battery parameters
    spec_energy_Wh_p_kg = aircraft.power.batt_spec_energy_w_h_p_kg
    batt_int_factor = aircraft.power.batt_int_factor
    batt_accessible_energy_frac = 1.0 - aircraft.power.batt_inaccessible_energy_frac

    # default ABU specifications
    if abu_spec is None:
      abu_spec = {
        "n_abus": 1,                     # number of ABUs attached (default 1)
        "E_ops_kwh_per_abu": 1.0,        # energy reserved for ABU's own safe ops [kWh]
        "struct_frac": 0.20,             # structural fraction of battery mass
        "integration_frac": 0.05,        # integration hardware fraction of battery mass
      }

    # estimate ABU rotor+hub mass using NDARC Section 19.2 AFDD00 rotor + hub mass model
    def _calc_single_lift_rotor_hub_mass_kg():
      """
      Quick patch: temporarily override lift_rotor_count in propulsion
      to reuse existing NDARC rotor+hub mass function.
      """
      # save original getter
      orig_getter = type(aircraft.propulsion).lift_rotor_count.fget

      try:
        # monkey patch to force number of rotors
        type(aircraft.propulsion).lift_rotor_count = property(lambda _self: n_abus)

        # call original mass function
        return aircraft._calc_lift_rotor_hub_mass_kg()

      finally:
        # restore original getter 
        type(aircraft.propulsion).lift_rotor_count = property(orig_getter)

    # sweep ABU mission energies
    for E_mission_kwh_per_abu in E_mission_kwh_per_abu_list:

      # ABU energy modeling 
      n_abus = abu_spec["n_abus"]
      E_ops_kwh_per_abu = abu_spec["E_ops_kwh_per_abu"]

      # total ABU energy = mission + self-operations
      E_total_kwh_per_abu = E_mission_kwh_per_abu + E_ops_kwh_per_abu

      # compute ABU battery mass
      m_abu_batt_kg = (E_total_kwh_per_abu * 1000.0) / (
        spec_energy_Wh_p_kg * batt_accessible_energy_frac * batt_int_factor
      )

      # rotor mass per ABU 
      m_rot_hub_kg = _calc_single_lift_rotor_hub_mass_kg()

      # add structural and integration overhead
      m_abu_struct_kg = abu_spec["struct_frac"] * m_abu_batt_kg
      m_abu_integ_kg = abu_spec["integration_frac"] * m_abu_batt_kg

      # total ABU mass (battery + structure + integration + rotor) per unit
      m_abu_total_per_abu_kg = m_abu_batt_kg + m_abu_struct_kg + m_abu_integ_kg + m_rot_hub_kg
      m_abu_total_all_kg     = n_abus * m_abu_total_per_abu_kg

      # attach ABU to compute attached powers
      try:
        aircraft.max_takeoff_mass_kg = baseline_mtow_kg + m_abu_total_all_kg

        # hover & cruise powers with ABU attached
        P_hover_attach_kw  = aircraft._calc_hover_electric_power_kw()
        P_cruise_attach_kw = aircraft._calc_cruise_avg_electric_power_kw()

        # 1. hover energy
        E_hover_kwh = P_hover_attach_kw * (t_hover_s / 3600.0)

        # 2. divert cruise to alternate 
        t_divert_s = divert_distance_mi * 1609.34 / V_cruise_m_p_s
        E_divert_kwh = P_cruise_attach_kw * (t_divert_s / 3600.0)

        # 3. hover descent (landing) energy
        E_hover_descend_kwh = 0.0

        try:
          # save original property getter
          orig_prop = type(aircraft.mission).hover_descend_s
          orig_getter = getattr(type(aircraft.mission), 'hover_descend_s', None)

          # temporarily override to return custom hover-descent time
          type(aircraft.mission).hover_descend_s = property(lambda _self: t_hover_descend_s)

          # compute energy with patched mission segment
          E_hover_descend_kwh = aircraft._calc_hover_descend_energy_kw_hr()

        finally:
          # Restore the original property definition
          if orig_getter is not None:
            type(aircraft.mission).hover_descend_s = orig_prop

        # 4. ABU ops reserve 
        E_ops_kwh_total = n_abus * E_ops_kwh_per_abu

        # 5. energy available for loiter
        E_abu_mission_total_kwh = n_abus * E_mission_kwh_per_abu
        E_required_after_loiter_kwh = E_hover_kwh + E_divert_kwh + E_hover_descend_kwh + E_ops_kwh_total
        E_available_for_loiter_kwh  = E_abu_mission_total_kwh - E_required_after_loiter_kwh

        # 6. maximum extra safe loiter (hover) time 
        t_loiter_hover_max_s = max(0.0, E_available_for_loiter_kwh / P_hover_attach_kw * 3600.0)

        feasible = (E_available_for_loiter_kwh >= 0.0)
        margin_kwh = E_available_for_loiter_kwh  # negative means shortfall

        results.append({
          "n_abus": n_abus,
          "E_abu_mission_kwh": E_mission_kwh_per_abu,
          "E_abu_total_kwh": E_total_kwh_per_abu,
          "m_abu_batt_kg": m_abu_batt_kg,
          "m_abu_struct_kg": m_abu_struct_kg,
          "m_abu_integ_kg": m_abu_integ_kg,
          "m_rot_hub_kg": m_rot_hub_kg,
          "m_abu_total_all_kg": m_abu_total_all_kg,
          "P_hover_attach_kw": P_hover_attach_kw,
          "P_cruise_attach_kw": P_cruise_attach_kw,
          "t_divert_s": t_divert_s,
          "divert_distance_mi": divert_distance_mi,
          "E_divert_kwh": E_divert_kwh,
          "t_hover_s": t_hover_s,
          "E_hover_kwh": E_hover_kwh,
          "t_hover_descend_s": t_hover_descend_s,
          "E_hover_descend_kwh": E_hover_descend_kwh,
          "E_ops_kwh_total": E_ops_kwh_total,
          "t_loiter_hover_max_s": t_loiter_hover_max_s,
          "feasible": feasible,
          "margin_kwh": margin_kwh,
          "note": "feasible" if feasible else "Insufficient ABU mission energy"
        })

      finally:
        # restore MTOW
        aircraft.max_takeoff_mass_kg = baseline_mtow_kg

    return results

# ABU Evaluator 3 (Baseline): Landing Safety without ABU (designed-in divert energy, incremental from baseline MTOW)
# quantify how much extra main-pack energy is required if the aircraft is designed
# to carry the divert capability itself (no landing ABU), starting from the baseline
# MTOW already specified in the JSON configuration.
#
# This evaluator adds an incremental battery mass on top of the baseline aircraft
# to cover a landing-disruption contingency: loiter/hover + divert cruise + final hover-descent/landing.
# Because extra mass increases power/energy, MTOW is iterated until convergence.
#
# Assumptions:
# - No ABU attachment; all propulsion energy comes from the main aircraft battery.
# - Baseline aircraft (JSON) is already sized for baseline mission; we only add extra battery mass.
# - Contingency energy is computed at (baseline MTOW + added battery mass).
#
# Inputs:
#   divert_distance_mi : straight-line distance to alternate (miles)
#   t_hover_s          : required hover/loiter time (seconds)
#   t_hover_descend_s  : approximate hover-descent time (seconds)
#   tol                : MTOW convergence tolerance (kg)
#   max_iter           : maximum MTOW iterations
def _evaluate_landing_safety_divert_baseline(aircraft,
                                            divert_distance_mi,
                                            t_hover_s,
                                            t_hover_descend_s,
                                            tol=1e-3,
                                            max_iter=100):
    if aircraft.mission is None or aircraft.propulsion is None or aircraft.environ is None or aircraft.power is None:
      return None

    # battery sizing parameters
    spec_energy_Wh_p_kg = aircraft.power.batt_spec_energy_w_h_p_kg
    batt_int_factor = aircraft.power.batt_int_factor
    batt_accessible_energy_frac = 1.0 - aircraft.power.batt_inaccessible_energy_frac

    if spec_energy_Wh_p_kg is None or spec_energy_Wh_p_kg <= 0.0:
      return None
    if batt_int_factor is None or batt_int_factor <= 0.0:
      return None
    if batt_accessible_energy_frac <= 0.0:
      return None

    # original baseline MTOW 
    baseline_mtow_kg = aircraft.max_takeoff_mass_kg

    # helper: compute battery mass directly from an energy requirement
    def _battery_mass_from_energy_kwh(E_total_kwh):
      return (E_total_kwh * 1000.0) / (
        spec_energy_Wh_p_kg * batt_accessible_energy_frac * batt_int_factor
      )

    history = []

    # initial guess: no added battery mass
    mtow_guess = baseline_mtow_kg

    # iterate MTOW increment due to added contingency battery mass
    for i in range(max_iter):
      try:
        aircraft.max_takeoff_mass_kg = mtow_guess

        # baseline mission energy at this (temporary) MTOW
        E_baseline_kwh = aircraft._calc_total_mission_energy_kw_hr()
        if E_baseline_kwh is None:
          return None

        # compute powers at this MTOW
        P_hover_kw = aircraft._calc_hover_electric_power_kw()
        P_cruise_kw = aircraft._calc_cruise_avg_electric_power_kw()
        if P_hover_kw is None or P_cruise_kw is None:
          return None

        V_cruise_m_p_s = aircraft.mission.cruise_h_m_p_s
        if V_cruise_m_p_s is None or V_cruise_m_p_s <= 0.0:
          return None

        # 1) loiter/hover energy
        E_hover_loiter_kwh = P_hover_kw * (t_hover_s / 3600.0)

        # 2) divert cruise energy
        t_divert_s = divert_distance_mi * 1609.34 / V_cruise_m_p_s
        E_divert_kwh = P_cruise_kw * (t_divert_s / 3600.0)

        # 3) hover descent (landing) energy with patched hover_descend_s
        E_hover_descend_kwh = 0.0

        try:
          orig_prop = type(aircraft.mission).hover_descend_s
          orig_getter = getattr(type(aircraft.mission), 'hover_descend_s', None)

          type(aircraft.mission).hover_descend_s = property(lambda _self: t_hover_descend_s)

          E_hover_descend_kwh = aircraft._calc_hover_descend_energy_kw_hr()
          if E_hover_descend_kwh is None:
            return None

        finally:
          if orig_getter is not None:
            type(aircraft.mission).hover_descend_s = orig_prop

        # contingency energy required for landing disruption
        E_divert_required_kwh = E_hover_loiter_kwh + E_divert_kwh + E_hover_descend_kwh

        # 4) incremental battery mass required for the contingency ONLY
        # (do not re-size baseline pack; just add mass on top of baseline aircraft)
        delta_batt_mass_kg = _battery_mass_from_energy_kwh(E_divert_required_kwh)

        # new MTOW = baseline MTOW + incremental contingency battery mass
        new_mtow_kg = baseline_mtow_kg + delta_batt_mass_kg
        delta_kg = new_mtow_kg - mtow_guess

        # total energy required
        E_total_required_kwh = E_baseline_kwh + E_divert_required_kwh

        history.append({
          "iteration": i,
          "mtow_guess_kg": mtow_guess,
          "new_mtow_kg": new_mtow_kg,
          "delta_kg": delta_kg,
          "baseline_mtow_kg": baseline_mtow_kg,
          "E_baseline_kwh": E_baseline_kwh,
          "E_divert_required_kwh": E_divert_required_kwh,
          "E_total_required_kwh": E_total_required_kwh,
          "P_hover_kw": P_hover_kw,
          "P_cruise_kw": P_cruise_kw,
          "t_divert_s": t_divert_s,
          "E_hover_loiter_kwh": E_hover_loiter_kwh,
          "E_divert_cruise_kwh": E_divert_kwh,
          "E_hover_descend_kwh": E_hover_descend_kwh,
          "delta_batt_mass_kg": delta_batt_mass_kg,
        })

        if abs(delta_kg) < tol:
          return {
            "baseline_mtow_kg": baseline_mtow_kg,
            "mtow_converged_kg": new_mtow_kg,
            "delta_battery_mass_converged_kg": delta_batt_mass_kg,
            "baseline_converged_total_mission_kwh": E_baseline_kwh,
            "divert_required_kwh": E_divert_required_kwh,
            "total_required_kwh": E_total_required_kwh,
            "P_hover_kw": P_hover_kw,
            "P_cruise_kw": P_cruise_kw,
            "t_divert_s": t_divert_s,
            "E_hover_loiter_kwh": E_hover_loiter_kwh,
            "E_divert_cruise_kwh": E_divert_kwh,
            "E_hover_descend_kwh": E_hover_descend_kwh,
            "history": history,
          }

        mtow_guess = new_mtow_kg

      finally:
        # keep looping; MTOW restored after loop
        pass

    # if not converged, still return last iterate + history
    aircraft.max_takeoff_mass_kg = baseline_mtow_kg

    if len(history) == 0:
      return None

    last = history[-1]
    return {
      "baseline_mtow_kg": baseline_mtow_kg,
      "mtow_converged_kg": last.get("new_mtow_kg", mtow_guess),
      "delta_battery_mass_converged_kg": last.get("delta_batt_mass_kg", 0.0),
      "baseline_converged_total_mission_kwh": last.get("E_baseline_kwh", 0.0),
      "total_required_kwh": last.get("E_total_required_kwh", 0.0),
      "divert_required_kwh": last.get("E_divert_required_kwh", 0.0),
      "P_hover_kw": last.get("P_hover_kw", 0.0),
      "P_cruise_kw": last.get("P_cruise_kw", 0.0),
      "t_divert_s": last.get("t_divert_s", 0.0),
      "E_hover_loiter_kwh": last.get("E_hover_loiter_kwh", 0.0),
      "E_divert_cruise_kwh": last.get("E_divert_kwh", 0.0),
      "E_hover_descend_kwh": last.get("E_hover_descend_kwh", 0.0),
      "history": history,
      "note": "did not converge within max_iter; returning last iterate"
    }

# ABU Evaluator 4.1: Common Case Economics (Baseline, no ABU)
# estimates daily utilization (flights/day, flight hours/day)
# for a baseline eVTOL that must recharge its main pack between flights using the analytical CC-CV charging model
#
# Inputs:
#   E_pack_kwh          : main battery pack energy capacity [kWh]
#   P_charger_ac_kw     : charger AC power [kW]
#   eta_charger_dc      : AC->DC efficiency (0–1)
#   c_rate_max          : max allowed charge C-rate (e.g., 1.0)
#   v_pack_nom_v        : nominal pack voltage [V]
#   i_term_c            : CV termination current ratio (e.g., 0.05C)
#   soc_target          : target SOC after charge (default 1.0)
#   soc_cc_end          : SOC where CC ends (default 0.80)
#   t_ground_ops_hr     : turnaround ops [hr]
#   daily_operation_hr  : daily operation window [hr]
#   mission_time_s      : optional mission duration [s]; if None, sum segments
def _evaluate_common_case_baseline(aircraft,
                                    E_pack_kwh=None,
                                    P_charger_ac_kw=115.0,
                                    eta_charger_dc=0.95,
                                    c_rate_max=1.0,
                                    v_pack_nom_v=800.0,
                                    i_term_c=0.05,
                                    soc_start=None,
                                    soc_target=1.0,
                                    soc_cc_end=0.80,
                                    t_ground_ops_hr=0.2833,
                                    daily_operation_hr=24.0,
                                    mission_time_s=None):

    # 1. Per-mission energy (from aircraft model)
    E_mission_kwh = aircraft._calc_total_mission_energy_kw_hr()
    if E_mission_kwh is None:
      return None

    # 2. Determine pack size 
    if E_pack_kwh is None:
      E_pack_kwh = E_mission_kwh  # simple baseline

    # 3. Compute mission flight time if not given (sum segment times)
    if mission_time_s is None:
      # # Main mission & Reserve mission
      # seg_time_names = [
      #   "depart_taxi_s","hover_climb_s","trans_climb_s","depart_proc_s","accel_climb_s",
      #   "cruise_s","decel_descend_s","arrive_proc_s","trans_descend_s","hover_descend_s","arrive_taxi_s",
      #   "reserve_hover_climb_s","reserve_trans_climb_s","reserve_accel_climb_s","reserve_cruise_s",
      #   "reserve_decel_descend_s","reserve_trans_descend_s","reserve_hover_descend_s",
      # ]

      # Main mission only
      seg_time_names = [
        "depart_taxi_s","hover_climb_s","trans_climb_s","depart_proc_s","accel_climb_s",
        "cruise_s","decel_descend_s","arrive_proc_s","trans_descend_s","hover_descend_s","arrive_taxi_s",
      ]

      mission_time_s = 0.0
      if getattr(aircraft, "mission", None) is not None:
        for nm in seg_time_names:
          mission_time_s += float(getattr(aircraft.mission, nm, 0.0) or 0.0)

    t_flight_hr = (mission_time_s or 0.0) / 3600.0

    # 4. Infer DoD of the mission relative to the pack
    if soc_start is None:
      dod = min(1.0, max(0.0, E_mission_kwh / max(E_pack_kwh, 1e-9)))
      soc_start = max(0.0, soc_target - dod)
    else:
      # if SOC_start provided, derive corresponding DoD for reference
      dod = soc_target - soc_start
      dod = min(1.0, max(0.0, dod))

    # 5. Detailed CC–CV charge time
    chg = aircraft._estimate_cccv_charge_time_hr(
      E_pack_kwh=E_pack_kwh,
      P_charger_ac_kw=P_charger_ac_kw,
      eta_charger_dc=eta_charger_dc,
      c_rate_max=c_rate_max,
      v_pack_nom_v=v_pack_nom_v,
      i_term_c=i_term_c,
      soc_start=soc_start,
      soc_target=soc_target,
      soc_cc_end=soc_cc_end
    )
    if chg is None:
      return None

    t_charge_hr = chg["t_charge_hr"]
    t_cc_hr = chg.get("t_cc_hr", 0.0)
    t_cv_hr = chg.get("t_cv_hr", 0.0)

    # 6. Per-mission cycle time and daily throughput
    t_cycle_hr = t_flight_hr + t_charge_hr + t_ground_ops_hr
    if t_cycle_hr <= 0.0:
      return None

    n_feasible = int(daily_operation_hr // t_cycle_hr)
    t_used_hr  = n_feasible * t_cycle_hr
    t_slack_hr = max(0.0, daily_operation_hr - t_used_hr)

    t_flight_day_hr   = n_feasible * t_flight_hr
    t_downtime_day_hr = n_feasible * (t_charge_hr + t_ground_ops_hr) + t_slack_hr

    return {
      "daily_operation_hr": daily_operation_hr,
      "E_mission_kwh": E_mission_kwh,
      "E_pack_kwh": E_pack_kwh,
      "dod": dod,
      "soc_start": soc_start,
      "soc_target": soc_target,
      "soc_cc_end": soc_cc_end,
      "t_flight_hr": t_flight_hr,
      "t_charge_hr": t_charge_hr,
      "t_cc_hr": t_cc_hr,
      "t_cv_hr": t_cv_hr,
      "t_ground_ops_hr": t_ground_ops_hr,
      "t_cycle_hr": t_cycle_hr,
      "n_feasible_flights": n_feasible,
      "t_flight_day_hr": t_flight_day_hr,
      "t_downtime_day_hr": t_downtime_day_hr,
      "t_slack_hr": t_slack_hr,
      "charger_ac_kw": P_charger_ac_kw,
      "eta_charger_dc": eta_charger_dc,
      "c_rate_max": c_rate_max,
      "v_pack_nom_v": v_pack_nom_v,
      "i_term_c": i_term_c,
      "P_dc_kw": chg.get("P_dc_kw", 0.0),
      "P_cc_cap_kw": chg.get("P_cc_cap_kw", 0.0),
      "P_cc_kw": chg.get("P_cc_kw", 0.0),
      "I_cc_A": chg.get("I_cc_A", 0.0),
      "I_term_A": chg.get("I_term_A", 0.0),
      "charger_limit_indicator_flag": chg.get("charger_limit_indicator_flag"),
    }

# ABU Evaluator 4.1-TL: Common Case Economics (Baseline, no ABU)
# Same as baseline evaluator, but includes full operating timeline logging
#
# Logs:
#   • aircraft_depart
#   • aircraft_arrive
#   • aircraft_ground_ops_start
#   • aircraft_ground_ops_done
#   • aircraft_charge_start
#   • aircraft_charge_done
#
# Returns:
#   baseline summary metrics + timeline event list
#
def _evaluate_common_case_baseline_timeline(aircraft,
                                            E_pack_kwh=None,
                                            P_charger_ac_kw=115.0,
                                            eta_charger_dc=0.95,
                                            c_rate_max=1.0,
                                            v_pack_nom_v=800.0,
                                            i_term_c=0.05,
                                            soc_start=None,
                                            soc_target=1.0,
                                            soc_cc_end=0.80,
                                            t_ground_ops_hr=0.2833,
                                            daily_operation_hr=24.0,
                                            mission_time_s=None):

    # 1. Mission energy
    E_mission_kwh = aircraft._calc_total_mission_energy_kw_hr()
    if E_mission_kwh is None:
      return None

    # 2. Pack size 
    if E_pack_kwh is None:
      E_pack_kwh = E_mission_kwh  # baseline: pack sized to mission

    # 3. Flight time 
    if mission_time_s is None:
      seg_time_names = [
        "depart_taxi_s","hover_climb_s","trans_climb_s","depart_proc_s","accel_climb_s",
        "cruise_s","decel_descend_s","arrive_proc_s","trans_descend_s","hover_descend_s","arrive_taxi_s",
      ]
      mission_time_s = 0.0
      if getattr(aircraft, "mission", None) is not None:
        for nm in seg_time_names:
          mission_time_s += float(getattr(aircraft.mission, nm, 0.0) or 0.0)

    t_flight_hr = (mission_time_s or 0.0) / 3600.0

    # 4. Infer DoD, initial SOC 
    if soc_start is None:
      dod = min(1.0, max(0.0, E_mission_kwh / max(E_pack_kwh, 1e-9)))
      soc_start = max(0.0, soc_target - dod)
    else:
      dod = soc_target - soc_start
      dod = min(1.0, max(0.0, dod))

    # 5. Charge time model
    chg = aircraft._estimate_cccv_charge_time_hr(
      E_pack_kwh=E_pack_kwh,
      P_charger_ac_kw=P_charger_ac_kw,
      eta_charger_dc=eta_charger_dc,
      c_rate_max=c_rate_max,
      v_pack_nom_v=v_pack_nom_v,
      i_term_c=i_term_c,
      soc_start=soc_start,
      soc_target=soc_target,
      soc_cc_end=soc_cc_end
    )
    if chg is None:
      return None

    t_charge_hr = chg["t_charge_hr"]
    t_cc_hr = chg.get("t_cc_hr", 0.0)
    t_cv_hr = chg.get("t_cv_hr", 0.0)

    # 6. Cycle time
    t_cycle_hr = t_flight_hr + t_charge_hr + t_ground_ops_hr
    if t_cycle_hr <= 0.0:
      return None

    # Timeline Simulation
    timeline = []          # list of {t_hr, event, flight_index}
    t_now_hr = 0.0         # current aircraft availability time
    flight_index = 0

    while True:

      # If starting a new flight exceeds operation window → stop
      if t_now_hr + t_flight_hr > daily_operation_hr:
        break

      # --- departure ---
      timeline.append({
        "t_hr": t_now_hr,
        "event": "aircraft_depart",
        "flight_index": flight_index
      })

      # --- arrival ---
      t_arrive = t_now_hr + t_flight_hr
      timeline.append({
        "t_hr": t_arrive,
        "event": "aircraft_arrive",
        "flight_index": flight_index
      })

      # --- ground ops ---
      timeline.append({
        "t_hr": t_arrive,
        "event": "aircraft_ground_ops_start",
        "flight_index": flight_index
      })

      t_after_ground = t_arrive + t_ground_ops_hr
      timeline.append({
        "t_hr": t_after_ground,
        "event": "aircraft_ground_ops_done",
        "flight_index": flight_index
      })

      # --- charging ---
      timeline.append({
        "t_hr": t_after_ground,
        "event": "aircraft_charge_start",
        "flight_index": flight_index
      })

      t_after_charge = t_after_ground + t_charge_hr
      timeline.append({
        "t_hr": t_after_charge,
        "event": "aircraft_charge_done",
        "flight_index": flight_index
      })

      # update availability
      t_now_hr = t_after_charge
      flight_index += 1

      if t_now_hr > daily_operation_hr:
        break

    # number of completed flights
    n_flights_completed = flight_index

    # slack
    t_total_used_hr = min(daily_operation_hr, t_now_hr)
    t_slack_hr = max(0.0, daily_operation_hr - t_total_used_hr)

    t_flight_day_hr = n_flights_completed * t_flight_hr
    t_downtime_day_hr = n_flights_completed * (t_charge_hr + t_ground_ops_hr) + t_slack_hr

    # results
    return {
      "daily_operation_hr": daily_operation_hr,
      "E_mission_kwh": E_mission_kwh,
      "E_pack_kwh": E_pack_kwh,
      "dod": dod,
      "soc_start": soc_start,
      "soc_target": soc_target,
      "soc_cc_end": soc_cc_end,

      "t_flight_hr": t_flight_hr,
      "t_charge_hr": t_charge_hr,
      "t_cc_hr": t_cc_hr,
      "t_cv_hr": t_cv_hr,
      "t_ground_ops_hr": t_ground_ops_hr,
      "t_cycle_hr": t_cycle_hr,

      "n_flights_completed": n_flights_completed,
      "t_flight_day_hr": t_flight_day_hr,
      "t_downtime_day_hr": t_downtime_day_hr,
      "t_slack_hr": t_slack_hr,

      "charger_ac_kw": P_charger_ac_kw,
      "eta_charger_dc": eta_charger_dc,
      "c_rate_max": c_rate_max,
      "v_pack_nom_v": v_pack_nom_v,
      "i_term_c": i_term_c,

      "P_dc_kw": chg.get("P_dc_kw", 0.0),
      "P_cc_cap_kw": chg.get("P_cc_cap_kw", 0.0),
      "P_cc_kw": chg.get("P_cc_kw", 0.0),
      "I_cc_A": chg.get("I_cc_A", 0.0),
      "I_term_A": chg.get("I_term_A", 0.0),
      "charger_limit_indicator_flag": chg.get("charger_limit_indicator_flag"),

      "aircraft_timeline": timeline,
    }

# ABU Evaluator 4.2: Common Case Economics (ABU, Assisted Takeoff, Overlap Charging, Daily Utilization, ABU Queuing)
#
# A finite pool of takeoff ABUs
#   takeoff attach → detach → ABU returns → ABU recharges
#   main battery charges in parallel with ABU

# Inputs:
#   candidates                     : list of ABU assisted-takeoff detach cases 
#   abu_spec                       : ABU spec used for assisted takeoff 
#   n_abu_pool                     : size of takeoff-ABU pool at each LZ
#   P_charger_ac_kw                : charger AC power [kW] (assumed same for main + ABUs)
#   eta_charger_dc                 : charger AC->DC efficiency (0–1)
#   c_rate_max                     : max allowed charge C-rate (e.g., 1.0)
#   v_pack_nom_v_main              : nominal voltage of eVTOL main pack [V]
#   v_pack_nom_v_abu               : nominal voltage of ABU packs [V] 
#   i_term_c                       : CV termination current ratio (e.g., 0.05C)
#   soc_target                     : target SOC after charge (default 1.0)
#   soc_cc_end                     : SOC where CC ends (default 0.80)
#   t_ground_ops_hr                : ground turnaround ops [hr]
#   V_abu_horizontal_m_p_s         : takeoff-ABU horizontal speed on return [m/s]
#   V_abu_vertical_m_p_s           : takeoff-ABU vertical descent speed on return [m/s]
#   h_detach_takeoff_ft            : takeoff-ABU detach altitude [ft]
#   daily_operation_hr             : daily operation window [hr]
#   mission_time_s                 : optional mission duration [s]; if None, sum main-mission segments
def _evaluate_common_case_abu_assisted_takeoff_overlap_charging_queuing(aircraft,
                                                                        candidates,
                                                                        abu_spec=None,
                                                                        n_abu_pool=1,
                                                                        P_charger_ac_kw=115.0,
                                                                        eta_charger_dc=0.95,
                                                                        c_rate_max=1.0,
                                                                        v_pack_nom_v_main=800.0,
                                                                        v_pack_nom_v_abu=400.0,
                                                                        i_term_c=0.05,
                                                                        soc_target=1.0,
                                                                        soc_cc_end=0.80,
                                                                        t_ground_ops_hr=0.2833,
                                                                        V_abu_horizontal_m_p_s=30.0,
                                                                        V_abu_vertical_m_p_s=5.1,
                                                                        h_detach_ft=3000.0,
                                                                        daily_operation_hr = 24.0,
                                                                        mission_time_s=None):

    if aircraft.mission is None or aircraft.propulsion is None or aircraft.environ is None or aircraft.power is None:
      return None

    results = []

    # default ABU specification 
    if abu_spec is None:
      abu_spec = {
        "n_abus": 1,
        "E_mission_kwh_per_abu": 15.0,
        "E_ops_kwh_per_abu": 6.0,
        "m_struct_kg_per_abu": 50.0,
        "m_integration_kg_per_abu": 10.0,
      }

    # run assisted takeoff evaluator to get post-detach energy, ABU usage
    detach_results = aircraft.evaluate_abu_detach_candidates(candidates, abu_spec)
    if not detach_results:
      return None

    # pre-cruise timing (ABU stays attached for entire pre-cruise) 
    m = aircraft.mission
    depart_taxi_s   = float(m.depart_taxi_s or 0.0)
    hover_climb_s   = float(m.hover_climb_s or 0.0)
    trans_climb_s   = float(m.trans_climb_s or 0.0)
    depart_proc_s   = float(m.depart_proc_s or 0.0)
    accel_climb_s   = float(m.accel_climb_s or 0.0)

    t_attach_s = depart_taxi_s + hover_climb_s + trans_climb_s + depart_proc_s + accel_climb_s
    t_attach_hr = t_attach_s / 3600.0

    # horizontal distance to detach point (for ABU return) 
    d_precruise_m = \
      float(m.depart_taxi_avg_h_m_p_s or 0.0) * depart_taxi_s + \
      float(m.trans_climb_avg_h_m_p_s or 0.0) * trans_climb_s + \
      float(m.depart_proc_h_m_p_s      or 0.0) * depart_proc_s + \
      float(m.accel_climb_avg_h_m_p_s  or 0.0) * accel_climb_s

    # Vertical drop (detach altitude) 
    h_detach_m = max(0.0, h_detach_ft * 0.3048)

    # ABU return time
    t_horizontal_abu_s = d_precruise_m / max(V_abu_horizontal_m_p_s, 1e-9)
    t_vertical_abu_s   = h_detach_m / max(V_abu_vertical_m_p_s, 1e-9)
    t_return_abu_hr    = (t_horizontal_abu_s + t_vertical_abu_s) / 3600.0

    # main mission (post-detach) time
    if mission_time_s is None:
      # Sum post-detach segments from candidate log
      seg_log = detach_results[0].get("post_detach_segment_log", {})
      mission_time_s_eff = sum(float(getattr(m, f"{k}_s", 0.0) or 0.0) for k in seg_log.keys())
    else:
      mission_time_s_eff = float(mission_time_s or 0.0)

    t_flight_hr = mission_time_s_eff / 3600.0

    # helper simulation: N-hour operations with finite ABU pool 
    def _simulate_daily_ops_abu_pool(n_abu_pool_local,
                                     t_flight_hr_local,
                                     t_charge_hr_main_local,
                                     t_attach_hr_local,
                                     t_return_abu_hr_local,
                                     t_charge_hr_abu_local,
                                     t_ground_ops_hr_local):

      t_aircraft_ready_hr = 0.0

      # ABU pool availability
      n_pool = max(1, n_abu_pool_local)
      abu_available_times = [0.0 for _ in range(n_pool)]
      abu_busy_time       = [0.0 for _ in range(n_pool)]

      # timeline logs
      aircraft_timeline = []
      abu_timelines     = {j: [] for j in range(n_pool)}

      n_flights_completed = 0
      t_wait_abu_day_hr   = 0.0

      # simulation loop 
      while True:

        t_earliest = t_aircraft_ready_hr
        ready_abus = [j for j in range(n_pool) if abu_available_times[j] <= t_earliest]

        if len(ready_abus) > 0:
          j_min = min(ready_abus)
          t_min = abu_available_times[j_min]
        else:
          j_min = min(range(n_pool), key=lambda j: abu_available_times[j])
          t_min = abu_available_times[j_min]

        t_block = t_min
        t_depart = max(t_earliest, t_block)

        # check if flight fits before N (hours) of daily operation
        if t_depart + t_flight_hr_local > daily_operation_hr:
          break

        # waiting time due to ABU bottleneck
        if t_block > t_aircraft_ready_hr:
          t_wait_abu_day_hr += (t_block - t_aircraft_ready_hr)

        flight_idx = n_flights_completed

        # -------------------------------------------------
        # aircraft timeline events
        # -------------------------------------------------
        aircraft_timeline.append({
          "t_hr": t_depart,
          "event": "aircraft_depart",
          "flight_index": flight_idx
        })

        t_arrive = t_depart + t_flight_hr_local
        aircraft_timeline.append({
          "t_hr": t_arrive,
          "event": "aircraft_arrive",
          "flight_index": flight_idx
        })

        t_after_ground = t_arrive + t_ground_ops_hr_local
        aircraft_timeline.append({
          "t_hr": t_after_ground,
          "event": "aircraft_ground_ops_done",
          "flight_index": flight_idx
        })

        t_after_main_charge = t_after_ground + t_charge_hr_main_local
        aircraft_timeline.append({
          "t_hr": t_after_main_charge,
          "event": "aircraft_charge_done",
          "flight_index": flight_idx
        })

        t_aircraft_ready_hr = t_after_main_charge

        # -------------------------------------------------
        # ABU timeline events
        # -------------------------------------------------
        # attach
        t_attach_start = t_depart
        abu_timelines[j_min].append({
          "t_hr": t_attach_start,
          "event": "abu_attach",
          "flight_index": flight_idx,
          "abu_index": j_min
        })

        # detach
        t_detach = t_attach_start + t_attach_hr_local
        abu_timelines[j_min].append({
          "t_hr": t_detach,
          "event": "abu_detach",
          "flight_index": flight_idx,
          "abu_index": j_min
        })

        # return complete
        t_return_done = t_detach + t_return_abu_hr_local
        abu_timelines[j_min].append({
          "t_hr": t_return_done,
          "event": "abu_return_done",
          "flight_index": flight_idx,
          "abu_index": j_min
        })

        # charge start
        t_charge_start = t_return_done
        abu_timelines[j_min].append({
          "t_hr": t_charge_start,
          "event": "abu_charge_start",
          "flight_index": flight_idx,
          "abu_index": j_min
        })

        # charge complete
        t_charge_done = t_charge_start + t_charge_hr_abu_local
        abu_timelines[j_min].append({
          "t_hr": t_charge_done,
          "event": "abu_charge_done",
          "flight_index": flight_idx,
          "abu_index": j_min
        })

        # update ABU availability state
        abu_available_times[j_min] = t_charge_done
        abu_busy_time[j_min]      += (t_charge_done - t_depart)

        n_flights_completed += 1

      # end simulation day 
      t_flight_day_hr = n_flights_completed * t_flight_hr_local
      t_used_hr       = min(daily_operation_hr, t_aircraft_ready_hr)
      t_slack_hr      = max(0.0, daily_operation_hr - t_used_hr)

      total_busy      = sum(abu_busy_time)
      abu_util_avg    = total_busy / (daily_operation_hr * n_pool)

      return {
        "n_flights_completed": n_flights_completed,
        "t_flight_day_hr": t_flight_day_hr,
        "t_slack_hr": t_slack_hr,
        "t_wait_abu_day_hr": t_wait_abu_day_hr,
        "abu_utilization_avg": abu_util_avg,
        "aircraft_timeline": aircraft_timeline,
        "abu_timelines": abu_timelines,
      }

    # main loop for each candidate
    for cand in detach_results:
      name = cand.get("name", "unknown")

      # post-detach main energy
      E_pack_kwh_main = float(cand.get("aircraft_total_kwh_after", 0.0))

      # ABU usage
      n_abus = int(abu_spec.get("n_abus", 1))
      E_mission_per_abu = float(abu_spec.get("E_mission_kwh_per_abu", 0.0))
      E_ops_per_abu     = float(abu_spec.get("E_ops_kwh_per_abu", 0.0))
      E_pack_kwh_abu    = E_mission_per_abu + E_ops_per_abu

      E_used_total = float(cand.get("E_abu_used_kwh", 0.0))
      E_used_per_abu = E_used_total / max(n_abus, 1)

      # SOC
      E_reserve_kwh = float(aircraft._calc_total_reserve_mission_energy_kw_hr() or 0.0)
      soc_start_main = max(0.0, E_reserve_kwh / max(E_pack_kwh_main, 1e-9))
      soc_start_main = min(1.0, soc_start_main)

      recharge_per_abu_kwh = E_used_per_abu + E_ops_per_abu
      dod_abu = recharge_per_abu_kwh / max(E_pack_kwh_abu, 1e-9)
      dod_abu = max(0.0, min(1.0, dod_abu))
      soc_start_abu = max(0.0, soc_target - dod_abu)

      dod_main = soc_target - soc_start_main

      # charging
      chg_main = aircraft._estimate_cccv_charge_time_hr(
        E_pack_kwh=E_pack_kwh_main,
        P_charger_ac_kw=P_charger_ac_kw,
        eta_charger_dc=eta_charger_dc,
        c_rate_max=c_rate_max,
        v_pack_nom_v=v_pack_nom_v_main,
        i_term_c=i_term_c,
        soc_start=soc_start_main,
        soc_target=soc_target,
        soc_cc_end=soc_cc_end
      )

      chg_abu = aircraft._estimate_cccv_charge_time_hr(
        E_pack_kwh=E_pack_kwh_abu,
        P_charger_ac_kw=P_charger_ac_kw,
        eta_charger_dc=eta_charger_dc,
        c_rate_max=c_rate_max,
        v_pack_nom_v=v_pack_nom_v_abu,
        i_term_c=i_term_c,
        soc_start=soc_start_abu,
        soc_target=soc_target,
        soc_cc_end=soc_cc_end
      )

      if chg_main is None or chg_abu is None:
        continue

      t_charge_main = float(chg_main.get("t_charge_hr", 0.0))
      t_charge_abu  = float(chg_abu.get("t_charge_hr", 0.0))

      # parallel charging → use slower one
      t_charge_total = max(t_charge_main, t_charge_abu)

      # nominal cycle (infinite ABUs)
      t_cycle_nominal_hr = t_flight_hr + t_charge_main + t_ground_ops_hr
      n_nominal = int(daily_operation_hr // t_cycle_nominal_hr)

      # finite ABU pool simulation
      sim = _simulate_daily_ops_abu_pool(
        n_abu_pool_local      = n_abu_pool,
        t_flight_hr_local     = t_flight_hr,
        t_charge_hr_main_local= t_charge_main,
        t_attach_hr_local     = t_attach_hr,
        t_return_abu_hr_local = t_return_abu_hr,
        t_charge_hr_abu_local = t_charge_abu,
        t_ground_ops_hr_local = t_ground_ops_hr
      )

      results.append({
        "daily_operation_hr": daily_operation_hr,

        "candidate_name": name,
        "n_abu_pool": n_abu_pool,
        "n_abus_per_flight": n_abus,

        # packs
        "E_pack_kwh_main": E_pack_kwh_main,
        "E_pack_kwh_abu": E_pack_kwh_abu,
        "dod_main": dod_main,
        "dod_abu": dod_abu,
        "soc_start_main": soc_start_main,
        "soc_start_abu": soc_start_abu,
        "soc_target": soc_target,

        # times
        "t_flight_hr": t_flight_hr,
        "t_takeoff_attach_hr": t_attach_hr,
        "t_return_abu_hr": t_return_abu_hr,
        "t_charge_hr_main": t_charge_main,
        "t_charge_hr_abu": t_charge_abu,
        "t_cycle_nominal_hr": t_cycle_nominal_hr,
        "n_flights_nominal_no_abu_limit": n_nominal,

        # N-hour simulation
        "n_flights_completed": sim["n_flights_completed"],
        "t_flight_day_hr": sim["t_flight_day_hr"],
        "t_slack_hr": sim["t_slack_hr"],
        "t_wait_abu_day_hr": sim["t_wait_abu_day_hr"],
        "abu_utilization_avg": sim["abu_utilization_avg"],

        # full timelines
        "aircraft_timeline": sim["aircraft_timeline"],
        "abu_timelines": sim["abu_timelines"],
      })

    return results

# ABU Evaluator 4.3: Common Case Economics (ABU, Extended Flight Powered by ABU, Overlap Charging, Daily Utilization with Queuing)
#
# estimates daily utilization (flights/day, flight hours/day) for a single eVTOL
# when ABUs are used to extend cruise, detach after completing their purposes, then return to the landing zone
# and begin recharging while the eVTOL continues its flight.
#
# A finite pool of ABUs at the landing zone is modeled. The eVTOL can only depart
# when BOTH:
#   (a) its main battery is recharged, and
#   (b) at least one ABU at the landing zone is fully charged and available.
#
# If no ABUs are ready when the aircraft is ready, departure is delayed (ABU bottleneck).
#
# Inputs:
#   E_mission_kwh_per_abu_list : list of ABU mission energy values [kWh per ABU]
#   abu_spec                   : ABU specifications
#   n_abu_pool                 : total number of ABUs available at the landing zone
#   P_charger_ac_kw            : charger AC power [kW] (for both eVTOL and ABU)
#   eta_charger_dc             : AC->DC efficiency (0–1)
#   c_rate_max                 : max allowed charge C-rate (e.g., 1.0)
#   v_pack_nom_v_main          : nominal voltage of eVTOL main pack [V]
#   v_pack_nom_v_abu           : nominal voltage of ABU pack [V]
#   i_term_c                   : CV termination current (fraction of C)
#   soc_target                 : target SOC after charging (default 1.0)
#   soc_cc_end                 : SOC where CC ends (default 0.80)
#   t_ground_ops_hr            : ground turnaround ops [hr] per flight
#   V_abu_horizontal_m_p_s     : ABU horizontal speed during return [m/s]
#   V_abu_vertical_m_p_s       : ABU vertical descent speed during return [m/s]
#   h_detach_ft                : ABU detach altitude above landing zone [ft]
#   daily_operation_hr         : daily operation window [hr]
#   mission_time_s             : optional mission duration override [s]; if None, sum segments
def _evaluate_common_case_abu_extended_flight_overlap_charging_queuing(aircraft,
                                                                        E_mission_kwh_per_abu_list,
                                                                        abu_spec=None,
                                                                        n_abu_pool=3,
                                                                        P_charger_ac_kw=115.0,
                                                                        eta_charger_dc=0.95,
                                                                        c_rate_max=1.0,
                                                                        v_pack_nom_v_main=800.0,
                                                                        v_pack_nom_v_abu=400.0,
                                                                        i_term_c=0.05,
                                                                        soc_target=1.0,
                                                                        soc_cc_end=0.80,
                                                                        t_ground_ops_hr=0.2833,
                                                                        V_abu_horizontal_m_p_s=30.0,
                                                                        V_abu_vertical_m_p_s=5.1,
                                                                        h_detach_ft=3000.0,
                                                                        daily_operation_hr = 24.0,
                                                                        mission_time_s=None):

    if aircraft.mission is None or aircraft.propulsion is None or aircraft.environ is None or aircraft.power is None:
      return None

    results = []

    # default ABU specifications if not provided
    if abu_spec is None:
      abu_spec = {
        "n_abus": 1,
        "E_ops_kwh_per_abu": 1.0,
        "struct_frac": 0.20,
        "integration_frac": 0.05,
      }

    # run underlying endurance analysis (Evaluator 2.2, baseline cruise at baseline MTOW)
    ext_results = aircraft._evaluate_extended_flight_detach_on_depletion_or_end(
      E_mission_kwh_per_abu_list,
      abu_spec=abu_spec
    )
    if ext_results is None or len(ext_results) == 0:
      return None

    # compute mission time (full main mission) if not provided
    if mission_time_s is None:
      seg_time_names = [
        "depart_taxi_s","hover_climb_s","trans_climb_s","depart_proc_s","accel_climb_s",
        "cruise_s","decel_descend_s","arrive_proc_s","trans_descend_s","hover_descend_s","arrive_taxi_s",
      ]
      mission_time_s = 0.0
      if getattr(aircraft, "mission", None) is not None:
        for nm in seg_time_names:
          mission_time_s += float(getattr(aircraft.mission, nm, 0.0) or 0.0)

    t_flight_hr = (mission_time_s or 0.0) / 3600.0

    # helper: simulate N-hr operations for a single eVTOL and finite ABU pool at the landing zone
    def _simulate_daily_ops_single_evtol(n_abu_pool_local,
                                         t_flight_hr_local,
                                         t_charge_hr_main_local,
                                         t_attach_hr_local,
                                         t_return_abu_hr_local,
                                         t_charge_hr_abu_local,
                                         t_ground_ops_hr_local):
      
      # initialize aircraft and ABUs
      t_aircraft_ready_hr = 0.0  # time when aircraft is ready to depart (main charged + ground ops done); initially 0 = ready at start of day
      abu_available_times_hr = [0.0 for _ in range(max(1, n_abu_pool_local))] # time when ABU j will next be ready (fully charged)
      abu_busy_time_hr = [0.0 for _ in range(max(1, n_abu_pool_local))] # how much of the N-hours ABU j was actively busy (for utilization calculation)

      # new: timeline logs
      aircraft_timeline = []
      abu_timelines = {j: [] for j in range(max(1, n_abu_pool_local))}

      n_flights_completed = 0
      t_wait_abu_day_hr = 0.0

      # compute attach-start time (pre-cruise)
      t_attach_start_hr_local = (
          float(getattr(aircraft.mission, "depart_taxi_s", 0.0) or 0.0)
        + float(getattr(aircraft.mission, "hover_climb_s", 0.0) or 0.0)
        + float(getattr(aircraft.mission, "trans_climb_s", 0.0) or 0.0)
        + float(getattr(aircraft.mission, "depart_proc_s", 0.0) or 0.0)
        + float(getattr(aircraft.mission, "accel_climb_s", 0.0) or 0.0)
      ) / 3600.0

      # while True, keep flying flights until time runs past the defined operating hours
      while True:

        # aircraft earliest departure (based on its own readiness; eVTOL must wait until its previous flight + ground ops + main battery charge are done)
        t_aircraft_earliest_depart_hr = t_aircraft_ready_hr

        # find ABU choice for this departure
        # first, list ABUs already available by aircraft earliest departure
        ready_indices = []
        for j in range(len(abu_available_times_hr)):
          if abu_available_times_hr[j] <= t_aircraft_earliest_depart_hr:
            ready_indices.append(j)

        if len(ready_indices) > 0:
          # at least one ABU is already ready; then pick the lowest index; no additional ABU wait
          j_min = min(ready_indices)
          t_abu_min_hr = abu_available_times_hr[j_min]
          t_depart_hr = t_aircraft_earliest_depart_hr
        else:
          # no ABU ready yet; then aircraft must wait for earliest ABU to become available
          j_min = 0
          t_abu_min_hr = abu_available_times_hr[0]
          for j in range(1, len(abu_available_times_hr)):
            if abu_available_times_hr[j] < t_abu_min_hr:
              t_abu_min_hr = abu_available_times_hr[j]
              j_min = j
          t_depart_hr = max(t_aircraft_earliest_depart_hr, t_abu_min_hr)

        # check if a full mission can be completed within N-hr
        if t_depart_hr + t_flight_hr_local > daily_operation_hr:
          break

        # log ABU bottleneck wait time (if any; meaning if ABU wasn’t ready, aircraft waited)
        if t_abu_min_hr > t_aircraft_earliest_depart_hr:
          t_wait_abu_day_hr += (t_abu_min_hr - t_aircraft_earliest_depart_hr) # accumulate daily ABU-caused delay

        ## timeline logging 

        flight_idx = n_flights_completed

        # aircraft depart
        aircraft_timeline.append({
          "t_hr": t_depart_hr,
          "event": "aircraft_depart",
          "flight_index": flight_idx
        })

        # ABU attached at depart
        abu_timelines[j_min].append({
          "t_hr": t_depart_hr,
          "event": "abu_attached",
          "flight_index": flight_idx
        })

        # compute detach time
        t_detach_hr = t_depart_hr + t_attach_start_hr_local + t_attach_hr_local

        # ABU detaches
        aircraft_timeline.append({
          "t_hr": t_detach_hr,
          "event": "abu_detach",
          "flight_index": flight_idx
        })
        abu_timelines[j_min].append({
          "t_hr": t_detach_hr,
          "event": "abu_detach",
          "flight_index": flight_idx
        })

        # ABU return
        t_return_done_hr = t_detach_hr + t_return_abu_hr_local
        abu_timelines[j_min].append({
          "t_hr": t_return_done_hr,
          "event": "abu_return_done",
          "flight_index": flight_idx
        })

        # ABU charge
        t_charge_start_abu_hr = t_return_done_hr
        t_charge_done_abu_hr = t_charge_start_abu_hr + t_charge_hr_abu_local

        abu_timelines[j_min].append({
          "t_hr": t_charge_start_abu_hr,
          "event": "abu_charge_start",
          "flight_index": flight_idx
        })
        abu_timelines[j_min].append({
          "t_hr": t_charge_done_abu_hr,
          "event": "abu_charge_done",
          "flight_index": flight_idx
        })

        # update ABU availability
        # mark ABU j_min as busy for this interval (from depart through end of charge)
        abu_available_times_hr[j_min] = t_charge_done_abu_hr
        abu_busy_time_hr[j_min] += (t_charge_done_abu_hr - t_depart_hr) # count its busy duration to compute utilization

        # aircraft arrival
        t_arrive_hr = t_depart_hr + t_flight_hr_local
        aircraft_timeline.append({
          "t_hr": t_arrive_hr,
          "event": "aircraft_arrive",
          "flight_index": flight_idx
        })

        # ground ops done
        t_after_ground_hr = t_arrive_hr + t_ground_ops_hr_local
        aircraft_timeline.append({
          "t_hr": t_after_ground_hr,
          "event": "aircraft_ground_ops_done",
          "flight_index": flight_idx
        })

        # main battery charge
        t_after_charge_main_hr = t_after_ground_hr + t_charge_hr_main_local  # aircraft cycle = flight + ground ops + main battery chargin
        aircraft_timeline.append({
          "t_hr": t_after_charge_main_hr,
          "event": "aircraft_charge_done",
          "flight_index": flight_idx
        })

        t_aircraft_ready_hr = t_after_charge_main_hr

        # total flights per day that fit inside N-hours
        n_flights_completed += 1

      # after simulation: compute daily stats
      # aircraft metrics
      t_flight_day_hr_local = n_flights_completed * t_flight_hr_local
      t_total_used_hr = min(daily_operation_hr, t_aircraft_ready_hr)
      t_slack_hr_local = max(0.0, daily_operation_hr - t_total_used_hr)

      # ABU utilization
      total_busy_hr = sum(abu_busy_time_hr)
      abu_utilization_avg = total_busy_hr / (daily_operation_hr * float(n_abu_pool_local)) if n_abu_pool_local > 0 else 0.0 # fraction of day the ABU pool is busy/ active

      return {
        "n_flights_completed": n_flights_completed,
        "t_flight_day_hr": t_flight_day_hr_local,
        "t_slack_hr": t_slack_hr_local,
        "t_wait_abu_day_hr": t_wait_abu_day_hr,
        "abu_utilization_avg": abu_utilization_avg,
        "aircraft_timeline": aircraft_timeline, #timeline outputs
        "abu_timelines": abu_timelines, #timeline outputs
      }

    # precompute post-cruise segment horizontal distances (aircraft mission geometry)
    mission = aircraft.mission
    decel_h_m_p_s = float(getattr(mission, "decel_descend_avg_h_m_p_s", 0.0) or 0.0)
    decel_s       = float(getattr(mission, "decel_descend_s", 0.0) or 0.0)
    arrive_proc_h = float(getattr(mission, "arrive_proc_h_m_p_s", 0.0) or 0.0)
    arrive_proc_s = float(getattr(mission, "arrive_proc_s", 0.0) or 0.0)
    trans_desc_h  = float(getattr(mission, "trans_descend_avg_h_m_p_s", 0.0) or 0.0)
    trans_desc_s  = float(getattr(mission, "trans_descend_s", 0.0) or 0.0)
    arrive_taxi_h = float(getattr(mission, "arrive_taxi_avg_h_m_p_s", 0.0) or 0.0)
    arrive_taxi_s = float(getattr(mission, "arrive_taxi_s", 0.0) or 0.0)

    d_postcruise_m = \
      decel_h_m_p_s * decel_s + \
      arrive_proc_h * arrive_proc_s + \
      trans_desc_h * trans_desc_s + \
      arrive_taxi_h * arrive_taxi_s

    # main pack nameplate (baseline total mission energy)
    E_pack_kwh_main = aircraft._calc_total_mission_energy_kw_hr()
    if E_pack_kwh_main is None:
      return None

    # reserve mission energy
    E_reserve_kwh = float(aircraft._calc_total_reserve_mission_energy_kw_hr() or 0.0)

    cruise_v_m_p_s = float(getattr(mission, "cruise_h_m_p_s", 0.0) or 0.0)
    cruise_s       = float(getattr(mission, "cruise_s", 0.0) or 0.0)

    # iterate through each ABU mission energy case
    for case in ext_results:
      n_abus                    = int(abu_spec.get("n_abus", 1))
      E_abu_mission_kwh_per_abu = float(case.get("E_abu_mission_kwh", 0.0))
      E_abu_total_kwh_per_abu   = float(case.get("E_abu_total_kwh", 0.0))
      E_abu_used_kwh            = float(case.get("E_abu_used_kwh", 0.0))
      E_saved_kwh               = float(case.get("E_saved_kwh", 0.0))
      t_attached_effective_s    = float(case.get("t_attached_effective_s", 0.0))

      # 1. main aircraft battery (after ABU assistance)
      # pack sized to baseline mission; recharge energy reduced by ABU-supplied cruise share.
      E_mission_kwh_main = max(0.0, E_pack_kwh_main - E_saved_kwh - E_reserve_kwh)  # assume reserve remains in main pack
      dod_main = E_mission_kwh_main / max(E_pack_kwh_main, 1e-9)
      dod_main = max(0.0, min(1.0, dod_main))
      soc_start_main = max(0.0, soc_target - dod_main)

      # 2. ABU battery (per ABU)
      E_ops_kwh_per_abu = abu_spec["E_ops_kwh_per_abu"]
      E_pack_kwh_abu = E_abu_total_kwh_per_abu  # mission + ops

      E_abu_used_per_abu_kwh = E_abu_used_kwh / max(n_abus, 1)
      dod_abu = (E_abu_used_per_abu_kwh + E_ops_kwh_per_abu) / max(E_pack_kwh_abu, 1e-9)
      dod_abu = max(0.0, min(1.0, dod_abu))
      soc_start_abu = max(0.0, soc_target - dod_abu)

      # 3. ABU return time from detach point to landing zone
      # remaining cruise distance (aircraft) from detach point
      t_attach_s_clamped = max(0.0, min(t_attached_effective_s, cruise_s))
      t_cruise_remaining_s = max(0.0, cruise_s - t_attach_s_clamped)
      d_cruise_rem_m = cruise_v_m_p_s * t_cruise_remaining_s

      # total horizontal distance from detach point to landing zone
      d_total_horizontal_m = max(0.0, d_cruise_rem_m + d_postcruise_m)

      t_horizontal_abu_s = d_total_horizontal_m / max(V_abu_horizontal_m_p_s, 1e-9)
      t_vertical_abu_s   = max(0.0, h_detach_ft*0.3048) / max(V_abu_vertical_m_p_s, 1e-9)
      t_return_cruise_abu_hr = (t_horizontal_abu_s + t_vertical_abu_s) / 3600.0

      # ABU attached duration (for overlap)
      t_attached_hr = t_attached_effective_s / 3600.0

      # 4. charging times (main eVTOL + ABUs), using CC–CV model
      chg_main = aircraft._estimate_cccv_charge_time_hr(
        E_pack_kwh=E_pack_kwh_main,
        P_charger_ac_kw=P_charger_ac_kw,
        eta_charger_dc=eta_charger_dc,
        c_rate_max=c_rate_max,
        v_pack_nom_v=v_pack_nom_v_main,
        i_term_c=i_term_c,
        soc_start=soc_start_main,
        soc_target=soc_target,
        soc_cc_end=soc_cc_end
      )
      
      chg_abu = aircraft._estimate_cccv_charge_time_hr(
        E_pack_kwh=E_pack_kwh_abu,
        P_charger_ac_kw=P_charger_ac_kw,
        eta_charger_dc=eta_charger_dc,
        c_rate_max=c_rate_max,
        v_pack_nom_v=v_pack_nom_v_abu,
        i_term_c=i_term_c,
        soc_start=soc_start_abu,
        soc_target=soc_target,
        soc_cc_end=soc_cc_end
      )

      if chg_main is None or chg_abu is None:
        continue

      t_charge_hr_main = float(chg_main.get("t_charge_hr", 0.0))
      t_charge_hr_abu  = float(chg_abu.get("t_charge_hr", 0.0))

      # 5. nominal cycle time if ABUs were infinite (no ABU bottleneck)
      t_cycle_nominal_hr = t_flight_hr + t_charge_hr_main + t_ground_ops_hr
      if t_cycle_nominal_hr <= 0.0:
        continue
      n_flights_nominal = int(daily_operation_hr // t_cycle_nominal_hr)

      # 6. simulate N-hr operations with finite ABU pool and overlapping return+charge
      sim = _simulate_daily_ops_single_evtol(
        n_abu_pool_local       = n_abu_pool,
        t_flight_hr_local      = t_flight_hr,
        t_charge_hr_main_local = t_charge_hr_main,
        t_attach_hr_local      = t_attached_hr,
        t_return_abu_hr_local  = t_return_cruise_abu_hr,
        t_charge_hr_abu_local  = t_charge_hr_abu,
        t_ground_ops_hr_local  = t_ground_ops_hr
      )

      n_flights_completed = sim.get("n_flights_completed", 0)
      t_flight_day_hr_sim = sim.get("t_flight_day_hr", 0.0)
      t_slack_hr_sim      = sim.get("t_slack_hr", 0.0)
      t_wait_abu_day_hr   = sim.get("t_wait_abu_day_hr", 0.0)
      abu_utilization_avg = sim.get("abu_utilization_avg", 0.0)

      abu_bottleneck_flag = (n_flights_completed < n_flights_nominal)

      air_tl = sim.get("aircraft_timeline", [])
      abu_tls = sim.get("abu_timelines", {})

      # 7. store results for this ABU energy case
      results.append({
        "daily_operation_hr": daily_operation_hr,

        "E_abu_mission_kwh_per_abu": E_abu_mission_kwh_per_abu,
        "E_abu_total_kwh_per_abu": E_abu_total_kwh_per_abu,
        "E_abu_used_kwh_total": E_abu_used_kwh,
        "E_saved_kwh": E_saved_kwh,

        "E_pack_kwh_main": E_pack_kwh_main,
        "E_mission_kwh_main": E_mission_kwh_main,
        "E_reserve_kwh": E_reserve_kwh,
        "dod_main": dod_main,
        "soc_start_main": soc_start_main,
        "soc_target": soc_target,

        "n_abus_per_flight": n_abus,
        "n_abu_pool": n_abu_pool,
        "E_ops_kwh_per_abu": E_ops_kwh_per_abu,
        "E_pack_kwh_abu": E_pack_kwh_abu,
        "dod_abu": dod_abu,
        "soc_start_abu": soc_start_abu,

        "t_flight_hr": t_flight_hr,
        "t_attached_hr": t_attached_hr,
        "t_return_cruise_abu_hr": t_return_cruise_abu_hr,
        "t_charge_hr_main": t_charge_hr_main,
        "t_charge_hr_abu": t_charge_hr_abu,
        "t_cycle_nominal_hr": t_cycle_nominal_hr,
        "n_flights_nominal_no_abu_limit": n_flights_nominal,

        "n_flights_completed": n_flights_completed,
        "t_flight_day_hr": t_flight_day_hr_sim,
        "t_slack_hr": t_slack_hr_sim,
        "t_wait_abu_day_hr": t_wait_abu_day_hr,
        "abu_utilization_avg": abu_utilization_avg,
        "abu_bottleneck_flag": abu_bottleneck_flag,

        "P_dc_kw_main": chg_main.get("P_dc_kw", 0.0),
        "P_dc_kw_abu": chg_abu.get("P_dc_kw", 0.0),
        "P_cc_cap_kw_main": chg_main.get("P_cc_cap_kw", 0.0),
        "P_cc_cap_kw_abu": chg_abu.get("P_cc_cap_kw", 0.0),
        "P_cc_kw_main": chg_main.get("P_cc_kw", 0.0),
        "P_cc_kw_abu": chg_abu.get("P_cc_kw", 0.0),
        "I_cc_A_main": chg_main.get("I_cc_A", 0.0),
        "I_cc_A_abu": chg_abu.get("I_cc_A", 0.0),
        "I_term_A_main": chg_main.get("I_term_A", 0.0),
        "I_term_A_abu": chg_abu.get("I_term_A", 0.0),
        "charger_limit_indicator_flag_main": chg_main.get("charger_limit_indicator_flag"),
        "charger_limit_indicator_flag_abu": chg_abu.get("charger_limit_indicator_flag"),

        "aircraft_timeline": air_tl,
        "abu_timelines": abu_tls,
      })

    return results

# ABU Evaluator 4.4: Common Case Economics (Combined: Assisted Takeoff + Extended Flight ABU, Overlap Charging, Daily Utilization with Queuing)
#
# estimates daily utilization (flights/day, flight hours/day) for a single eVTOL when:
#   Takeoff ABUs assist the pre-cruise segments and detach, then return to the TAKEOFF landing zone.
#   Cruise ABUs power the cruise segment and detach on depletion or end-of-cruise, then return to the LANDING zone.
#
# A finite pool of ABUs is modeled for BOTH ABU types:
#   n_abu_pool_takeoff  : number of takeoff ABUs available per landing zone (for assisted takeoff)
#   n_abu_pool_cruise   : number of cruise ABUs available per landing zone (for extended cruise)
#
# For simplicity, we assume each mission is a closed loop starting/ending at an equivalent "landing zone",
# so per-flight we always require:
#   one takeoff ABU from the local takeoff pool
#   one cruise ABU from the local cruise pool
#
# The eVTOL can only depart when:
#   (a) its main battery is recharged and ground ops are complete, and
#   (b) at least one takeoff ABU AND one cruise ABU are fully charged and available.
#
# If not enough ABUs are ready, departure is delayed (ABU bottleneck).
#
# Inputs:
#   candidates                     : list of ABU assisted-takeoff detach cases (same as Evaluator 1 interface)
#   E_mission_kwh_per_abu_list     : list of cruise-ABU mission energy values [kWh per ABU]
#   abu_spec_takeoff               : ABU spec used for assisted takeoff (dict)
#   abu_spec_cruise                : ABU spec used for extended flight (dict)
#   n_abu_pool_takeoff             : size of takeoff-ABU pool at each LZ
#   n_abu_pool_cruise              : size of cruise-ABU pool at each LZ
#   P_charger_ac_kw                : charger AC power [kW] (assumed same for main + ABUs)
#   eta_charger_dc                 : charger AC->DC efficiency (0–1)
#   c_rate_max                     : max allowed charge C-rate (e.g., 1.0)
#   v_pack_nom_v_main              : nominal voltage of eVTOL main pack [V]
#   v_pack_nom_v_abu               : nominal voltage of ABU packs [V] (takeoff & cruise)
#   i_term_c                       : CV termination current ratio (e.g., 0.05C)
#   soc_target                     : target SOC after charge (default 1.0)
#   soc_cc_end                     : SOC where CC ends (default 0.80)
#   t_ground_ops_hr                : ground turnaround ops [hr]
#   V_takeoff_abu_horizontal_m_p_s : takeoff-ABU horizontal speed on return [m/s]
#   V_takeoff_abu_vertical_m_p_s   : takeoff-ABU vertical descent speed on return [m/s]
#   h_detach_takeoff_ft            : takeoff-ABU detach altitude [ft]
#   V_cruise_abu_horizontal_m_p_s  : cruise-ABU horizontal speed on return [m/s]
#   V_cruise_abu_vertical_m_p_s    : cruise-ABU vertical descent speed on return [m/s]
#   h_detach_cruise_ft             : cruise-ABU detach altitude [ft]
#   daily_operation_hr             : daily operation window [hr]
#   mission_time_s                 : optional mission duration [s]; if None, sum main-mission segments
def _evaluate_common_case_abu_combined_flight_overlap_charging_queuing(aircraft,
                                                                        candidates,
                                                                        E_mission_kwh_per_abu_list,
                                                                        abu_spec_takeoff=None,
                                                                        abu_spec_cruise=None,
                                                                        n_abu_pool_takeoff=3,
                                                                        n_abu_pool_cruise=3,
                                                                        P_charger_ac_kw=115.0,
                                                                        eta_charger_dc=0.95,
                                                                        c_rate_max=1.0,
                                                                        v_pack_nom_v_main=800.0,
                                                                        v_pack_nom_v_abu=400.0,
                                                                        i_term_c=0.05,
                                                                        soc_target=1.0,
                                                                        soc_cc_end=0.80,
                                                                        t_ground_ops_hr=0.2833,
                                                                        V_takeoff_abu_horizontal_m_p_s=30.0,
                                                                        V_takeoff_abu_vertical_m_p_s=5.1,
                                                                        h_detach_takeoff_ft=3000.0,
                                                                        V_cruise_abu_horizontal_m_p_s=30.0,
                                                                        V_cruise_abu_vertical_m_p_s=5.1,
                                                                        h_detach_cruise_ft=3000.0,
                                                                        daily_operation_hr = 24.0,
                                                                        mission_time_s=None):

    if aircraft.mission is None or aircraft.propulsion is None or aircraft.environ is None or aircraft.power is None:
      return None

    results = []
    orig_mtow = aircraft.max_takeoff_mass_kg

    # default ABU specifications 
    if abu_spec_takeoff is None:
      abu_spec_takeoff = {
        "n_abus": 1,
        "E_mission_kwh_per_abu": 15.0,
        "E_ops_kwh_per_abu": 6.0,
        "m_struct_kg_per_abu": 50.0,
        "m_integration_kg_per_abu": 10.0,
      }

    if abu_spec_cruise is None:
      abu_spec_cruise = {
        "n_abus": 1,
        "E_ops_kwh_per_abu": 12.0,
        "struct_frac": 0.20,
        "integration_frac": 0.05,
      }

    # assisted takeoff outcomes (Evaluator 1)
    takeoff_out = aircraft.evaluate_abu_detach_candidates(candidates, abu_spec=abu_spec_takeoff)
    if takeoff_out is None or len(takeoff_out) == 0:
      return None

    # compute full main-mission flight time if not provided
    if mission_time_s is None:
      seg_time_names = [
        "depart_taxi_s","hover_climb_s","trans_climb_s","depart_proc_s","accel_climb_s",
        "cruise_s","decel_descend_s","arrive_proc_s","trans_descend_s","hover_descend_s","arrive_taxi_s",
      ]
      mission_time_s = 0.0
      if getattr(aircraft, "mission", None) is not None:
        for nm in seg_time_names:
          mission_time_s += float(getattr(aircraft.mission, nm, 0.0) or 0.0)
    t_flight_hr = (mission_time_s or 0.0) / 3600.0

    # helper: rotor+hub mass per ABU using NDARC-based function
    def _calc_rotor_hub_mass_for_n_abus(n_abus):
      orig_getter = type(aircraft.propulsion).lift_rotor_count.fget
      try:
        type(aircraft.propulsion).lift_rotor_count = property(lambda _self: n_abus)
        return aircraft._calc_lift_rotor_hub_mass_kg()
      finally:
        type(aircraft.propulsion).lift_rotor_count = property(orig_getter)

    # battery parameters (for ABU mass inference)
    spec_energy_Wh_p_kg = aircraft.power.batt_spec_energy_w_h_p_kg
    batt_int_factor = aircraft.power.batt_int_factor
    batt_accessible_frac = 1.0 - aircraft.power.batt_inaccessible_energy_frac

    # main pack nominal capacity (baseline total mission energy; nameplate)
    E_pack_kwh_main_nameplate = aircraft._calc_total_mission_energy_kw_hr()
    if E_pack_kwh_main_nameplate is None:
      return None

    # reserve mission energy
    E_reserve_kwh = float(aircraft._calc_total_reserve_mission_energy_kw_hr() or 0.0)

    mission = aircraft.mission

    # pre-cruise timing and distance (used for both takeoff attach window and takeoff-ABU return distance)
    depart_taxi_s   = float(getattr(mission, "depart_taxi_s", 0.0) or 0.0)
    hover_climb_s   = float(getattr(mission, "hover_climb_s", 0.0) or 0.0)
    trans_climb_s   = float(getattr(mission, "trans_climb_s", 0.0) or 0.0)
    depart_proc_s   = float(getattr(mission, "depart_proc_s", 0.0) or 0.0)
    accel_climb_s   = float(getattr(mission, "accel_climb_s", 0.0) or 0.0)

    depart_taxi_v_h = float(getattr(mission, "depart_taxi_avg_h_m_p_s", 0.0) or 0.0)
    trans_climb_v_h = float(getattr(mission, "trans_climb_avg_h_m_p_s", 0.0) or 0.0)
    depart_proc_v_h = float(getattr(mission, "depart_proc_h_m_p_s", 0.0) or 0.0)
    accel_climb_v_h = float(getattr(mission, "accel_climb_avg_h_m_p_s", 0.0) or 0.0)

    # time from takeoff to start of cruise (also used as takeoff-ABU attach duration)
    t_precruise_s = depart_taxi_s + hover_climb_s + trans_climb_s + depart_proc_s + accel_climb_s
    t_precruise_hr = t_precruise_s / 3600.0

    # horizontal distance to start of cruise (detach point for takeoff ABU)
    d_precruise_m = \
      depart_taxi_v_h * depart_taxi_s + \
      trans_climb_v_h * trans_climb_s + \
      depart_proc_v_h * depart_proc_s + \
      accel_climb_v_h * accel_climb_s

    # post-cruise segment distances (for cruise-ABU return)
    decel_h_m_p_s = float(getattr(mission, "decel_descend_avg_h_m_p_s", 0.0) or 0.0)
    decel_s       = float(getattr(mission, "decel_descend_s", 0.0) or 0.0)
    arrive_proc_h = float(getattr(mission, "arrive_proc_h_m_p_s", 0.0) or 0.0)
    arrive_proc_s = float(getattr(mission, "arrive_proc_s", 0.0) or 0.0)
    trans_desc_h  = float(getattr(mission, "trans_descend_avg_h_m_p_s", 0.0) or 0.0)
    trans_desc_s  = float(getattr(mission, "trans_descend_s", 0.0) or 0.0)
    arrive_taxi_h = float(getattr(mission, "arrive_taxi_avg_h_m_p_s", 0.0) or 0.0)
    arrive_taxi_s = float(getattr(mission, "arrive_taxi_s", 0.0) or 0.0)

    d_postcruise_m = \
      decel_h_m_p_s * decel_s + \
      arrive_proc_h * arrive_proc_s + \
      trans_desc_h  * trans_desc_s + \
      arrive_taxi_h * arrive_taxi_s

    cruise_v_m_p_s = float(getattr(mission, "cruise_h_m_p_s", 0.0) or 0.0)
    cruise_s       = float(getattr(mission, "cruise_s", 0.0) or 0.0)

    # helper: simulate N-hr operations for a single eVTOL with a number of finite ABU pools
    # (takeoff-ABU pool and cruise-ABU pool)
    def _simulate_daily_ops_single_evtol_combined(n_abu_pool_takeoff_local,
                                                  n_abu_pool_cruise_local,
                                                  t_flight_hr_local,
                                                  t_charge_hr_main_local,
                                                  t_takeoff_attach_hr_local,
                                                  t_return_takeoff_abu_hr_local,
                                                  t_charge_takeoff_abu_hr_local,
                                                  t_cruise_attach_hr_local,
                                                  t_cruise_attach_start_hr_local,
                                                  t_return_cruise_abu_hr_local,
                                                  t_charge_cruise_abu_hr_local,
                                                  t_ground_ops_hr_local):

      # initialize aircraft & ABU pools
      t_aircraft_ready_hr = 0.0

      n_takeoff_pool = max(1, n_abu_pool_takeoff_local)
      n_cruise_pool  = max(1, n_abu_pool_cruise_local)

      takeoff_available_times_hr = [0.0 for _ in range(n_takeoff_pool)]
      takeoff_busy_time_hr       = [0.0 for _ in range(n_takeoff_pool)]
      cruise_available_times_hr  = [0.0 for _ in range(n_cruise_pool)]
      cruise_busy_time_hr        = [0.0 for _ in range(n_cruise_pool)]

      # timeline logs
      aircraft_timeline       = []
      takeoff_abu_timelines   = {j: [] for j in range(n_takeoff_pool)}
      cruise_abu_timelines    = {j: [] for j in range(n_cruise_pool)}

      n_flights_completed     = 0
      t_wait_takeoff_abu_day_hr = 0.0
      t_wait_cruise_abu_day_hr  = 0.0

      # loop flights until the defined operating hours
      while True:
        t_aircraft_earliest_depart_hr = t_aircraft_ready_hr

        # --- takeoff ABU selection ---
        ready_takeoff = [
          j for j in range(n_takeoff_pool)
          if takeoff_available_times_hr[j] <= t_aircraft_earliest_depart_hr
        ]

        if len(ready_takeoff) > 0:
          # use lowest-index among ready ABUs
          j_to_min = min(ready_takeoff)
          t_to_min = takeoff_available_times_hr[j_to_min]
        else:
          # no ABUs ready; then pick ABU with minimum availability time
          j_to_min = min(range(n_takeoff_pool),
                         key=lambda j: takeoff_available_times_hr[j])
          t_to_min = takeoff_available_times_hr[j_to_min]

        # --- cruise ABU selection ---
        ready_cruise = [
          j for j in range(n_cruise_pool)
          if cruise_available_times_hr[j] <= t_aircraft_earliest_depart_hr
        ]

        if len(ready_cruise) > 0:
          j_cr_min = min(ready_cruise)
          t_cr_min = cruise_available_times_hr[j_cr_min]
        else:
          j_cr_min = min(range(n_cruise_pool),
                         key=lambda j: cruise_available_times_hr[j])
          t_cr_min = cruise_available_times_hr[j_cr_min]

        # departure time limited by aircraft readiness + ABU availability
        t_block_abu_hr = max(t_to_min, t_cr_min)
        t_depart_hr = max(t_aircraft_earliest_depart_hr, t_block_abu_hr)

        # if departure cannot finish full mission within N-hr, stop
        if t_depart_hr + t_flight_hr_local > daily_operation_hr:
          break

        # attribute ABU-caused waiting (whichever ABU is the bottleneck vs aircraft readiness)
        if t_block_abu_hr > t_aircraft_earliest_depart_hr:
          if t_to_min >= t_cr_min:
            t_wait_takeoff_abu_day_hr += (t_block_abu_hr - t_aircraft_earliest_depart_hr)
          else:
            t_wait_cruise_abu_day_hr += (t_block_abu_hr - t_aircraft_earliest_depart_hr)

        flight_idx = n_flights_completed

        # --- aircraft events ---
        aircraft_timeline.append({
          "t_hr": t_depart_hr,
          "event": "aircraft_depart",
          "flight_index": flight_idx
        })

        # arrival at end of mission
        t_arrive_hr = t_depart_hr + t_flight_hr_local
        aircraft_timeline.append({
          "t_hr": t_arrive_hr,
          "event": "aircraft_arrive",
          "flight_index": flight_idx
        })

        # ground ops
        t_after_ground_hr = t_arrive_hr + t_ground_ops_hr_local
        aircraft_timeline.append({
          "t_hr": t_after_ground_hr,
          "event": "aircraft_ground_ops_done",
          "flight_index": flight_idx
        })

        # main battery charge
        t_after_main_charge_hr = t_after_ground_hr + t_charge_hr_main_local
        aircraft_timeline.append({
          "t_hr": t_after_main_charge_hr,
          "event": "aircraft_charge_done",
          "flight_index": flight_idx
        })

        t_aircraft_ready_hr = t_after_main_charge_hr

        # --- takeoff ABU timeline ---
        # attach from departure; detach after takeoff attach duration
        t_takeoff_attach_start_hr = t_depart_hr
        t_takeoff_detach_hr = t_takeoff_attach_start_hr + t_takeoff_attach_hr_local

        takeoff_abu_timelines[j_to_min].append({
          "t_hr": t_takeoff_attach_start_hr,
          "event": "takeoff_abu_attached",
          "flight_index": flight_idx
        })
        takeoff_abu_timelines[j_to_min].append({
          "t_hr": t_takeoff_detach_hr,
          "event": "takeoff_abu_detach",
          "flight_index": flight_idx
        })

        # return & charge
        t_takeoff_return_done_hr = t_takeoff_detach_hr + t_return_takeoff_abu_hr_local
        takeoff_abu_timelines[j_to_min].append({
          "t_hr": t_takeoff_return_done_hr,
          "event": "takeoff_abu_return_done",
          "flight_index": flight_idx
        })

        t_takeoff_charge_start_hr = t_takeoff_return_done_hr
        t_takeoff_charge_done_hr = t_takeoff_charge_start_hr + t_charge_takeoff_abu_hr_local

        takeoff_abu_timelines[j_to_min].append({
          "t_hr": t_takeoff_charge_start_hr,
          "event": "takeoff_abu_charge_start",
          "flight_index": flight_idx
        })
        takeoff_abu_timelines[j_to_min].append({
          "t_hr": t_takeoff_charge_done_hr,
          "event": "takeoff_abu_charge_done",
          "flight_index": flight_idx
        })

        takeoff_available_times_hr[j_to_min] = t_takeoff_charge_done_hr
        takeoff_busy_time_hr[j_to_min] += (t_takeoff_charge_done_hr - t_depart_hr)

        # --- cruise ABU timeline ---
        # attach sometime into the mission (start of cruise)
        t_cruise_attach_start_hr = t_depart_hr + t_cruise_attach_start_hr_local
        t_cruise_detach_hr = t_cruise_attach_start_hr + t_cruise_attach_hr_local

        cruise_abu_timelines[j_cr_min].append({
          "t_hr": t_cruise_attach_start_hr,
          "event": "cruise_abu_attached",
          "flight_index": flight_idx
        })
        cruise_abu_timelines[j_cr_min].append({
          "t_hr": t_cruise_detach_hr,
          "event": "cruise_abu_detach",
          "flight_index": flight_idx
        })

        t_cruise_return_done_hr = t_cruise_detach_hr + t_return_cruise_abu_hr_local
        cruise_abu_timelines[j_cr_min].append({
          "t_hr": t_cruise_return_done_hr,
          "event": "cruise_abu_return_done",
          "flight_index": flight_idx
        })

        t_cruise_charge_start_hr = t_cruise_return_done_hr
        t_cruise_charge_done_hr = t_cruise_charge_start_hr + t_charge_cruise_abu_hr_local

        cruise_abu_timelines[j_cr_min].append({
          "t_hr": t_cruise_charge_start_hr,
          "event": "cruise_abu_charge_start",
          "flight_index": flight_idx
        })
        cruise_abu_timelines[j_cr_min].append({
          "t_hr": t_cruise_charge_done_hr,
          "event": "cruise_abu_charge_done",
          "flight_index": flight_idx
        })

        cruise_available_times_hr[j_cr_min] = t_cruise_charge_done_hr
        cruise_busy_time_hr[j_cr_min] += (t_cruise_charge_done_hr - t_depart_hr)

        # increment completed flights
        n_flights_completed += 1

      # after simulation: compute daily stats
      t_flight_day_hr_local = n_flights_completed * t_flight_hr_local
      t_total_used_hr = min(daily_operation_hr, t_aircraft_ready_hr)
      t_slack_hr_local = max(0.0, daily_operation_hr - t_total_used_hr)

      total_busy_takeoff_hr = sum(takeoff_busy_time_hr)
      total_busy_cruise_hr  = sum(cruise_busy_time_hr)

      abu_utilization_avg_takeoff = total_busy_takeoff_hr / (daily_operation_hr * float(n_takeoff_pool)) if n_takeoff_pool > 0 else 0.0
      abu_utilization_avg_cruise  = total_busy_cruise_hr / (daily_operation_hr * float(n_cruise_pool)) if n_cruise_pool > 0 else 0.0

      return {
        "n_flights_completed": n_flights_completed,
        "t_flight_day_hr": t_flight_day_hr_local,
        "t_slack_hr": t_slack_hr_local,
        "t_wait_takeoff_abu_day_hr": t_wait_takeoff_abu_day_hr,
        "t_wait_cruise_abu_day_hr": t_wait_cruise_abu_day_hr,
        "abu_utilization_avg_takeoff": abu_utilization_avg_takeoff,
        "abu_utilization_avg_cruise": abu_utilization_avg_cruise,
        "aircraft_timeline": aircraft_timeline,
        "takeoff_abu_timelines": takeoff_abu_timelines,
        "cruise_abu_timelines": cruise_abu_timelines,
      }

    # iterate combined scenarios (for each assisted-takeoff candidate & cruise-ABU energy level)
    for cand in takeoff_out:
      cand_name = cand.get("name", "unknown")

      # assisted-takeoff result: main-pack energy after offloading pre-cruise energy to ABUs
      E_aircraft_after_takeoff_kwh = float(cand.get("aircraft_total_kwh_after", 0.0))
      MTOW_detached = float(cand.get("MTOW_detached_kg", orig_mtow))
      E_abu_used_takeoff_kwh = float(cand.get("E_abu_used_kwh", 0.0))

      # takeoff ABU properties
      n_abus_takeoff = int(abu_spec_takeoff.get("n_abus", 1))
      E_ops_takeoff_per_abu_kwh = float(abu_spec_takeoff.get("E_ops_kwh_per_abu", 6.0))
      E_pack_takeoff_abu_per_abu_kwh = float(abu_spec_takeoff.get("E_mission_kwh_per_abu", 0.0)) + E_ops_takeoff_per_abu_kwh

      # SoC of takeoff ABUs at start of charge (used mission + ops reserve)
      E_used_mission_takeoff_per_abu_kwh = E_abu_used_takeoff_kwh / max(n_abus_takeoff, 1)
      dod_abu_takeoff = (E_used_mission_takeoff_per_abu_kwh + E_ops_takeoff_per_abu_kwh) / max(E_pack_takeoff_abu_per_abu_kwh, 1e-9)
      dod_abu_takeoff = max(0.0, min(1.0, dod_abu_takeoff))
      soc_start_abu_takeoff = max(0.0, soc_target - dod_abu_takeoff)

      # pre-cruise attach duration for takeoff ABU (entire pre-cruise sequence)
      t_takeoff_attach_hr = t_precruise_hr

      # horizontal + vertical return time for takeoff ABU
      t_horizontal_takeoff_abu_s = d_precruise_m / max(V_takeoff_abu_horizontal_m_p_s, 1e-9)
      t_vertical_takeoff_abu_s   = max(0.0, h_detach_takeoff_ft * 0.3048) / max(V_takeoff_abu_vertical_m_p_s, 1e-9)
      t_return_takeoff_abu_hr    = (t_horizontal_takeoff_abu_s + t_vertical_takeoff_abu_s) / 3600.0

      # sweep cruise ABU energies (recomputed at post-detach MTOW)
      for E_abu_mission_cruise_per_abu_kwh in E_mission_kwh_per_abu_list:
        n_abus_cruise = int(abu_spec_cruise.get("n_abus", 1))
        E_ops_cruise_per_abu_kwh = float(abu_spec_cruise.get("E_ops_kwh_per_abu", 12.0))
        struct_frac = float(abu_spec_cruise.get("struct_frac", 0.20))
        integ_frac  = float(abu_spec_cruise.get("integration_frac", 0.05))

        # ABU cruise pack nameplate per ABU
        E_pack_cruise_abu_per_abu_kwh = float(E_abu_mission_cruise_per_abu_kwh) + E_ops_cruise_per_abu_kwh

        # infer ABU cruise mass (battery + structure + integration + rotor)
        m_abu_batt_per_abu_kg = (E_pack_cruise_abu_per_abu_kwh * 1000.0) / max(
          spec_energy_Wh_p_kg * batt_accessible_frac * batt_int_factor, 1e-9
        )
        m_struct_per_abu_kg = struct_frac * m_abu_batt_per_abu_kg
        m_integ_per_abu_kg  = integ_frac * m_abu_batt_per_abu_kg
        m_rotor_per_abu_kg  = _calc_rotor_hub_mass_for_n_abus(n_abus_cruise) / max(n_abus_cruise, 1)
        m_abu_total_all_kg  = n_abus_cruise * (
          m_abu_batt_per_abu_kg + m_struct_per_abu_kg + m_integ_per_abu_kg + m_rotor_per_abu_kg
        )

        # recompute cruise powers at POST-TAKEOFF MTOW
        prev_mtow = aircraft.max_takeoff_mass_kg
        try:
          # baseline (no cruise ABUs) at post-takeoff MTOW
          aircraft.max_takeoff_mass_kg = MTOW_detached
          baseline_cruise_power_kw = float(aircraft._calc_cruise_avg_electric_power_kw() or 0.0)
          baseline_cruise_energy_kwh = float(aircraft._calc_cruise_energy_kw_hr() or 0.0)

          # attached cruise with ABUs (heavier by m_abu_total_all_kg)
          aircraft.max_takeoff_mass_kg = MTOW_detached + m_abu_total_all_kg
          P_cruise_attach_kw = float(aircraft._calc_cruise_avg_electric_power_kw() or 0.0)
        finally:
          aircraft.max_takeoff_mass_kg = prev_mtow

        if P_cruise_attach_kw <= 0.0 or baseline_cruise_power_kw <= 0.0:
          continue

        # cruise ABU depletion and attached duration
        E_abu_total_cruise_kwh = float(E_abu_mission_cruise_per_abu_kwh) * n_abus_cruise
        t_attached_until_depletion_s = (E_abu_total_cruise_kwh / P_cruise_attach_kw) * 3600.0
        t_baseline_cruise_s          = (baseline_cruise_energy_kwh / baseline_cruise_power_kw) * 3600.0
        t_attached_effective_s       = min(t_attached_until_depletion_s, t_baseline_cruise_s)

        # ABU energy actually used
        E_cruise_attach_kwh          = P_cruise_attach_kw * (t_attached_effective_s / 3600.0)
        E_abu_used_cruise_total_kwh  = min(E_abu_total_cruise_kwh, E_cruise_attach_kwh)

        # main-battery energy saved on cruise at post-detach MTOW
        E_saved_kwh_cruise = min(
          baseline_cruise_power_kw * (t_attached_effective_s / 3600.0),
          baseline_cruise_energy_kwh
        )

        # main pack energy to recharge (after takeoff + cruise ABU assistance)
        E_pack_kwh_main = E_aircraft_after_takeoff_kwh
        E_mission_kwh_main = max(0.0, E_pack_kwh_main - E_saved_kwh_cruise - E_reserve_kwh)
        dod_main = E_mission_kwh_main / max(E_pack_kwh_main, 1e-9)
        dod_main = max(0.0, min(1.0, dod_main))
        soc_start_main = max(0.0, soc_target - dod_main)

        # cruise ABU SoC at start of charge
        E_used_mission_cruise_per_abu_kwh = E_abu_used_cruise_total_kwh / max(n_abus_cruise, 1)
        dod_abu_cruise = (E_used_mission_cruise_per_abu_kwh + E_ops_cruise_per_abu_kwh) / max(
          E_pack_cruise_abu_per_abu_kwh, 1e-9
        )
        dod_abu_cruise = max(0.0, min(1.0, dod_abu_cruise))
        soc_start_abu_cruise = max(0.0, soc_target - dod_abu_cruise)

        # cruise ABU attach duration (time under ABU power)
        t_cruise_attach_hr = t_attached_effective_s / 3600.0

        # time from departure to cruise start (same as pre-cruise)
        t_cruise_attach_start_hr = t_precruise_hr

        # cruise ABU return time (from detach point to LZ)
        t_attach_s_clamped = max(0.0, min(t_attached_effective_s, cruise_s))
        t_cruise_remaining_s = max(0.0, cruise_s - t_attach_s_clamped)
        d_cruise_rem_m = cruise_v_m_p_s * t_cruise_remaining_s
        d_total_horizontal_cruise_m = max(0.0, d_cruise_rem_m + d_postcruise_m)

        t_horizontal_cruise_abu_s = d_total_horizontal_cruise_m / max(V_cruise_abu_horizontal_m_p_s, 1e-9)
        t_vertical_cruise_abu_s   = max(0.0, h_detach_cruise_ft * 0.3048) / max(V_cruise_abu_vertical_m_p_s, 1e-9)
        t_return_cruise_abu_hr    = (t_horizontal_cruise_abu_s + t_vertical_cruise_abu_s) / 3600.0

        # charging times (main eVTOL + ABUs) via CC–CV
        chg_main = aircraft._estimate_cccv_charge_time_hr(
          E_pack_kwh=E_pack_kwh_main,
          P_charger_ac_kw=P_charger_ac_kw,
          eta_charger_dc=eta_charger_dc,
          c_rate_max=c_rate_max,
          v_pack_nom_v=v_pack_nom_v_main,
          i_term_c=i_term_c,
          soc_start=soc_start_main,
          soc_target=soc_target,
          soc_cc_end=soc_cc_end
        )

        chg_takeoff_abu = aircraft._estimate_cccv_charge_time_hr(
          E_pack_kwh=E_pack_takeoff_abu_per_abu_kwh,
          P_charger_ac_kw=P_charger_ac_kw,
          eta_charger_dc=eta_charger_dc,
          c_rate_max=c_rate_max,
          v_pack_nom_v=v_pack_nom_v_abu,
          i_term_c=i_term_c,
          soc_start=soc_start_abu_takeoff,
          soc_target=soc_target,
          soc_cc_end=soc_cc_end
        )

        chg_cruise_abu = aircraft._estimate_cccv_charge_time_hr(
          E_pack_kwh=E_pack_cruise_abu_per_abu_kwh,
          P_charger_ac_kw=P_charger_ac_kw,
          eta_charger_dc=eta_charger_dc,
          c_rate_max=c_rate_max,
          v_pack_nom_v=v_pack_nom_v_abu,
          i_term_c=i_term_c,
          soc_start=soc_start_abu_cruise,
          soc_target=soc_target,
          soc_cc_end=soc_cc_end
        )

        if chg_main is None or chg_takeoff_abu is None or chg_cruise_abu is None:
          continue

        t_charge_hr_main        = float(chg_main.get("t_charge_hr", 0.0))
        t_charge_hr_takeoff_abu = float(chg_takeoff_abu.get("t_charge_hr", 0.0))
        t_charge_hr_cruise_abu  = float(chg_cruise_abu.get("t_charge_hr", 0.0))

        # nominal cycle assuming infinite ABUs (no queuing limit)
        t_cycle_nominal_hr = t_flight_hr + t_charge_hr_main + t_ground_ops_hr
        if t_cycle_nominal_hr <= 0.0:
          continue
        n_flights_nominal = int(daily_operation_hr // t_cycle_nominal_hr)

        # simulate N-hr operations with BOTH finite pools and explicit return + charge timelines
        sim = _simulate_daily_ops_single_evtol_combined(
          n_abu_pool_takeoff_local       = n_abu_pool_takeoff,
          n_abu_pool_cruise_local        = n_abu_pool_cruise,
          t_flight_hr_local              = t_flight_hr,
          t_charge_hr_main_local         = t_charge_hr_main,
          t_takeoff_attach_hr_local      = t_takeoff_attach_hr,
          t_return_takeoff_abu_hr_local  = t_return_takeoff_abu_hr,
          t_charge_takeoff_abu_hr_local  = t_charge_hr_takeoff_abu,
          t_cruise_attach_hr_local       = t_cruise_attach_hr,
          t_cruise_attach_start_hr_local = t_cruise_attach_start_hr,
          t_return_cruise_abu_hr_local   = t_return_cruise_abu_hr,
          t_charge_cruise_abu_hr_local   = t_charge_hr_cruise_abu,
          t_ground_ops_hr_local          = t_ground_ops_hr
        )

        n_flights_completed        = sim.get("n_flights_completed", 0)
        t_flight_day_hr_sim        = sim.get("t_flight_day_hr", 0.0)
        t_slack_hr_sim             = sim.get("t_slack_hr", 0.0)
        t_wait_takeoff_abu_day_hr  = sim.get("t_wait_takeoff_abu_day_hr", 0.0)
        t_wait_cruise_abu_day_hr   = sim.get("t_wait_cruise_abu_day_hr", 0.0)
        abu_util_takeoff_avg       = sim.get("abu_utilization_avg_takeoff", 0.0)
        abu_util_cruise_avg        = sim.get("abu_utilization_avg_cruise", 0.0)

        abu_bottleneck_takeoff_flag = (n_flights_completed < n_flights_nominal and t_wait_takeoff_abu_day_hr > 0.0)
        abu_bottleneck_cruise_flag  = (n_flights_completed < n_flights_nominal and t_wait_cruise_abu_day_hr > 0.0)

        aircraft_timeline          = sim.get("aircraft_timeline", [])
        takeoff_abu_timelines      = sim.get("takeoff_abu_timelines", {})
        cruise_abu_timelines       = sim.get("cruise_abu_timelines", {})

        # store combined result for this (candidate, cruise-ABU energy) pair
        results.append({
          "daily_operation_hr": daily_operation_hr,

          "candidate_name": cand_name,

          # cruise ABU sweep value
          "E_abu_mission_cruise_per_abu_kwh": float(E_abu_mission_cruise_per_abu_kwh),

          # main pack (after takeoff + cruise ABU assistance)
          "E_pack_kwh_main": E_pack_kwh_main,
          "E_mission_kwh_main": E_mission_kwh_main,
          "E_reserve_kwh": E_reserve_kwh,
          "dod_main": dod_main,
          "soc_start_main": soc_start_main,
          "soc_target": soc_target,
          "soc_cc_end": soc_cc_end,

          # takeoff ABUs (per flight)
          "n_abus_takeoff_per_flight": n_abus_takeoff,
          "n_abu_pool_takeoff": n_abu_pool_takeoff,
          "E_abu_used_takeoff_total_kwh": E_abu_used_takeoff_kwh,
          "E_ops_takeoff_per_abu_kwh": E_ops_takeoff_per_abu_kwh,
          "E_pack_takeoff_abu_per_abu_kwh": E_pack_takeoff_abu_per_abu_kwh,
          "soc_start_abu_takeoff": soc_start_abu_takeoff,
          "dod_abu_takeoff": dod_abu_takeoff,
          "t_takeoff_attach_hr": t_takeoff_attach_hr,
          "t_return_takeoff_abu_hr": t_return_takeoff_abu_hr,

          # cruise ABUs (per flight)
          "n_abus_cruise_per_flight": n_abus_cruise,
          "n_abu_pool_cruise": n_abu_pool_cruise,
          "E_abu_used_cruise_total_kwh": E_abu_used_cruise_total_kwh,
          "E_saved_kwh_cruise": E_saved_kwh_cruise,
          "E_ops_cruise_per_abu_kwh": E_ops_cruise_per_abu_kwh,
          "E_pack_cruise_abu_per_abu_kwh": E_pack_cruise_abu_per_abu_kwh,
          "soc_start_abu_cruise": soc_start_abu_cruise,
          "dod_abu_cruise": dod_abu_cruise,
          "t_cruise_attach_hr": t_cruise_attach_hr,
          "t_cruise_attach_start_hr": t_cruise_attach_start_hr,
          "t_return_cruise_abu_hr": t_return_cruise_abu_hr,

          # timing & nominal cycle
          "t_flight_hr": t_flight_hr,
          "t_charge_hr_main": t_charge_hr_main,
          "t_charge_hr_takeoff_abu": t_charge_hr_takeoff_abu,
          "t_charge_hr_cruise_abu": t_charge_hr_cruise_abu,
          "t_cycle_nominal_hr": t_cycle_nominal_hr,
          "n_flights_nominal_no_abu_limit": n_flights_nominal,

          # N-hr simulation results with queuing
          "n_flights_completed": n_flights_completed,
          "t_flight_day_hr": t_flight_day_hr_sim,
          "t_slack_hr": t_slack_hr_sim,
          "t_wait_takeoff_abu_day_hr": t_wait_takeoff_abu_day_hr,
          "t_wait_cruise_abu_day_hr": t_wait_cruise_abu_day_hr,
          "abu_utilization_avg_takeoff": abu_util_takeoff_avg,
          "abu_utilization_avg_cruise": abu_util_cruise_avg,
          "abu_bottleneck_takeoff_flag": abu_bottleneck_takeoff_flag,
          "abu_bottleneck_cruise_flag": abu_bottleneck_cruise_flag,

          # charger / power details
          "charger_ac_kw": P_charger_ac_kw,
          "eta_charger_dc": eta_charger_dc,
          "c_rate_max": c_rate_max,
          "v_pack_nom_v_main": v_pack_nom_v_main,
          "v_pack_nom_v_abu": v_pack_nom_v_abu,
          "i_term_c": i_term_c,

          "P_dc_kw_main": chg_main.get("P_dc_kw", 0.0),
          "P_cc_cap_kw_main": chg_main.get("P_cc_cap_kw", 0.0),
          "P_cc_kw_main": chg_main.get("P_cc_kw", 0.0),
          "I_cc_A_main": chg_main.get("I_cc_A", 0.0),
          "I_term_A_main": chg_main.get("I_term_A", 0.0),
          "charger_limit_indicator_flag_main": chg_main.get("charger_limit_indicator_flag"),

          "P_dc_kw_takeoff_abu": chg_takeoff_abu.get("P_dc_kw", 0.0),
          "P_cc_cap_kw_takeoff_abu": chg_takeoff_abu.get("P_cc_cap_kw", 0.0),
          "P_cc_kw_takeoff_abu": chg_takeoff_abu.get("P_cc_kw", 0.0),
          "I_cc_A_takeoff_abu": chg_takeoff_abu.get("I_cc_A", 0.0),
          "I_term_A_takeoff_abu": chg_takeoff_abu.get("I_term_A", 0.0),
          "charger_limit_indicator_flag_takeoff_abu": chg_takeoff_abu.get("charger_limit_indicator_flag"),

          "P_dc_kw_cruise_abu": chg_cruise_abu.get("P_dc_kw", 0.0),
          "P_cc_cap_kw_cruise_abu": chg_cruise_abu.get("P_cc_cap_kw", 0.0),
          "P_cc_kw_cruise_abu": chg_cruise_abu.get("P_cc_kw", 0.0),
          "I_cc_A_cruise_abu": chg_cruise_abu.get("I_cc_A", 0.0),
          "I_term_A_cruise_abu": chg_cruise_abu.get("I_term_A", 0.0),
          "charger_limit_indicator_flag_cruise_abu": chg_cruise_abu.get("charger_limit_indicator_flag"),

          # full timelines (for later plotting / debugging)
          "aircraft_timeline": aircraft_timeline,
          "takeoff_abu_timelines": takeoff_abu_timelines,
          "cruise_abu_timelines": cruise_abu_timelines,
        })

    # restore MTOW
    aircraft.max_takeoff_mass_kg = orig_mtow
    return results
