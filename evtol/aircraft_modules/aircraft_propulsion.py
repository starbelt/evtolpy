# aircraft_propulsion.py
#
# Propulsion module for aircraft model
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

# requires disk_area_m2 from propulsion
# use MTOM to calculate kg per disk area m2
# return None if propulsion object not populated
def _calc_disk_loading_kg_p_m2(aircraft):
    if aircraft.propulsion != None:
      return aircraft.max_takeoff_mass_kg/aircraft.propulsion.disk_area_m2
    else:
      return None
    
# calculates the over-torque factor for the propulsion system
# assumes rotor thrust is redistributed across remaining lift rotors
# includes a 30% transient/control margin
# uses user input when available, otherwise estimates from contingency rotor count
def _calc_over_torque_factor(aircraft):
    if aircraft.propulsion == None:
      return None
    if hasattr(aircraft.propulsion, 'over_torque_factor') and \
       aircraft.propulsion.over_torque_factor != None:
      return aircraft.propulsion.over_torque_factor

    if hasattr(aircraft.propulsion, 'lift_rotor_count') and \
       aircraft.propulsion.lift_rotor_count != None:
      rotor_count = aircraft.propulsion.lift_rotor_count
    else:
      rotor_count = aircraft.propulsion.rotor_count

    if rotor_count == None or rotor_count <= 2:
      return None

    contingency_rotor_count = rotor_count-2
    contingency_factor = rotor_count/contingency_rotor_count
    transient_margin_factor = 1.3

    return contingency_factor*transient_margin_factor
    
# estimates rotor solidity from thrust coefficient at hover
# based on MTOW, air density, rotor geometry, and tip Mach hover RPM
def _calc_rotor_solidity(aircraft):
    if aircraft.propulsion is None or aircraft.environ is None:
      return None
    else:
      # Hover RPM at sea level 
      rpm_hover_rpm = (aircraft.environ.sound_speed_m_p_s*aircraft.propulsion.tip_mach/(aircraft.propulsion.rotor_diameter_m/2.0))*60.0/(2.0*math.pi)
      omega_hover_sl_rad_s = rpm_hover_rpm*math.pi/30.0 # Convert to rad/s

      # Rotor thrust coefficient at hover 
      ct_hover = (
        (aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2/aircraft.propulsion.rotor_count)
        /(aircraft.environ.air_density_sea_lvl_kg_p_m3
          *math.pi*(aircraft.propulsion.rotor_diameter_m/2.0)**4
          *(omega_hover_sl_rad_s**2.0))
      )
      # Rotor solidity 
      rotor_solidity = ct_hover*6.0/aircraft.propulsion.rotor_avg_cl
      return rotor_solidity
  
# requires propulsion pusher_rotor_diameter_m and pusher_rotor_tip_mach
# requires environ sound_speed_m_p_s
# calculates pusher rotor RPM from tip Mach and rotor radius
# return None if required object/field not populated
def _calc_pusher_rotor_rpm(aircraft):
    if aircraft.propulsion == None or aircraft.environ == None:
      return None
    if aircraft.propulsion.pusher_rotor_count == 0:
      return 0.0
    if aircraft.propulsion.pusher_rotor_diameter_m == None or \
       aircraft.propulsion.pusher_rotor_tip_mach == None:
      return None
    else:
      return \
       (aircraft.environ.sound_speed_m_p_s*aircraft.propulsion.pusher_rotor_tip_mach/\
        (aircraft.propulsion.pusher_rotor_diameter_m/2.0))*60.0/(2.0*math.pi)

# requires aircraft cruise_avg_shaft_power_kw
# requires propulsion pusher_rotor_count
# requires aircraft pusher_rotor_rpm
# calculates single pusher motor torque [N-m] from cruise shaft power per motor
# return None if required field/object not populated
def _calc_pusher_motor_torque_nm(aircraft):
    if aircraft.propulsion == None:
      return None
    if aircraft.propulsion.pusher_rotor_count == 0:
      return 0.0
    if aircraft.pusher_rotor_rpm == None or aircraft.cruise_avg_shaft_power_kw == None:
      return None
    else:
      omega_rad_p_s = aircraft.pusher_rotor_rpm*math.pi/30.0
      if omega_rad_p_s == 0.0:
        return None
      return \
       (aircraft.cruise_avg_shaft_power_kw*1000.0/aircraft.propulsion.pusher_rotor_count)/\
       omega_rad_p_s