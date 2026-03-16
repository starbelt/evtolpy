# aircraft_aero.py
#
# Aerodynamic module for aircraft model
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

# requires mission cruise_h_m_p_s
# this calculation replaces stall speed with cruise speed
# see stall speed equation
# return None if mission object not populated
def _calc_cruise_cl(aircraft):
    if aircraft.mission != None:
      return \
       (aircraft.stall_speed_m_p_s**2.0)*aircraft.vehicle_cl_max/\
       (aircraft.mission.cruise_h_m_p_s**2.0)
    else:
      return None
    
# Hoerner Eq 6.31 (p 111)
def _calc_fuselage_cd0_p_cf(aircraft):
    return \
     3.0*aircraft.fuselage_fineness_ratio+4.5/aircraft.fuselage_fineness_ratio**0.5+\
     21.0/aircraft.fuselage_fineness_ratio**2.0    

# requires environ kinematic_viscosity_max_alt_m2_p_s
# requires mission cruise_h_m_p_s
# reynolds number = velocity*length/kinematic viscosity
# return None if environ or mission object not populated
def _calc_fuselage_cruise_reynolds(aircraft):
    if aircraft.environ != None and aircraft.mission != None:
      return \
       aircraft.mission.cruise_h_m_p_s*aircraft.fuselage_l_m/\
       aircraft.environ.kinematic_viscosity_max_alt_m2_p_s
    else:
      return None

# requires aircraft fuselage_cruise_reynolds
# Prandtl-Schlichting skin friction formula
# where other additive terms are negligible in this regime
# return None if aircraft field not populated
def _calc_fuselage_cf(aircraft):
    if aircraft.fuselage_cruise_reynolds != None:
      return 0.455/math.log10(aircraft.fuselage_cruise_reynolds)**2.58
      # negligible: 
      # +0.0016*aircraft.fuselage_fineness_ratio/aircraft.fuselage_cruise_reynolds**0.4
    else:
      return None

# requires aircraft fuselage_cf and aircraft wing_area_m2
# dimensional analysis
# fuselage_cd0 = fuselage_cda/wing_area_m2
# where fuselage_cda = fuselage_cd0_p_cf*fuselage_cf*fuselage_reference_area
# where fuselage_reference_area = pi*((fuselage_w+fuselage_h)/4)**2
# return None if aircraft field not populated
def _calc_fuselage_cd0(aircraft):
    if aircraft.fuselage_cf != None and aircraft.wing_area_m2 != None:
      fuselage_reference_area = math.pi*((aircraft.fuselage_w_m+aircraft.fuselage_h_m)/4.0)**2.0
      return (
        aircraft.fuselage_cd0_p_cf*aircraft.fuselage_cf*fuselage_reference_area/aircraft.wing_area_m2
      )
    else:
      return None
    
# requires aircraft cruise_cl, wing_aspect_ratio
# induced drag coefficient equation
# return None if aircraft field not populated
def _calc_induced_drag_cdi(aircraft):
    if aircraft.cruise_cl != None and aircraft.wing_aspect_ratio != None:
      return \
       aircraft.cruise_cl**2.0/\
       (math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
    else:
      return None
    
# requires aircraft horiz_tail_area_m2
# return None if aircraft field not populated
def _calc_horiz_tail_cd0(aircraft):
    if aircraft.horiz_tail_area_m2 != None and aircraft.vert_tail_area_m2 != None:
      return (\
       aircraft.horiz_tail_area_m2/(aircraft.wing_area_m2)\
       )*aircraft.empennage_airfoil_cd0
    else:
      return None

# requires aircraft vert_tail_area_m2
# return None if aircraft field not populated
def _calc_vert_tail_cd0(aircraft):
    if aircraft.horiz_tail_area_m2 != None and aircraft.vert_tail_area_m2 != None:
      return (\
       aircraft.vert_tail_area_m2/(aircraft.wing_area_m2)\
       )*aircraft.empennage_airfoil_cd0
    else:
      return None

# requires aircraft wing_area_m2
# return None if aircraft field not populated
def _calc_landing_gear_cd0(aircraft):
    if aircraft.wing_area_m2 != None:
      return aircraft.landing_gear_drag_area_m2/aircraft.wing_area_m2
    else:
      return None

# requires aircraft wing_area_m2
# requires propulsion disk_area_m2
# return None if aircraft field or propulsion object not populated
def _calc_stopped_rotor_cd0(aircraft):
    if aircraft.wing_area_m2 != None and aircraft.propulsion.disk_area_m2 != None:
      return \
       (aircraft.propulsion.disk_area_m2/aircraft.ratio_disk_to_stopped_rotor_area)/\
       aircraft.wing_area_m2
    else:
      return None

# requires aircraft fuselage_cd0, induced_drag_cdi, horiz_tail_cd0,
# vert_tail_cd0, landing_gear_cd0, stopped_rotor_cd0
# per-component drag buildup
# return None if aircraft field(s) not populated
def _calc_cruise_cd(aircraft):
    if aircraft.fuselage_cd0 != None and aircraft.induced_drag_cdi != None and \
       aircraft.horiz_tail_cd0 != None and aircraft.vert_tail_cd0 != None and \
       aircraft.landing_gear_cd0 != None and aircraft.stopped_rotor_cd0 != None:
      return (\
       aircraft.fuselage_cd0+aircraft.wing_airfoil_cd_at_cruise_cl+\
       aircraft.induced_drag_cdi+aircraft.horiz_tail_cd0+aircraft.vert_tail_cd0+\
       aircraft.landing_gear_cd0+aircraft.stopped_rotor_cd0)*aircraft.trim_drag_factor*\
       aircraft.excres_protub_factor
    else:
      return None

# requires aircraft cruise_cl and cruise_cd
# dimensional analysis
# return None if aircraft field not populated
def _calc_cruise_l_p_d(aircraft):
    if aircraft.cruise_cl != None and aircraft.cruise_cd != None:
      return aircraft.cruise_cl/aircraft.cruise_cd
    else:
      return None

# requires aircraft fields for fuselage, empennage, landing gear, etc.
# returns total drag coefficient
def _calc_total_drag_coef(aircraft):
    if aircraft.environ == None or aircraft.wing_area_m2 == None:
      return None
    cd0_sum = 0.0
    if aircraft.fuselage_cd0 != None:
      cd0_sum += aircraft.fuselage_cd0
    if aircraft.horiz_tail_cd0 != None:
      cd0_sum += aircraft.horiz_tail_cd0
    if aircraft.vert_tail_cd0 != None:
      cd0_sum += aircraft.vert_tail_cd0
    if aircraft.landing_gear_cd0 != None:
      cd0_sum += aircraft.landing_gear_cd0
    return cd0_sum