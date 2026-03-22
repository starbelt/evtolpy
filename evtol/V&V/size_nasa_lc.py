

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from evtol.aircraft import Aircraft

# Construct the absolute path to the JSON file
json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'NASA_LC.json'))
ac = Aircraft(json_path)

# MTOW Convergence 
final_mtow, history = ac._iterate_mtow()

print(f"Initial MTOW guess:  {history[0]['mtow_guess_kg']:.2f} kg")
print(f"Converged MTOW:      {final_mtow:.2f} kg")
print(f"Iterations:          {len(history)}")
print(f"Final delta:         {history[-1]['delta_kg']:.6f} kg")
print(f"Cruise CL:           {ac.cruise_cl:.4f}")
print(f"Cruise CD:           {ac.cruise_cd:.5f}")
print(f"Cruise L/D:          {ac.cruise_l_p_d:.2f}")

# Drag Breakdown 
print(f"\n{'Drag Component':<25s} {'CD':>10s} {'Fraction':>10s}")
print("-" * 46)
drag_components = {
    'Fuselage':          ac.fuselage_cd0,
    'Horizontal Tail':   ac.horiz_tail_cd0,
    'Vertical Tail':     ac.vert_tail_cd0,
    'Landing Gear':      ac.landing_gear_cd0,
    'Stopped Rotors':    ac.stopped_rotor_cd0,
    'Induced Drag':      ac.induced_drag_cdi,
}
total_cd = 0.0
for name, cd_val in drag_components.items():
    print(f"{name:<25s} {cd_val:>10.5f} {cd_val/ac.cruise_cd:>9.1%}")
    total_cd += cd_val
print("-" * 46)
print(f"{'Total CD':<25s} {ac.cruise_cd:>10.5f}")

# Iteration History 
print(f"\n{'Iter':>4s} {'Guess (kg)':>12s} {'New (kg)':>12s} {'Delta (kg)':>12s} {'Empty (kg)':>12s} {'Batt (kg)':>10s}")
print("-" * 65)
for row in history:
    print(f"{row['iteration']:>4d} {row['mtow_guess_kg']:>12.2f} {row['new_mtow_kg']:>12.2f} "
          f"{row['delta_kg']:>12.4f} {row['empty_mass_kg']:>12.2f} {row['battery_mass_kg']:>10.2f}")

# Mass Breakdown 
structural = {
    'Wing':               ac.wing_mass_kg,
    'Horizontal Tail':    ac.horiz_tail_mass_kg,
    'Vertical Tail':      ac.vert_tail_mass_kg,
    'Fuselage':           ac.fuselage_mass_kg,
    'Boom':               ac.boom_mass_kg,
    'Landing Gear':       ac.landing_gear_mass_kg,
}

propulsion = {
    'EPU (all rotors)':   ac.epu_mass_kg,
    'Lift Rotor + Hub':   ac.lift_rotor_hub_mass_kg,
    'Tilt Rotor':         ac.tilt_rotor_mass_kg,
}

subsystems = {
    'Actuators':          ac.actuator_mass_kg,
    'Furnishings':        ac.furnishings_mass_kg,
    'Env. Control':       ac.environmental_control_system_mass_kg,
    'Avionics':           ac.avionics_mass_kg,
    'Hi-Volt Power':      ac.hivolt_power_dist_mass_kg,
    'Lo-Volt Power':      ac.lovolt_power_coms_mass_kg,
}

print(f"\n{'Component':<22s} {'Mass (kg)':>10s} {'Fraction':>10s}")
print("=" * 44)

print("-- Structural --")
for name, mass in structural.items():
    print(f"  {name:<20s} {mass:>10.2f} {mass/ac.max_takeoff_mass_kg:>9.1%}")

print("-- Propulsion --")
for name, mass in propulsion.items():
    print(f"  {name:<20s} {mass:>10.2f} {mass/ac.max_takeoff_mass_kg:>9.1%}")

print("-- Subsystems --")
for name, mass in subsystems.items():
    print(f"  {name:<20s} {mass:>10.2f} {mass/ac.max_takeoff_mass_kg:>9.1%}")

print("=" * 44)
print(f"  {'Empty Mass':<20s} {ac.empty_mass_kg:>10.2f} {ac.empty_mass_kg/ac.max_takeoff_mass_kg:>9.1%}")
print(f"  {'Battery':<20s} {ac.battery_mass_kg:>10.2f} {ac.battery_mass_kg/ac.max_takeoff_mass_kg:>9.1%}")
print(f"  {'Payload':<20s} {ac.payload_kg:>10.2f} {ac.payload_kg/ac.max_takeoff_mass_kg:>9.1%}")
print("=" * 44)
print(f"  {'MTOW':<20s} {ac.max_takeoff_mass_kg:>10.2f}")

# Energy by Segment 
primary_segments = [
    ('Depart Taxi',         ac.depart_taxi_energy_kw_hr),
    ('Hover Climb',         ac.hover_climb_energy_kw_hr),
    ('Transition Climb',    ac.trans_climb_energy_kw_hr),
    ('Depart Procedures',   ac.depart_proc_energy_kw_hr),
    ('Accelerate Climb',    ac.accel_climb_energy_kw_hr),
    ('Cruise',              ac.cruise_energy_kw_hr),
    ('Decelerate Descend',  ac.decel_descend_energy_kw_hr),
    ('Arrive Procedures',   ac.arrive_proc_energy_kw_hr),
    ('Transition Descend',  ac.trans_descend_energy_kw_hr),
    ('Hover Descend',       ac.hover_descend_energy_kw_hr),
    ('Arrive Taxi',         ac.arrive_taxi_energy_kw_hr),
]

reserve_segments = [
    ('Rsv Hover Climb',     ac.reserve_hover_climb_energy_kw_hr),
    ('Rsv Trans. Climb',    ac.reserve_trans_climb_energy_kw_hr),
    ('Rsv Accel. Climb',    ac.reserve_accel_climb_energy_kw_hr),
    ('Rsv Cruise',          ac.reserve_cruise_energy_kw_hr),
    ('Rsv Decel. Descend',  ac.reserve_decel_descend_energy_kw_hr),
    ('Rsv Trans. Descend',  ac.reserve_trans_descend_energy_kw_hr),
    ('Rsv Hover Descend',   ac.reserve_hover_descend_energy_kw_hr),
]

primary_total = sum(e for _, e in primary_segments)
reserve_total = sum(e for _, e in reserve_segments)

print(f"\n{'Segment':<25s} {'Energy (kWh)':>12s}")
print("-" * 38)
for name, en in primary_segments:
    print(f"{name:<25s} {en:>12.4f}")
print("-" * 38)
for name, en in reserve_segments:
    print(f"{name:<25s} {en:>12.4f}")
print("-" * 38)
print(f"{'Primary Total':<25s} {primary_total:>12.4f}")
print(f"{'Reserve Total':<25s} {reserve_total:>12.4f}")
print(f"{'Mission Total':<25s} {primary_total + reserve_total:>12.4f}")
print(f"\nBattery Mass: {ac.battery_mass_kg:.2f} kg")


# Comparison to Reference Values
reference_values = {
    "Actual (kg)": 1752.0,
    "CTOW (kg)": 1752.0,
    "Hover power (kW)": 229.676,
    "Cruise power (kW)": 76.0614,
    "Battery weight (kg)": 330.669,
    "Cruise L/D": 10.4,
}

ptow_kg = history[0]["mtow_guess_kg"]
ctow_kg = final_mtow
hover_power_kw = ac._calc_hover_electric_power_kw()
cruise_power_kw = ac._calc_cruise_avg_electric_power_kw()
cruise_distance_km = (ac.mission.cruise_h_m_p_s * ac.mission.cruise_s) / 1000.0
cruise_energy_kwh = cruise_power_kw * (ac.mission.cruise_s / 3600.0)

sized_values = {
    "Actual (kg)": ptow_kg,
    "CTOW (kg)": ctow_kg,
    "Hover power (kW)": hover_power_kw,
    "Cruise power (kW)": cruise_power_kw,
    "Battery weight (kg)": ac.battery_mass_kg,
    "kWh/100km": (cruise_energy_kwh / (cruise_distance_km / 100.0)) if cruise_distance_km else None,
    "Cruise L/D": ac.cruise_l_p_d,
}

def percent_diff(sized, reference):
    if sized is None or reference is None or reference == 0:
        return None
    return 100.0 * (sized - reference) / reference

def fmt_val(value, width=12, precision=2):
    if value is None:
        return f"{'n/a':>{width}s}"
    return f"{value:>{width}.{precision}f}"

def fmt_pct(value, width=10, precision=1):
    if value is None:
        return f"{'n/a':>{width}s}"
    return f"{value:>{width}.{precision}f}"

print("\nComparison to Reference Values (Percent Difference) ")
print(f"{'Metric':<18s} {'Sized':>12s} {'Ref':>12s} {'% Diff':>10s}")
print("-" * 56)
for metric, ref in reference_values.items():
    sized = sized_values.get(metric)
    pct = percent_diff(sized, ref)
    precision = 3 if metric in {"Hover FoM"} else 2
    print(
        f"{metric:<18s}"
        f"{fmt_val(sized, precision=precision)}"
        f"{fmt_val(ref, precision=precision)}"
        f"{fmt_pct(pct)}"
    )