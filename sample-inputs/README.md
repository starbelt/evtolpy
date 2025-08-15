# Sample Inputs

The package software uses JSON files as input. These files specify all relevant
parameters. JSON does not support inline comments, so this README documents the
format of the input file.

## Directory Contents

* [test-environ.json](test-environ.json): A JSON file for the `Environ` class
  unit test
* [test-mission.json](test-mission.json): A JSON file for the `Mission` class
  unit test
* [test-power.json](test-power.json): A JSON file for the `Power` class unit
  test
* [test-propulsion.json](test-propulsion.json): A JSON file for the `Propulsion`
  class unit test
* [test-aircraft.json](test-aircraft.json): A JSON file for the `Aircraft` class
  unit test
* [test-all.json](test-all.json): A JSON file for testing all parameter
  specifications combined
* [README.md](README.md): This document

## Environmental Parameters

* `g_m_p_s2`: acceleration due to gravity in meters per second squared
* `sound_speed_m_p_s`: speed of sound at the maximum altitude, e.g. 5000 ft, in
  meters per second
* `air_density_sea_lvl_kg_p_m3`: air density (kg/m^3) at sea level
* `air_density_max_alt_kg_p_m3`: air density (kg/m^3) at the maximum altitude,
  e.g. 5000 ft
* `kinematic_viscosity_sea_lvl_m2_p_s`: kinematic viscosity of air (m^2/s) at
  sea level

## Mission Parameters

See page 4 of the corresponding
[reference document](../references/summary-mission-and-requirements.pdf).

Mission segments:
* `depart_taxi_avg_h_m_p_s`: departure ground taxi average horizontal meters per
  second (typical: 1.34 m/s)
* `depart_taxi_s`: departure ground taxi duration in seconds (typical: 30 s)
* `hover_climb_avg_v_m_p_s`: takeoff vertical ascent average vertical meters per
  second (typical: 2.54 m/s)
* `hover_climb_s`: takeoff vertical ascent duration in seconds (typical: 12 s)
* `trans_climb_avg_h_m_p_s`: transition from vertical ascent to horizontal
  flight; average horizontal m/s (typical: 0.6 * stall speed = 24.4 m/s)
* `trans_climb_v_m_p_s`: transition from vertical ascent to horizontal
  flight; vertical m/s (typical: 5.1 m/s)
* `trans_climb_s`: transition from vertical ascent to horizontal flight;
  duration in seconds (typical: 30 s)
* `depart_proc_h_m_p_s`: departure procedures horizontal meters per second
  (typical: 1.2 * stall speed = 48.8 m/s)
* `depart_proc_s`: departure procedures duration in seconds (typical: 18 s)
* `accel_climb_avg_h_m_p_s`: accelerate to horizontal flight while climbing
  average horizontal meters per second (typical: 58 m/s)
* `accel_climb_v_m_p_s`: accelerate to horizontal flight while climbing;
  vertical meters per second (typical: 5.1 m/s)
* `accel_climb_s`: accelerate to horizontal flight while climbing duration in
  seconds (typical: 143 s)
* `cruise_h_m_p_s`: cruise flight horizontal meters per second (typical: 67.1)
* `cruise_s`: cruise flight duration in seconds (typical: 664 s)
* `decel_descend_avg_h_m_p_s`: decelerate from horizontal flight while
  descending; average horizontal meters per second (typical: 58 m/s)
* `decel_descend_v_m_p_s`: decelerate from horizontal flight while descending;
  vertical meters per second (typical: 5.1 m/s)
* `decel_descend_s`: decelerate from horizontal flight while descending duration
  in seconds (typical: 143 s)
* `arrive_proc_h_m_p_s`: arrival procedures horizontal meters per second
  (typical: 1.2 * stall speed = 48.8 m/s)
* `arrive_proc_s`: arrival procedures duration in seconds (typical: 18 s)
* `trans_descend_avg_h_m_p_s`: transition from horizontal flight to vertical
  descent average horizontal m/s (typical: 0.6 * stall speed = 24.4 m/s)
* `trans_descend_v_m_p_s`: transition from horizontal flight to vertical descent
  vertical meters per second (typical: 5.1 m/s)
* `trans_descend_s`: transition from horizontal flight to vertical descent
  duration in seconds (typical: 30 s)
* `hover_descend_avg_v_m_p_s`: landing vertical descent average vertical meters
  per second (typical: 2.54 m/s)
* `hover_descend_s`: landing vertical descent duration in sec (typical: 12 s)
* `arrive_taxi_avg_h_m_p_s`: arrival ground taxi average horizontal meters per
  second (typical: 1.34 m/s)
* `arrive_taxi_s`: arrival ground taxi duration in seconds (typical: 30 s)
* `reserve_hover_climb_avg_v_m_p_s`: reserve takeoff vertical ascent average
  vertical meters per second (typical: 2.54 m/s)
* `reserve_hover_climb_s`: reserve takeoff vertical ascent duration in seconds
  (typical: 12 s)
* `reserve_trans_climb_avg_h_m_p_s`: reserve vertical ascent to cruise
  transition average horizontal m/s (typical: 0.6 * stall speed = 24.4 m/s)
* `reserve_trans_climb_v_m_p_s`: reserve vertical ascent to cruise transition
  vertical meters per second (typical: 5.1 m/s)
* `reserve_trans_climb_s`: reserve vertical ascent to cruise transition duration
  in seconds (typical: 30 s)
* `reserve_accel_climb_avg_h_m_p_s`: reserve accelerate to horizontal flight
  while climbing average horizontal meters per second (typical: 58 m/s)
* `reserve_accel_climb_v_m_p_s`: reserve accelerate to horizontal flight while
  climbing vertical meters per second (typical: 5.1 m/s)
* `reserve_accel_climb_s`: reserve accelerate to horizontal flight while
  climbing duration in seconds (typical: 24 s)
* `reserve_cruise_h_m_p_s`: reserve cruise flight horizontal meters per second
  (typical: 67.1 m/s)
* `reserve_cruise_s`: reserve cruise flight duration in seconds (typical: 54 s)
* `reserve_decel_descend_avg_h_m_p_s`: reserve decelerate from horizontal flight
  and descend average horizontal meters per second (typical: 58 m/s)
* `reserve_decel_descend_v_m_p_s`: reserve decelerate from horizontal flight and
  descend vertical meters per second (typical: 5.1 m/s)
* `reserve_decel_descend_s`: reserve decelerate from horizontal flight and
  descend duration in seconds (typical: 24 s)
* `reserve_trans_descend_avg_h_m_p_s`: reserve vertical descent from cruise
  transition average horizontal meters per second (typical: 0.6 * stall speed =
  24.4 m/s)
* `reserve_trans_descend_v_m_p_s`: reserve vertical descent from cruise
  transition vertical meters per second (typical: 5.1 m/s)
* `reserve_trans_descend_s`: reserve vertical descent from cruise transition
  duration in seconds (typical: 30 s)
* `reserve_hover_descend_avg_v_m_p_s`: reserve landing vertical descent average
  vertical meters per second (typical: 2.54 m/s)
* `reserve_hover_descend_s`: reserve landing vertical descent duration in
  seconds (typical: 12 s)

## Power: Electric Aircraft Parameters

* `batt_spec_energy_w_h_p_kg`: battery energy density in Watt-hours per kg
  (typical range 150 to 250)
* `batt_inaccessible_energy_frac`: fraction of battery energy that remains
  inaccessible due to, e.g., low voltage losses or equivalent series resistance
  (e.g. 0.05)
* `batt_eol_capacity`: battery end-of-life (EOL) capacity as a fraction; the
  retirement state of health (SOH) as a factor from zero to one (typical: 0.8)
* `batt_int_factor`: battery pack integration factor; accounts for battery
  system mass that does not store energy (e.g. 0.65)
* `epu_effic`: electric propulsion unit (electric engine and supporting
  components) efficiency; assumed constant for both hover and cruise (generally
  not greater than 0.9)
* `hover_power_effic`: fraction of electric hover power converted to mechanical
  power (e.g. 0.7)

## Propulsion: Rotor Aircraft Parameters

* `rotor_effic`: rotor efficiency; the ratio between the power produced by the
  rotor and the power applied (e.g. 0.8)
* `rotor_count`: number of rotors
* `rotor_diameter_m`: rotor diameter in meters
* `tip_mach`: ratio of rotor tip to speed of sound; impacts noise level
* `rotor_avg_cl`: average coefficient of lift for the rotor; thrust coefficient
  (Ct) normalized by rotor solidity (sigma) (max. 0.2; 0.125 more realistic)
  times 6 gives a theoretical upper limit for Cl

## Aircraft Parameters

* `max_takeoff_mass_kg`: maximum takeoff mass (MTOM) in kilograms
* `payload_kg`: payload mass in kilograms
* `vehicle_cl_max`: whole vehicle (not airfoil) maximum coefficient of lift
* `wing_taper_ratio`: ratio of the wingtip chord to the wing root chord
* `wingspan_m`: wingspan in meters
* `d_value_m`: largest diameter of the aircraft when the rotors are turning
* `stall_speed_m_p_s`: stall speed in meters per second
* `fuselage_l_m`: fuselage length in meters
* `fuselage_w_m`: fuselage width in meters
* `fuselage_h_m`: fuselage height in meters
* `wing_airfoil_cd_at_cruise_cl`: wing airfoil drag coefficient at cruise
* `empennage_airfoil_cd0`: tail assembly zero-lift drag coefficient
* `span_effic_factor`: wing geometry & lift distribution effect on induced drag
* `trim_drag_factor`: additional drag caused by control surfaces
* `landing_gear_drag_area_m2`: landing gear drag area in square meters
* `excres_protub_factor`: accounts for excrescence drag and protuberance drag
* `horiz_tail_vol_coeff`: horizontal tail volume coefficient
* `vert_tail_vol_coeff`: vertical tail volume coefficient
* `ratio_disk_to_stopped_rotor_area`: rotor disk area / boom drag area (i.e.,
  stopped rotor area plus any margin due to rotor boom)
* `wing_t_p_c`: wing thickness-to-chord ratio
* `actuator_mass_kg`: total mass of rotor actuators in kilograms
* `furnishings_mass_kg`: furnishings mass in kilograms
* `environmental_control_system_mass_kg`: environmental control system mass in
  kilograms
* `avionics_mass_kg`: avionics mass in kilograms
* `hivolt_power_dist_mass_kg`: high voltage power distribution mass in kilograms
* `lovolt_power_coms_mass_kg`: low voltage power and comms mass in kilograms
* `mass_margin_factor`: mass margin factor from 0.0 to 1.0 or greater; typically
  5 percent (i.e., 0.05)

### Aircraft Parameter Notes

* `max_takeoff_mass_kg`: Find, e.g. online, for the aircraft of interest
* `payload_kg`: Find, e.g. online, for the aircraft of interest
* `vehicle_cl_max`: The lift force equation defines the lift coefficient
  $C_L = \frac{2 L}{\rho u^2 S}$, where $L$ is lift force, $\rho$ is air
  density, $u$ is the aircraft speed (e.g., stall velocity), and $S$ is the wing
  area. This framework assumes the maximum coefficient of lift $C_L$ is known
  and calculates the wing area.
* `wing_taper_ratio`: Calculate the ratio of the wingtip chord to the wing root
  chord by dividing the length of the wing tip by the length of the wing where
  it attaches to the aircraft.
* `wingspan_m`: Calculate from an overhead view.
* `d_value_m`: Calculate from an overhead view.
* `stall_speed_m_p_s`: Part 23.49/23.562 requires 79 knots, i.e. 40.6 m/s
* `fuselage_l_m`: Measure from an overhead view.
* `fuselage_w_m`: Measure from an overhead view.
* `fuselage_h_m`: Measure from an overhead view.
* `wing_airfoil_cd_at_cruise_cl`: First calculate cruise lift coefficient
  $C_L = \frac{2 L}{\rho u^2 S}$ using the cruise speed for $u$. Then use the
  [NLF(1)-0414F](http://airfoiltools.com/airfoil/details?airfoil=nlf414f-il)
  model to find the corresponding Cd.
* `empennage_airfoil_cd0`: No simple way to model. Must be higher than 0.0031,
  so 0.006 is a good estimate.
* `span_effic_factor`: Different from the Oswald efficiency factor, which will
  be less than 0.9. No greater than 0.8.
* `trim_drag_factor`: Additional drag caused by control surfaces; express as a
  factor greater than 1.0.
* `landing_gear_drag_area_m2`: Calculate from a front view.
* `excres_protub_factor`: Additional drag caused by excrescence and protuberance
  expressed as a factor greater than 1.0.
* `horiz_tail_vol_coeff`: See
  [EAA Chapter 62](https://www.eaa62.org/technotes/tail.htm)
* `vert_tail_vol_coeff`: See
  [EAA Chapter 62](https://www.eaa62.org/technotes/tail.htm)
* `ratio_disk_to_stopped_rotor_area`: rotor disk area / boom drag area plus any
  margin due to rotor boom
* `wing_t_p_c`: wing thickness-to-chord ratio; typically 9 to 13 percent
