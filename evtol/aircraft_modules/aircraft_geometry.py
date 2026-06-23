# aircraft_geometry.py
#
# Geometry module for aircraft model
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

# requires environ air_density_max_alt_kg_p_m3
# stall speed equation solved for wing area
# return None if environ object not populated
def _calc_wing_area_m2(aircraft):
    if aircraft.environ != None:
      return \
       (2.0*aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2)/\
       (aircraft.environ.air_density_sea_lvl_kg_p_m3*(aircraft.stall_speed_m_p_s**2.0)*\
        aircraft.vehicle_cl_max)
    else:
      return None
    
# Hoerner Eq 13.1 (p 238)
def _calc_fuselage_fineness_ratio(aircraft):
    return 2.0*aircraft.fuselage_l_m/(aircraft.fuselage_w_m+aircraft.fuselage_h_m)

# requires aircraft wing_root_chord_m
# wing Mean Aerodynamic Chord formula
# return None if aircraft field not populated
def _calc_wing_mac_m(aircraft):
    if aircraft.wing_root_chord_m != None:
      return \
       (2.0/3.0)*aircraft.wing_root_chord_m*\
       (1.0+aircraft.wing_taper_ratio**2.0/(1.0+aircraft.wing_taper_ratio))
    else:
      return None

# requires aircraft wing_area_m2
# wing aspect ratio = wingspan^2/wing area
# return None if aircraft field not populated or invalid
def _calc_wing_aspect_ratio(aircraft):
    if aircraft.wing_area_m2 != None and aircraft.wingspan_m != None and \
       aircraft.wing_area_m2 > 0.0 and aircraft.wingspan_m > 0.0:
      return aircraft.wingspan_m**2.0/aircraft.wing_area_m2
    else:
      return None
    
# requires aircraft wing_area_m2
# recall wing root chord = 2*wing area/(wingspan*(1+taper ratio))
# return None if aircraft field not populated or invalid
def _calc_wing_root_chord_m(aircraft):
    if aircraft.wing_area_m2 != None and aircraft.wingspan_m != None and \
       aircraft.wing_taper_ratio != None and aircraft.wing_area_m2 > 0.0 and \
       aircraft.wingspan_m > 0.0 and (1.0+aircraft.wing_taper_ratio) != 0.0:
      return 2.0*aircraft.wing_area_m2/(aircraft.wingspan_m*(1.0+aircraft.wing_taper_ratio))
    else:
      return None

# requires aircraft wing_area_m2 and wing_mac_m
# return None if aircraft field not populated
def _calc_horiz_tail_area_m2(aircraft):
    if aircraft.wing_area_m2 != None and aircraft.wing_mac_m != None:
      return \
       (aircraft.horiz_tail_vol_coeff*aircraft.wing_area_m2*aircraft.wing_mac_m)/\
       (0.5*aircraft.fuselage_l_m)
    else:
      return None

# requires aircraft wing_area_m2
# return None if aircraft field not populated or invalid
def _calc_vert_tail_area_m2(aircraft):
    if aircraft.wing_area_m2 != None and aircraft.wingspan_m != None and \
       aircraft.fuselage_l_m != None and aircraft.wing_area_m2 > 0.0 and \
       aircraft.wingspan_m > 0.0 and aircraft.fuselage_l_m > 0.0:
      return \
       (aircraft.vert_tail_vol_coeff*aircraft.wingspan_m*aircraft.wing_area_m2)/\
       (0.5*aircraft.fuselage_l_m)
    else:
      return None

# Hoerner Eq 6.30 (p 111)
def _calc_fuselage_wetted_area_m2(aircraft):
    if aircraft.fuselage_cf != None and aircraft.wing_area_m2 != None:
      fuselage_reference_area = math.pi*((aircraft.fuselage_w_m+aircraft.fuselage_h_m)/4.0)**2.0
      return 3*aircraft.fuselage_fineness_ratio*fuselage_reference_area
    else:
      return None
  