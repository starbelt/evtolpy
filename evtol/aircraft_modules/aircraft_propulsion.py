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
    
# calculates the over-torque factor for the propulsion system.
def _calc_over_torque_factor(aircraft):
    if aircraft.propulsion == None:
      return None
    else:
      return aircraft.propulsion.rotor_count/(aircraft.propulsion.rotor_count-2)+0.3
    
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