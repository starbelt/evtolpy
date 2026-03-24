# aircraft_mass.py
#
# Mass/Weight module for aircraft model
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

# ratio of payload mass to max takeoff mass
def _calc_payload_mass_frac(aircraft):
    return aircraft.payload_kg/aircraft.max_takeoff_mass_kg

# Parametric EPU mass estimation model (FHE / Magicall datasheet based)
# Uses hover torque and over-torque scaling to compute motor torque at max thrust
# Scales rotor RPM to account for sea-level vs. minimum air density conditions
# Computes maximum motor power and applies empirical regression to estimate single EPU mass
def _calc_single_epu_mass_kg(aircraft):
    if aircraft.propulsion == None and aircraft.environ == None:
      return None
    else:
      # Hover torque
      rpm_hover_rpm = (aircraft.environ.sound_speed_m_p_s*aircraft.propulsion.tip_mach/(aircraft.propulsion.rotor_diameter_m/2.0))*60.0/(2.0*math.pi)
      omega_hover_rad_s = 2.0*math.pi*rpm_hover_rpm/60.0
      torque_hover_nm = (aircraft.hover_shaft_power_kw*1000.0/aircraft.propulsion.rotor_count)/omega_hover_rad_s
      torque_max_nm = aircraft.over_torque_factor * torque_hover_nm

      # Max RPM (min density)
      rpm_hover_sl_rpm = rpm_hover_rpm  # assuming hover calc is at sea-level
      rpm_max_rpm = rpm_hover_sl_rpm*math.sqrt(aircraft.environ.air_density_sea_lvl_kg_p_m3/aircraft.environ.air_density_max_alt_kg_p_m3)*math.sqrt(aircraft.over_torque_factor)
      omega_max_rad_s = 2.0*math.pi*rpm_max_rpm/60.0
      power_max_kw = (torque_max_nm*omega_max_rad_s)/1000.0

      # Empirical mass model
      return 1.15*((power_max_kw/12.67) + (torque_max_nm/52.2) + 2.55)
    
# calculates battery mass [kg] from total mission energy, 
# requires battery specific energy, inaccessible energy fraction, and integration factor.
def _calc_battery_mass_kg(aircraft):
    if aircraft.power is None:
      return None
    total_energy_kw_hr = aircraft._calc_total_mission_energy_kw_hr()
    batt_accessible_energy_frac = 1-aircraft.power.batt_inaccessible_energy_frac
    if total_energy_kw_hr != None and aircraft.power != None:
      return (total_energy_kw_hr*1000.0)/(aircraft.power.batt_spec_energy_w_h_p_kg*batt_accessible_energy_frac*aircraft.power.batt_int_factor)
    else:
      return None 
    
# estimates wing structural mass [kg] using NDARC AFDD93 model 
# based on Raymer estimation and 0.9 technology factor
def _calc_wing_mass_kg(aircraft):
    max_takeoff_mass_lb = aircraft.max_takeoff_mass_kg*KG_2_LB
    wing_area_ft2 = aircraft.wing_area_m2*(M_2_FT**2)
    wing_mass_lb = (
      5.66411
      *(max_takeoff_mass_lb/1000.0)**0.847
      *(3.8*1.5)**0.39579
      *(wing_area_ft2)**0.21754
      *(aircraft.wing_aspect_ratio)**0.50016
      *((1.0+aircraft.wing_taper_ratio)/aircraft.wing_t_p_c)**0.09359
      *0.9
    )
    return wing_mass_lb/KG_2_LB

# estimates horizontal tail structural mass [kg] using NDARC model 
# based on tail area, dive speed, and 0.9 technology factor
def _calc_horiz_tail_mass_kg(aircraft):
    if aircraft.mission is None:
      return None
    horiz_tail_area_ft2 = aircraft.horiz_tail_area_m2*(M_2_FT**2)
    dive_speed_kts = 1.4*aircraft.mission.cruise_h_m_p_s*M_P_S_2_KTS
    horiz_tail_mass_lb = (
      horiz_tail_area_ft2
      *(0.00395*(horiz_tail_area_ft2**0.2)*dive_speed_kts-0.4885)
      *0.9
    )
    return horiz_tail_mass_lb/KG_2_LB

# estimates vertical tail structural mass [kg] using NDARC model 
# based on tail area, dive speed, and 0.9 technology factor
def _calc_vert_tail_mass_kg(aircraft):
    if aircraft.mission is None:
      return None
    vert_tail_area_ft2 = aircraft.vert_tail_area_m2*(M_2_FT**2)
    dive_speed_kts = 1.4*aircraft.mission.cruise_h_m_p_s*M_P_S_2_KTS
    vert_tail_mass_lb = (
        vert_tail_area_ft2
        *(0.00395*(vert_tail_area_ft2**0.2)*dive_speed_kts-0.4885)
        *0.9
    )
    return vert_tail_mass_lb/KG_2_LB

# estimates fuselage structural mass [kg] using NDARC model 
# based on wetted area, fineness ratio, dynamic pressure, and 0.9 technology factor
def _calc_fuselage_mass_kg(aircraft):
    if aircraft.mission is None or aircraft.environ is None:
      return None
    fuselage_wetted_area_ft2 = aircraft.fuselage_wetted_area_m2*(M_2_FT**2)
    max_takeoff_mass_lb = aircraft.max_takeoff_mass_kg*KG_2_LB
    fuselage_length_ft = aircraft.fuselage_l_m*0.5*M_2_FT
    cruise_speed_m_p_s = aircraft.mission.cruise_h_m_p_s
    dyn_pressure_lb_ft2 = (
        0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*(cruise_speed_m_p_s**2.0)
        *N_P_M2_2_LB_P_FT2
    )
    fuselage_mass_lb = (
        0.052
        *(fuselage_wetted_area_ft2**1.086)
        *((3.8*1.5*max_takeoff_mass_lb)**0.177)
        *(fuselage_length_ft**-0.051)
        *(aircraft.fuselage_fineness_ratio**-0.072)
        *(dyn_pressure_lb_ft2**0.241)
        *0.9
    )
    return fuselage_mass_lb/KG_2_LB
  
# estimates boom structural mass [kg] using NDARC engine support model and cowling equations
# based on EPU weight, rotor count, rotor diameter, and wing MAC
def _calc_boom_mass_kg(aircraft):
    if aircraft.propulsion is None:
      return None
    single_epu_mass_lb = aircraft.single_epu_mass_kg*KG_2_LB
    rotor_count = aircraft.propulsion.rotor_count
    rotor_diameter_m = aircraft.propulsion.rotor_diameter_m
    wing_mac_m = aircraft.wing_mac_m

    boom_mass_kg = (
      0.0412*(single_epu_mass_lb**1.1433)*(rotor_count**1.3762)/KG_2_LB
      + 6*0.2315*((1.2*rotor_diameter_m + wing_mac_m)**1.3476)
    )*2
    return boom_mass_kg

# estimates landing gear mass [kg] using NDARC simple model 
# assumes 3.25% of MTOW with factors for crashworthiness (1.14) and retractable gear (1.08)
def _calc_landing_gear_mass_kg(aircraft):
    return 0.0325*aircraft.max_takeoff_mass_kg*1.14*1.08

# estimates total electric propulsion unit (EPU) mass [kg] 
# using parametric model from FHE based on Magicall datasheet 
# scales single EPU mass by number of rotors
def _calc_epu_mass_kg(aircraft):
    if aircraft.propulsion is None:
      return None
    else:
      return aircraft.single_epu_mass_kg*aircraft.propulsion.rotor_count
    
# NDARC Section 19.2 AFDD00 rotor + hub mass model
# assumes 2-bladed rotors, flap natural frequency at 1.1 × max RPM
# returns lift rotor + hub mass [kg]
def _calc_lift_rotor_hub_mass_kg(aircraft):
    if aircraft.propulsion is None or aircraft.environ is None:
      return None
    rotor_radius_ft = (aircraft.propulsion.rotor_diameter_m / 2.0) * M_2_FT
    solidity = aircraft.rotor_solidity
    sound_speed_m_p_s = aircraft.environ.sound_speed_m_p_s
    tip_mach = aircraft.propulsion.tip_mach
    rho_sl = aircraft.environ.air_density_sea_lvl_kg_p_m3
    rho_alt = aircraft.environ.air_density_max_alt_kg_p_m3
    over_torque_factor = aircraft.over_torque_factor

    # common geometric term:
    term_common = (math.pi / 2.0/ 2.0) * aircraft.propulsion.rotor_diameter_m * solidity * M_2_FT

    tip_speed_ft_s = (
      sound_speed_m_p_s
      * tip_mach
      * math.sqrt(rho_sl / rho_alt)
      * math.sqrt(over_torque_factor)
      * M_2_FT
    )

    lift_rotor_hub_mass_lb = (
      (
        0.0024419
        * (aircraft.propulsion.lift_rotor_count)
        * (2.0 ** 0.53479)
        * (rotor_radius_ft ** 1.74231)
        * (term_common ** 0.77291)
        * (tip_speed_ft_s ** 0.87562)
        * (1.1 ** 2.51048)
      )
      + (
        0.00037547
        * (aircraft.propulsion.lift_rotor_count)
        * (2.0 ** 0.71443)
        * (rotor_radius_ft ** 1.99321)
        * (term_common ** 0.79577)
        * (tip_speed_ft_s ** 0.96323)
        * (1.1 ** 0.46203)
        * (1.1 ** 2.58473)
      )
    )
    return lift_rotor_hub_mass_lb / KG_2_LB

# NDARC Section 19.2 AFDD00 tilt rotor mass model
# assumes 3-bladed rotors, flap natural frequency at 1.1 × max RPM
# returns tilt rotor mass [kg]
def _calc_tilt_rotor_mass_kg(aircraft):
    if aircraft.propulsion is None or aircraft.environ is None:
      return None
    
    rotor_radius_ft = (aircraft.propulsion.rotor_diameter_m / 2.0) * M_2_FT
    solidity = aircraft.rotor_solidity
    sound_speed_m_p_s = aircraft.environ.sound_speed_m_p_s
    tip_mach = aircraft.propulsion.tip_mach
    rho_sl = aircraft.environ.air_density_sea_lvl_kg_p_m3
    rho_alt = aircraft.environ.air_density_max_alt_kg_p_m3
    over_torque_factor = aircraft.over_torque_factor

    # common geometric term 
    term_common = (math.pi / 2.0 / 3.0) * aircraft.propulsion.rotor_diameter_m * solidity * M_2_FT

    tip_speed_ft_s = (
      sound_speed_m_p_s
      * tip_mach
      * math.sqrt(rho_sl / rho_alt)
      * math.sqrt(over_torque_factor)
      * M_2_FT
    )

    tilt_rotor_mass_lb = (
      (
        0.0024419 * 1.1794
        * (aircraft.propulsion.tilt_rotor_count)
        * (3.0 ** 0.53479)
        * (rotor_radius_ft ** 1.74231)
        * (term_common ** 0.77291)
        * (tip_speed_ft_s ** 0.87562)
        * (1.1 ** 2.51048)
      )
      + (
        0.00037547 * (1.1794 ** 1.02958)
        * (aircraft.propulsion.tilt_rotor_count)
        * (3.0 ** 0.71443)
        * (rotor_radius_ft ** 1.99321)
        * (term_common ** 0.79577)
        * (tip_speed_ft_s ** 0.96323)
        * (1.1 ** 0.46203)
        * (1.1 ** 2.58473)
      )
    )
    return tilt_rotor_mass_lb / KG_2_LB

# estimates total pusher/cruise motor mass [kg] using Duffy et al, “Propulsion Scaling Methods in the Era of Electric Flight,” (2018)., 
# motor scaling relation based on single motor torque and number of pusher motors
# returns 0.0 if aircraft has no pusher rotors
def _calc_pusher_motor_mass_kg(aircraft):
    if aircraft.propulsion == None:
      return None
    if aircraft.propulsion.pusher_rotor_count == 0:
      return 0.0
    if aircraft.pusher_motor_torque_nm == None:
      return None
    else:
      single_motor_mass_lb = \
       (58.0/990.0)*((1.3558*aircraft.pusher_motor_torque_nm)-10.0)+2.0
      return \
       (single_motor_mass_lb*aircraft.propulsion.pusher_rotor_count)/KG_2_LB

# calculates aircraft empty mass
def _calc_empty_mass_kg(aircraft):
    structural_mass = (
      aircraft.wing_mass_kg +
      aircraft.horiz_tail_mass_kg +
      aircraft.vert_tail_mass_kg +
      aircraft.fuselage_mass_kg +
      aircraft.boom_mass_kg +
      aircraft.landing_gear_mass_kg +
      aircraft.lift_rotor_hub_mass_kg +
      aircraft.tilt_rotor_mass_kg +
      aircraft.pusher_motor_mass_kg   
    )
    subsys_mass = (
      aircraft.epu_mass_kg +
      aircraft.actuator_mass_kg +
      aircraft.furnishings_mass_kg +
      aircraft.environmental_control_system_mass_kg +
      aircraft.avionics_mass_kg +
      aircraft.hivolt_power_dist_mass_kg +
      aircraft.lovolt_power_coms_mass_kg
    )
    subtotal = structural_mass + subsys_mass
    return subtotal * (1.0 + aircraft.mass_margin_factor)

