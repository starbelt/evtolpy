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
    initial_mtow_kg = mtow_guess
    max_reasonable_mtow_kg = 10.0 * initial_mtow_kg
    previous_abs_delta = None
    divergence_count = 0
    max_divergence_count = 10
    history = []

    for i in range(max_iter):
      if not math.isfinite(mtow_guess) or mtow_guess <= 0.0:
        raise ValueError(
            f"Invalid MTOW guess at iteration {i}: {mtow_guess}. "
            f"The sizing iteration became non-physical."
        )

      if mtow_guess > max_reasonable_mtow_kg:
        raise ValueError(
          f"MTOW iteration diverged at iteration {i}: "
          f"MTOW guess reached {mtow_guess:.3f} kg, which exceeds "
          f"{max_reasonable_mtow_kg:.3f} kg "
          f"({max_reasonable_mtow_kg / initial_mtow_kg:.1f}x the initial MTOW). "
          f"The aircraft template parameters are likely physically self-inconsistent "
          f"under the current mass and energy models. Check inputs such as wingspan, "
          f"tail arm, rotor count, rotor diameter, EPU mass scaling, battery mass, "
          f"and mission energy requirements."
      )
      
      aircraft.max_takeoff_mass_kg = mtow_guess

      # recalculate dependent masses on this guess
      empty_mass_kg = aircraft.empty_mass_kg
      battery_mass_kg = aircraft.battery_mass_kg

      if empty_mass_kg is None or battery_mass_kg is None:
        raise ValueError(
            f"Mass could not be computed at iteration {i}: "
            f"empty_mass_kg={empty_mass_kg}, "
            f"battery_mass_kg={battery_mass_kg}. "
            f"Likely mission infeasible for this config."
        )

      if not math.isfinite(empty_mass_kg) or not math.isfinite(battery_mass_kg):
        raise ValueError(
            f"Non-finite mass calculated at iteration {i}: "
            f"empty_mass_kg={empty_mass_kg}, "
            f"battery_mass_kg={battery_mass_kg}. "
            f"Likely mission infeasible for this config."
        )

      new_mtow = empty_mass_kg + aircraft.payload_kg + battery_mass_kg

      delta = new_mtow - mtow_guess
      abs_delta = abs(delta)

      if not math.isfinite(new_mtow) or not math.isfinite(delta):
        raise ValueError(
            f"Non-finite MTOW update at iteration {i}: "
            f"new_mtow={new_mtow}, delta={delta}. "
            f"Likely mission infeasible for this config."
        )

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

      if previous_abs_delta is not None:
        if delta > 0.0 and abs_delta > previous_abs_delta:
          divergence_count += 1
        else:
          divergence_count = 0

        if divergence_count >= max_divergence_count and abs_delta / mtow_guess > 0.05:
          raise ValueError(
              f"MTOW iteration is diverging at iteration {i}: "
              f"mtow_guess={mtow_guess:.3f} kg, "
              f"new_mtow={new_mtow:.3f} kg, "
              f"delta={delta:.3f} kg "
              f"({abs_delta / mtow_guess:.1%} of current MTOW). "
              f"The residual has increased for {divergence_count} consecutive iterations. "
              f"The aircraft template parameters are likely physically self-inconsistent "
              f"under the current mass and energy models. Check inputs such as wingspan, "
              f"tail arm, rotor count, rotor diameter, EPU mass scaling, battery mass, "
              f"and mission energy requirements."
          )
        
      previous_abs_delta = abs_delta
      
      mtow_guess = new_mtow
    
    aircraft.max_takeoff_mass_kg = mtow_guess

    return mtow_guess, history