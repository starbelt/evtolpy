# aircraft_iteration.py
#
# Weight iteration module for aircraft model
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

# iterate Maximum Takeoff Weight (MTOW) until convergence
def _iterate_mtow(aircraft, tol=1e-3, max_iter=150):
    mtow_guess = aircraft.max_takeoff_mass_kg
    history = []

    for i in range(max_iter):
      aircraft.max_takeoff_mass_kg = mtow_guess

      # recalculate dependent masses on this guess
      empty_mass_kg = aircraft.empty_mass_kg
      battery_mass_kg = aircraft.battery_mass_kg

      if battery_mass_kg is None:
        raise ValueError(
            f"Battery mass could not be computed at iteration {i}. "
            f"Likely mission infeasible for this config."
        )

      new_mtow = empty_mass_kg + aircraft.payload_kg + battery_mass_kg

      delta = new_mtow - mtow_guess

      # store iteration data
      history.append({
          "iteration": i,
          "mtow_guess_kg": mtow_guess,
          "new_mtow_kg": new_mtow,
          "delta_kg": delta,
          "empty_mass_kg": empty_mass_kg,
          "battery_mass_kg": battery_mass_kg,
          "payload_mass_kg": aircraft.payload_kg,
          "total_energy_converged_kw_hr": aircraft._calc_total_mission_energy_kw_hr()
      })

      if abs(delta) < tol:
        aircraft.max_takeoff_mass_kg = new_mtow
        return new_mtow, history
      
      mtow_guess = new_mtow
    
    aircraft.max_takeoff_mass_kg = mtow_guess

    return mtow_guess, history