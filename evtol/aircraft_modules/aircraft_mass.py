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
def _calc_payload_mass_frac(self):
    return self.payload_kg/self.max_takeoff_mass_kg

# Parametric EPU mass estimation model (FHE / Magicall datasheet based)
# Uses hover torque and over-torque scaling to compute motor torque at max thrust
# Scales rotor RPM to account for sea-level vs. minimum air density conditions
# Computes maximum motor power and applies empirical regression to estimate single EPU mass
def _calc_single_epu_mass_kg(self):
    if self.propulsion == None and self.environ == None:
      return None
    else:
      # Hover torque
      rpm_hover_rpm = (self.environ.sound_speed_m_p_s*self.propulsion.tip_mach/(self.propulsion.rotor_diameter_m/2.0))*60.0/(2.0*math.pi)
      omega_hover_rad_s = 2.0*math.pi*rpm_hover_rpm/60.0
      torque_hover_nm = (self.hover_shaft_power_kw*1000.0/self.propulsion.rotor_count)/omega_hover_rad_s
      torque_max_nm = self.over_torque_factor * torque_hover_nm

      # Max RPM (min density)
      rpm_hover_sl_rpm = rpm_hover_rpm  # assuming hover calc is at sea-level
      rpm_max_rpm = rpm_hover_sl_rpm*math.sqrt(self.environ.air_density_sea_lvl_kg_p_m3/self.environ.air_density_max_alt_kg_p_m3)*math.sqrt(self.over_torque_factor)
      omega_max_rad_s = 2.0*math.pi*rpm_max_rpm/60.0
      power_max_kw = (torque_max_nm*omega_max_rad_s)/1000.0

      # Empirical mass model
      return 1.15*((power_max_kw/12.67) + (torque_max_nm/52.2) + 2.55)