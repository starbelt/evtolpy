# aircraft_performance.py
#
# Flight performance module for aircraft model
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

# requires environ g_m_p_s2, air_density_sea_lvl_kg_p_m3
# requires propulsion disk_area_m2, rotor_effic
# prop thrust momentum theory:_calc_hover_shaft_power_kw
#   F = change in pressure * disk area
#   change in pressure = 0.5 * air density * (v_e^2 - v_0^2); hover means v_0=0
#   so F = 0.5 * air density * v_e^2 * disk area
#   note: v_e is far-wake velocity, disk induced velocity is v_i = v_e/2
#   for hover: T = m*g = 2 * air density * disk area * v_i^2
#   induced power = T * v_i = (m*g)^(3/2) / sqrt(2 * air density * disk area)
#   therefore hover shaft power in watts is:
#   ((m*g)^1.5 / (2*air density*disk area)^0.5) / hover_power_effic
# return None if environ or power object not populated
def _calc_hover_shaft_power_kw(aircraft):
    if aircraft.environ != None and aircraft.power != None:
      return \
       ((
        (aircraft.environ.g_m_p_s2*aircraft.max_takeoff_mass_kg)**1.5/
        (2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3*\
         aircraft.propulsion.disk_area_m2)**0.5
       )/aircraft.power.hover_power_effic)/W_P_KW
    else:
      return None

# requires aircraft hover_shaft_power_kw
# requires power epu_effic
# scale hover_shaft_power by epu_effic
# return None if aircraft field or power object not populated
def _calc_hover_electric_power_kw(aircraft):
    if aircraft.hover_shaft_power_kw != None and aircraft.power != None:
      return aircraft.hover_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# calculates total energy required for the mission
def _calc_total_mission_energy_kw_hr(aircraft):
    segments = [
      aircraft.depart_taxi_energy_kw_hr,
      aircraft.hover_climb_energy_kw_hr,
      aircraft.trans_climb_energy_kw_hr,
      aircraft.depart_proc_energy_kw_hr,
      aircraft.accel_climb_energy_kw_hr,
      aircraft.cruise_energy_kw_hr,
      aircraft.decel_descend_energy_kw_hr,
      aircraft.arrive_proc_energy_kw_hr,
      aircraft.trans_descend_energy_kw_hr,
      aircraft.hover_descend_energy_kw_hr,
      aircraft.arrive_taxi_energy_kw_hr,
      aircraft.reserve_hover_climb_energy_kw_hr,
      aircraft.reserve_trans_climb_energy_kw_hr,
      aircraft.reserve_accel_climb_energy_kw_hr,
      aircraft.reserve_cruise_energy_kw_hr,
      aircraft.reserve_decel_descend_energy_kw_hr,
      aircraft.reserve_trans_descend_energy_kw_hr,
      aircraft.reserve_hover_descend_energy_kw_hr,
    ]
    total_energy_kw_hr = sum(e for e in segments if e is not None)
    if total_energy_kw_hr > 0:
      return total_energy_kw_hr  
    else:
      return None

# calculates total energy required for the mission
def _calc_total_reserve_mission_energy_kw_hr(aircraft):
    segments = [
      aircraft.reserve_hover_climb_energy_kw_hr,
      aircraft.reserve_trans_climb_energy_kw_hr,
      aircraft.reserve_accel_climb_energy_kw_hr,
      aircraft.reserve_cruise_energy_kw_hr,
      aircraft.reserve_decel_descend_energy_kw_hr,
      aircraft.reserve_trans_descend_energy_kw_hr,
      aircraft.reserve_hover_descend_energy_kw_hr,
    ]
    total_reserve_energy_kw_hr = sum(e for e in segments if e is not None)
    if total_reserve_energy_kw_hr > 0:
      return total_reserve_energy_kw_hr  
    else:
      return None

# ----- Depart Taxi (Segment A) -----
# requires mission depart_taxi_avg_h_m_p_s, depart_taxi_s
# horizontal power component only, assumes drag effects are negligible
# initial horizontal velocity = 0, accelerates to final velocity
# average velocity provided → used to find displacement, acceleration, and final velocity
# then use MTOM, acceleration, and average velocity to find average shaft power
# return None if mission object not populated
def _calc_depart_taxi_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None:
      d_h_m = aircraft.mission.depart_taxi_avg_h_m_p_s*aircraft.mission.depart_taxi_s
      vf_h_m_p_s = (2.0*d_h_m)/aircraft.mission.depart_taxi_s
      a_h_m_p_s2 = vf_h_m_p_s**2.0/(2.0*d_h_m)
      return \
       (aircraft.max_takeoff_mass_kg*a_h_m_p_s2*\
        aircraft.mission.depart_taxi_avg_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft depart_taxi_avg_shaft_power_kw
# requires power epu_effic
# scale depart_taxi_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_depart_taxi_avg_electric_power_kw(aircraft):
    if aircraft.depart_taxi_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.depart_taxi_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft depart_taxi_avg_electric_power_kw
# requires mission depart_taxi_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_depart_taxi_energy_kw_hr(aircraft):
    if aircraft.depart_taxi_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.depart_taxi_avg_electric_power_kw*aircraft.mission.depart_taxi_s)/\
       S_P_HR
    else:
      return None

# ----- Hover Climb (Segment B) -----
# requires mission hover_climb_avg_v_m_p_s, hover_climb_s
# vertical power component only, assumes drag effects are negligible
# initial vertical velocity = 0, accelerates to final velocity based on average climb rate
# average velocity provided → used to find displacement, acceleration, and final velocity
# includes both the induced hover power (to balance weight) and the additional power 
# required for vertical acceleration during climb
# return None if mission or propulsion object not populated
def _calc_hover_climb_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None:
        
        # vertical kinematics (upward positive)
        d_v_m = aircraft.mission.hover_climb_avg_v_m_p_s*aircraft.mission.hover_climb_s
        vf_v_m_p_s = (2.0*d_v_m)/aircraft.mission.hover_climb_s
        a_v_m_p_s2 = vf_v_m_p_s**2.0/(2.0*d_v_m)

        # required vertical thurst (from Newton's 2nd law)
        T_required_N = aircraft.max_takeoff_mass_kg*(aircraft.environ.g_m_p_s2+a_v_m_p_s2)

        # induced velocity in hover (prop thrust momentum theory)
        v_i_hover = math.sqrt(T_required_N/\
                              (2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.propulsion.disk_area_m2))

        # induced power (hover)
        P_hover_W = T_required_N*v_i_hover

        return P_hover_W/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
        return None

# requires aircraft hover_climb_avg_shaft_power_kw
# requires power epu_effic
# scale hover_climb_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_hover_climb_avg_electric_power_kw(aircraft):
    if aircraft.hover_climb_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.hover_climb_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft hover_climb_avg_electric_power_kw
# requires mission hover_climb_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_hover_climb_energy_kw_hr(aircraft):
    if aircraft.hover_climb_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.hover_climb_avg_electric_power_kw*aircraft.mission.hover_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Transition Climb (Segment C) -----
# requires mission trans_climb_avg_h_m_p_s, trans_climb_v_m_p_s, trans_climb_s
# includes aerodynamic lift, induced drag, parasite drag, weight, hover-induced power, and climb forces
# horizontal velocity: initial = 0, accelerates to final velocity
# average horizontal velocity provided → used to find displacement, acceleration, and final velocity
# vertical velocity: constant throughout (no vertical acceleration)
# return None if mission, propulsion, or environment object not populated
def _calc_trans_climb_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.trans_climb_avg_h_m_p_s**2.0
      theta = math.atan2(aircraft.mission.trans_climb_v_m_p_s, aircraft.mission.trans_climb_avg_h_m_p_s)

      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n*math.cos(theta)
      vehicle_cl = lift_n/(q*aircraft.wing_area_m2)

      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # horizontal acceleration
      v0_h_m_p_s = 0.0
      vf_h_m_p_s = 2.0*aircraft.mission.trans_climb_avg_h_m_p_s
      d_h_m = aircraft.mission.trans_climb_avg_h_m_p_s*aircraft.mission.trans_climb_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)
        
      # vertical component (constant velocity, no acceleration)
      a_v_m_p_s2 = 0.0

      # required vertical thrust from rotors (Newton's 2nd law with lift)
      T_required_N = max(0.0, weight_n - lift_n + aircraft.max_takeoff_mass_kg*a_v_m_p_s2)

      # induced velocity in transition (momentum theory)
      v_i_hover = math.sqrt(T_required_N/(2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.propulsion.disk_area_m2))

      # induced power (hover assist)
      P_hover_W = T_required_N*v_i_hover

      # horizontal force component
      force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2

      # total shaft power
      return (P_hover_W + force_h_n*aircraft.mission.trans_climb_avg_h_m_p_s) / \
            (aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None
    
# requires aircraft trans_climb_avg_shaft_power_kw
# requires power epu_effic
# scale trans_climb_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_trans_climb_avg_electric_power_kw(aircraft):
    if aircraft.trans_climb_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.trans_climb_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft trans_climb_avg_electric_power_kw
# requires mission trans_climb_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_trans_climb_energy_kw_hr(aircraft):
    if aircraft.trans_climb_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.trans_climb_avg_electric_power_kw*aircraft.mission.trans_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Depart Procedures (Segment D) -----
# requires mission depart_proc_h_m_p_s, depart_proc_s
# horizontal power component only, assumes constant velocity
# vertical motion neglected (lift = weight)
# includes aerodynamic lift, induced drag, parasite drag, and horizontal drag
# return None if mission, propulsion, or environment object not populated
def _calc_depart_proc_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.depart_proc_h_m_p_s**2.0
      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n
      
      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # force components 
      force_h_n = total_drag_n

      return (force_h_n*aircraft.mission.depart_proc_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft depart_proc_avg_shaft_power_kw
# requires power epu_effic
# scale depart_proc_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_depart_proc_avg_electric_power_kw(aircraft):
    if aircraft.depart_proc_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.depart_proc_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft depart_proc_avg_electric_power_kw
# requires mission depart_proc_s
# calculate total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_depart_proc_energy_kw_hr(aircraft):
    if aircraft.depart_proc_avg_electric_power_kw != None and aircraft.mission != None:
      return (aircraft.depart_proc_avg_electric_power_kw*aircraft.mission.depart_proc_s)/S_P_HR
    else:
      return None

# ----- Accelerate Climb (Segment E) -----
# requires mission accel_climb_avg_h_m_p_s, accel_climb_v_m_p_s, accel_climb_s
# includes aerodynamic lift, induced drag, parasite drag, weight, horizontal and vertical accelerations
# horizontal velocity: initial = depart_proc_h_m_p_s, average velocity provided → used to compute final velocity
# vertical velocity: initial = 0, accelerates to accel_climb_v_m_p_s
# return None if mission, propulsion, or environment object not populated
def _calc_accel_climb_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.accel_climb_avg_h_m_p_s**2.0
      theta = math.atan2(aircraft.mission.accel_climb_v_m_p_s, aircraft.mission.accel_climb_avg_h_m_p_s)

      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n*math.cos(theta)
      vehicle_cl = lift_n/(q*aircraft.wing_area_m2)

      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = aircraft.mission.depart_proc_h_m_p_s
      vf_h_m_p_s = 2.0*aircraft.mission.accel_climb_avg_h_m_p_s-v0_h_m_p_s
      d_h_m = aircraft.mission.accel_climb_avg_h_m_p_s*aircraft.mission.accel_climb_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical accelerations
      v0_v_m_p_s = 0.0
      vf_v_m_p_s = aircraft.mission.accel_climb_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*aircraft.mission.accel_climb_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)+aircraft.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_h_n*aircraft.mission.accel_climb_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft accel_climb_avg_shaft_power_kw
# requires power epu_effic
# scale accel_climb_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_accel_climb_avg_electric_power_kw(aircraft):
    if aircraft.accel_climb_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.accel_climb_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft accel_climb_avg_electric_power_kw
# requires mission accel_climb_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_accel_climb_energy_kw_hr(aircraft):
    if aircraft.accel_climb_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.accel_climb_avg_electric_power_kw*aircraft.mission.accel_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Cruise (Segment F) -----
# requires mission cruise_h_m_p_s, cruise_s
# horizontal power component only, assumes constant velocity
# vertical motion neglected (lift = weight)
# includes aerodynamic lift, induced drag, parasite drag, and horizontal drag
# return None if mission, propulsion, or environment object not populated
def _calc_cruise_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_max_alt_kg_p_m3*aircraft.mission.cruise_h_m_p_s**2.0
      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n
      
      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      if aircraft.wing_airfoil_cd_at_cruise_cl != None and aircraft.stopped_rotor_cd0 != None:
        cd0_cruise = cd0+aircraft.wing_airfoil_cd_at_cruise_cl+aircraft.stopped_rotor_cd0
      else:
        cd0_cruise = cd0
      dp_n = q*aircraft.wing_area_m2*cd0_cruise
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      return (total_drag_n*aircraft.mission.cruise_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft cruise_shaft_power_kw
# requires power epu_effic
# scale cruise_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_cruise_avg_electric_power_kw(aircraft):
    if aircraft.cruise_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.cruise_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None
    
# requires aircraft cruise_avg_electric_power_kw
# requires mission cruise_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_cruise_energy_kw_hr(aircraft):
    if aircraft.cruise_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.cruise_avg_electric_power_kw*aircraft.mission.cruise_s)/\
       S_P_HR
    else:
      return None

# ----- Decelerate Descend (Segment G) -----
# requires mission decel_descend_avg_h_m_p_s, decel_descend_v_m_p_s, decel_descend_s
# includes aerodynamic lift, induced drag, parasite drag, weight, horizontal deceleration, vertical thrust assist if gravity is insufficient, and spoiler drag if power is negative
# horizontal velocity: initial = cruise_h_m_p_s, average velocity provided → used to compute final velocity
# vertical velocity: initial = 0, accelerates to decel_descend_v_m_p_s (downwards)
# provide vertical thrust assist and spoiler drag (if needed)
# return None if mission, propulsion, or environment object not populated
def _calc_decel_descend_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:     
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.decel_descend_avg_h_m_p_s**2.0
      theta = math.atan2(aircraft.mission.decel_descend_v_m_p_s, aircraft.mission.decel_descend_avg_h_m_p_s)

      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n*math.cos(theta)
      vehicle_cl = lift_n/(q*aircraft.wing_area_m2)

      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = aircraft.mission.cruise_h_m_p_s
      vf_h_m_p_s = 2.0*aircraft.mission.decel_descend_avg_h_m_p_s-v0_h_m_p_s
      d_h_m = aircraft.mission.decel_descend_avg_h_m_p_s*aircraft.mission.decel_descend_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m) 

      # vertical accelerations
      v0_v_m_p_s = 0.0
      vf_v_m_p_s = aircraft.mission.decel_descend_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*aircraft.mission.decel_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)-aircraft.max_takeoff_mass_kg*a_v_m_p_s2 # physical: downward, speeding up

      # compute shaft power baseline
      shaft_power_kw = (force_h_n*aircraft.mission.decel_descend_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(aircraft.propulsion.rotor_effic*W_P_KW)

      # check vertical deficit: if gravity cannot provide enough, add vertical thrust assist shaft power
      vertical_deficit_n = aircraft.max_takeoff_mass_kg*a_v_m_p_s2-(weight_n-lift_n)
      shaft_power_deficit_kw = 0.0
      if vertical_deficit_n > 0.0:
        shaft_power_deficit_kw = (vertical_deficit_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(aircraft.propulsion.rotor_effic*W_P_KW)

      # total shaft power (baseline + vertical assist)
      shaft_power_kw += shaft_power_deficit_kw

      # check for negative power to add spoiler drag
      if shaft_power_kw < 0.0:
        # required additional horizontal force to neutralize negative power
        required_extra_force_n = -force_h_n
        # compute equivalent delta Cd
        delta_cd_spoiler = required_extra_force_n/(q*aircraft.wing_area_m2)
        if delta_cd_spoiler < 0.0:
          delta_cd_spoiler = 0.0
        # recompute with spoilers
        dp_spoiler_n = q*aircraft.wing_area_m2*delta_cd_spoiler
        total_drag_n = (di_n+dp_n+dp_spoiler_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor
        force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2

        # total shaft power (with spoiler drag and vertical assist)
        shaft_power_kw = (force_h_n*aircraft.mission.decel_descend_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(aircraft.propulsion.rotor_effic*W_P_KW) + shaft_power_deficit_kw

      return shaft_power_kw
    else:
      return None

# requires aircraft decel_descend_avg_shaft_power_kw
# requires power epu_effic
# scale decel_descend_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_decel_descend_avg_electric_power_kw(aircraft):
    if aircraft.decel_descend_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.decel_descend_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft decel_descend_avg_electric_power_kw
# requires mission decel_descend_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_decel_descend_energy_kw_hr(aircraft):
    if aircraft.decel_descend_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.decel_descend_avg_electric_power_kw*aircraft.mission.decel_descend_s)/\
       S_P_HR
    else:
      return None

# ----- Arrive Procedures (Segment H) -----
# requires mission arrive_proc_h_m_p_s, arrive_proc_s
# horizontal power component only, assumes constant velocity
# vertical motion neglected (lift = weight)
# includes aerodynamic lift, induced drag, parasite drag, and horizontal drag
# return None if mission, propulsion, or environment object not populated
def _calc_arrive_proc_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.arrive_proc_h_m_p_s**2.0
      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      # horizontal component
      lift_n = weight_n
      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # force components
      force_h_n = total_drag_n

      return (force_h_n*aircraft.mission.arrive_proc_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft arrive_proc_avg_shaft_power_kw
# requires power epu_effic
# scale arrive_proc_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_arrive_proc_avg_electric_power_kw(aircraft):
    if aircraft.arrive_proc_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.arrive_proc_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft arrive_proc_avg_electric_power_kw
# requires mission arrive_proc_s
# calculate total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_arrive_proc_energy_kw_hr(aircraft):
    if aircraft.arrive_proc_avg_electric_power_kw != None and aircraft.mission != None:
      return (aircraft.arrive_proc_avg_electric_power_kw*aircraft.mission.arrive_proc_s)/S_P_HR
    else:
      return None

# ----- Transition Descend (Segment I) -----  
# requires mission trans_descend_avg_h_m_p_s, trans_descend_v_m_p_s, trans_descend_s
# includes aerodynamic lift, induced drag, parasite drag, weight, descent forces,
# hover-induced thrust assist if gravity is insufficient, and spoiler drag if power is negative
# horizontal velocity: initial estimated from average, final = 0 (vehicle decelerates to stop)
# vertical velocity: initial = decel_descend_v_m_p_s, final = trans_descend_v_m_p_s
# return None if mission, propulsion, or environment object not populated
def _calc_trans_descend_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.trans_descend_avg_h_m_p_s**2.0
      theta = math.atan2(aircraft.mission.trans_descend_v_m_p_s, aircraft.mission.trans_descend_avg_h_m_p_s)

      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n*math.cos(theta)
      vehicle_cl = lift_n/(q*aircraft.wing_area_m2)

      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # horizontal acceleration (vehicle decelerates to stop)
      v0_h_m_p_s = 2.0*aircraft.mission.trans_descend_avg_h_m_p_s
      vf_h_m_p_s = 0.0
      d_h_m = aircraft.mission.trans_descend_avg_h_m_p_s*aircraft.mission.trans_descend_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical acceleration
      v0_v_m_p_s = aircraft.mission.decel_descend_v_m_p_s
      vf_v_m_p_s = aircraft.mission.trans_descend_v_m_p_s
      d_v_m = 0.5*(abs(v0_v_m_p_s)+abs(vf_v_m_p_s))*aircraft.mission.trans_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0 - v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # horizontal force component
      force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2

      # required vertical thrust from rotors (Newton's 2nd law with lift)
      T_req_n = max(0.0, (weight_n - lift_n) + aircraft.max_takeoff_mass_kg*a_v_m_p_s2)

      # induced velocity (momentum theory)
      v_i_hover = math.sqrt(T_req_n/(2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.propulsion.disk_area_m2))

      # hover-induced (assist) power
      P_hover_W = T_req_n*v_i_hover

      # baseline shaft power (vertical assist + horizontal forces)
      shaft_power_kw = (P_hover_W+force_h_n*aircraft.mission.trans_descend_avg_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
      
      # check for negative power → apply spoiler drag to dissipate excess
      if shaft_power_kw < 0.0:
        required_extra_force_n = -force_h_n
        delta_cd_spoiler = required_extra_force_n/(q*aircraft.wing_area_m2)
        if delta_cd_spoiler < 0.0:
          delta_cd_spoiler = 0.0
        dp_spoiler_n = q*aircraft.wing_area_m2*delta_cd_spoiler
        total_drag_n = (di_n+dp_n+dp_spoiler_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor
        force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2

        # recompute total shaft power with spoiler drag
        shaft_power_kw = (P_hover_W+force_h_n*aircraft.mission.trans_descend_avg_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)

      return shaft_power_kw
    else:
      return None

# requires aircraft trans_descend_avg_shaft_power_kw
# requires power epu_effic
# scale trans_descend_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_trans_descend_avg_electric_power_kw(aircraft):
    if aircraft.trans_descend_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.trans_descend_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft trans_descend_avg_electric_power_kw
# requires mission trans_descend_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_trans_descend_energy_kw_hr(aircraft):
    if aircraft.trans_descend_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.trans_descend_avg_electric_power_kw*aircraft.mission.trans_descend_s)/\
       S_P_HR
    else:
      return None

# ----- Hover Descend (Segment J) -----
# requires mission hover_descend_avg_v_m_p_s, hover_descend_s
# vertical power component only, assumes drag effects are negligible
# initial vertical velocity = 2*avg (downward), final = 0.0
# upward positive convention → acceleration is negative
# compute induced power from actual thrust
# return None if mission, propulsion, or environment object not populated
def _calc_hover_descend_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
        
        # vertical kinematics (upward positive)
        v0_v_m_p_s = 2.0*aircraft.mission.hover_descend_avg_v_m_p_s
        vf_v_m_p_s = 0.0
        d_v_m = aircraft.mission.hover_descend_avg_v_m_p_s*aircraft.mission.hover_descend_s
        a_v_m_p_s2 = (vf_v_m_p_s**2.0 - v0_v_m_p_s**2.0) / (2.0*d_v_m)

        # required thrust (Newton's 2nd law, upward positive)
        T_required_N = max(0.0, aircraft.max_takeoff_mass_kg * (aircraft.environ.g_m_p_s2 + a_v_m_p_s2))

        # induced velocity in hover (momentum theory)
        v_i_hover = math.sqrt(T_required_N / \
                              (2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3 * aircraft.propulsion.disk_area_m2))

        # induced power from actual thrust
        P_hover_W = T_required_N * v_i_hover

        # total shaft power (apply rotor efficiency once)
        return P_hover_W / (aircraft.propulsion.rotor_effic * W_P_KW)
    else:
        return None

# requires aircraft hover_descend_avg_shaft_power_kw
# requires power epu_effic
# scale hover_descend_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_hover_descend_avg_electric_power_kw(aircraft):
    if aircraft.hover_descend_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.hover_descend_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft hover_descend_avg_electric_power_kw
# requires mission hover_descend_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_hover_descend_energy_kw_hr(aircraft):
    if aircraft.hover_descend_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.hover_descend_avg_electric_power_kw*aircraft.mission.hover_descend_s)/\
       S_P_HR
    else:
      return None

# ----- Arrive Taxi (Segment K) -----
# requires mission arrive_taxi_avg_h_m_p_s, arrive_taxi_s
# horizontal motion only: initial velocity = 0.0, final = 2*avg
# includes horizontal acceleration effects (drag neglected)
# return None if mission, propulsion, or environment object not populated
def _calc_arrive_taxi_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      # horizontal accelerations
      v0_h_m_p_s = 0.0
      vf_h_m_p_s = 2.0*aircraft.mission.arrive_taxi_avg_h_m_p_s
      d_h_m = aircraft.mission.arrive_taxi_avg_h_m_p_s*aircraft.mission.arrive_taxi_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)
      
      # horizontal force 
      force_h_n = aircraft.max_takeoff_mass_kg*a_h_m_p_s2

      return (force_h_n*aircraft.mission.arrive_taxi_avg_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft arrive_taxi_avg_shaft_power_kw
# requires power epu_effic
# scale arrive_taxi_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_arrive_taxi_avg_electric_power_kw(aircraft):
    if aircraft.arrive_taxi_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.arrive_taxi_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft arrive_taxi_avg_electric_power_kw
# requires mission arrive_taxi_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_arrive_taxi_energy_kw_hr(aircraft):
    if aircraft.arrive_taxi_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.arrive_taxi_avg_electric_power_kw*aircraft.mission.arrive_taxi_s)/\
       S_P_HR
    else:
      return None
    
# ----- Reserve Hover Climb (Segment B') -----
# requires mission reserve_hover_climb_avg_v_m_p_s, reserve_hover_climb_s
# vertical power component only, assumes drag effects are negligible
# initial vertical velocity = 0, accelerates to final velocity based on average climb rate
# average velocity provided → used to find displacement, acceleration, and final velocity
# includes both the induced hover power (to balance weight) and the additional power 
# required for vertical acceleration during reserve hover climb
# return None if mission or propulsion object not populated
def _calc_reserve_hover_climb_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None:
        
        # vertical kinematics (upward positive)
        d_v_m = aircraft.mission.reserve_hover_climb_avg_v_m_p_s*aircraft.mission.reserve_hover_climb_s
        vf_v_m_p_s = (2.0*d_v_m)/aircraft.mission.reserve_hover_climb_s
        a_v_m_p_s2 = vf_v_m_p_s**2.0/(2.0*d_v_m)
        
        # required vertical thurst (from Newton's 2nd law)
        T_required_N = aircraft.max_takeoff_mass_kg*(aircraft.environ.g_m_p_s2+a_v_m_p_s2)

        # induced velocity in hover (prop thrust momentum theory)
        v_i_hover = math.sqrt(T_required_N/\
                              (2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.propulsion.disk_area_m2))

        # induced power (hover)
        P_hover_W = T_required_N*v_i_hover

        return P_hover_W/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
        return None

# requires aircraft reserve_hover_climb_avg_shaft_power_kw
# requires power epu_effic
# scale reserve_hover_climb_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_reserve_hover_climb_avg_electric_power_kw(aircraft):
    if aircraft.reserve_hover_climb_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.reserve_hover_climb_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None
      
# requires aircraft reserve_hover_climb_avg_electric_power_kw
# requires mission reserve_hover_climb_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_reserve_hover_climb_energy_kw_hr(aircraft):
    if aircraft.reserve_hover_climb_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.reserve_hover_climb_avg_electric_power_kw*aircraft.mission.reserve_hover_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Transition Climb (Segment C') -----
# requires mission reserve_trans_climb_avg_h_m_p_s, reserve_trans_climb_v_m_p_s, reserve_trans_climb_s
# includes aerodynamic lift, induced drag, parasite drag, weight, hover-induced power, and climb forces
# horizontal velocity: initial = 0, average horizontal velocity provided → used to find displacement and final velocity
# vertical velocity: constant throughout the segment (no vertical acceleration)
# return None if mission, propulsion, or environment object not populated
def _calc_reserve_trans_climb_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.reserve_trans_climb_avg_h_m_p_s**2.0
      theta = math.atan2(aircraft.mission.reserve_trans_climb_v_m_p_s, aircraft.mission.reserve_trans_climb_avg_h_m_p_s)

      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n*math.cos(theta)
      vehicle_cl = lift_n/(q*aircraft.wing_area_m2)

      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # horizontal acceleration
      v0_h_m_p_s = 0.0
      vf_h_m_p_s = 2.0*aircraft.mission.reserve_trans_climb_avg_h_m_p_s
      d_h_m = aircraft.mission.reserve_trans_climb_avg_h_m_p_s*aircraft.mission.reserve_trans_climb_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical component (constant velocity, no acceleration)
      a_v_m_p_s2 = 0.0

      # required vertical thrust from rotors (Newton's 2nd law with lift)
      T_required_N = max(0.0, weight_n - lift_n + aircraft.max_takeoff_mass_kg*a_v_m_p_s2)

      # induced velocity in transition (momentum theory)
      v_i_hover = math.sqrt(T_required_N/(2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.propulsion.disk_area_m2))

      # induced power (hover assist)
      P_hover_W = T_required_N*v_i_hover

      # horizontal force component
      force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2

      # total shaft power
      return (P_hover_W + force_h_n*aircraft.mission.reserve_trans_climb_avg_h_m_p_s) / \
            (aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft reserve_trans_climb_avg_shaft_power_kw
# requires power epu_effic
# scale reserve_trans_climb_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_reserve_trans_climb_avg_electric_power_kw(aircraft):
    if aircraft.reserve_trans_climb_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.reserve_trans_climb_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft reserve_trans_climb_avg_electric_power_kw
# requires mission reserve_trans_climb_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_reserve_trans_climb_energy_kw_hr(aircraft):
    if aircraft.reserve_trans_climb_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.reserve_trans_climb_avg_electric_power_kw*aircraft.mission.reserve_trans_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Acceleration Climb (Segment E') -----
# requires mission reserve_accel_climb_avg_h_m_p_s, reserve_accel_climb_v_m_p_s, reserve_accel_climb_s
# includes aerodynamic lift, induced drag, parasite drag, weight, and climb forces
# horizontal velocity: initial = final of Reserve Transition Climb (2*reserve_trans_climb_avg_h_m_p_s),
# vertical velocity: constant throughout the segment (no vertical acceleration)
# return None if mission, propulsion, or environment object not populated
def _calc_reserve_accel_climb_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.reserve_accel_climb_avg_h_m_p_s**2.0
      theta = math.atan2(aircraft.mission.reserve_accel_climb_v_m_p_s, aircraft.mission.reserve_accel_climb_avg_h_m_p_s)

      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n*math.cos(theta)
      vehicle_cl = lift_n/(q*aircraft.wing_area_m2)

      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor
      
      # horizontal accelerations
      v0_h_m_p_s = 2.0*aircraft.mission.reserve_trans_climb_avg_h_m_p_s
      vf_h_m_p_s = 2.0*aircraft.mission.reserve_accel_climb_avg_h_m_p_s-v0_h_m_p_s
      d_h_m = aircraft.mission.reserve_accel_climb_avg_h_m_p_s*aircraft.mission.reserve_accel_climb_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical component (constant velocity, no acceleration)
      a_v_m_p_s2 = 0.0

      # force components
      force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)+aircraft.max_takeoff_mass_kg*a_v_m_p_s2
      return (force_h_n*aircraft.mission.reserve_accel_climb_avg_h_m_p_s+force_v_n*aircraft.mission.reserve_accel_climb_v_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft reserve_accel_climb_avg_shaft_power_kw
# requires power epu_effic
# scale reserve_accel_climb_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_reserve_accel_climb_avg_electric_power_kw(aircraft):
    if aircraft.reserve_accel_climb_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.reserve_accel_climb_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft reserve_accel_climb_avg_electric_power_kw
# requires mission reserve_accel_climb_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_reserve_accel_climb_energy_kw_hr(aircraft):
    if aircraft.reserve_accel_climb_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.reserve_accel_climb_avg_electric_power_kw*aircraft.mission.reserve_accel_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Cruise (Segment F') -----
# requires mission reserve_cruise_h_m_p_s, reserve_cruise_s
# horizontal power component only
# includes aerodynamic lift, induced drag, parasite drag, weight, and horizontal motion
# return None if mission, propulsion, or environment object not populated
def _calc_reserve_cruise_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_max_alt_kg_p_m3*aircraft.mission.reserve_cruise_h_m_p_s**2.0
      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n
      
      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      if aircraft.wing_airfoil_cd_at_cruise_cl != None and aircraft.stopped_rotor_cd0 != None:
        cd0_cruise = cd0+aircraft.wing_airfoil_cd_at_cruise_cl+aircraft.stopped_rotor_cd0
      else:
        cd0_cruise = cd0
      dp_n = q*aircraft.wing_area_m2*cd0_cruise
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      return (total_drag_n*aircraft.mission.reserve_cruise_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
    else:
      return None

# requires aircraft reserve_cruise_shaft_power_kw
# requires power epu_effic
# scale reserve_cruise_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_reserve_cruise_avg_electric_power_kw(aircraft):
    if aircraft.reserve_cruise_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.reserve_cruise_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None
    
# requires aircraft reserve_cruise_avg_electric_power_kw
# requires mission reserve_cruise_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_reserve_cruise_energy_kw_hr(aircraft):
    if aircraft.reserve_cruise_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.reserve_cruise_avg_electric_power_kw*aircraft.mission.reserve_cruise_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Deceleration Descend (Segment G') -----
# requires mission reserve_decel_descend_avg_h_m_p_s, reserve_decel_descend_v_m_p_s, reserve_decel_descend_s
# includes aerodynamic lift, induced drag, parasite drag, weight, descend forces, and vertical thrust assist if gravity is insufficient
# provide vertical thrust assist and spoiler drag (if needed)
# return None if mission, propulsion, or environment object not populated
def _calc_reserve_decel_descend_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.reserve_decel_descend_avg_h_m_p_s**2.0
      theta = math.atan2(aircraft.mission.reserve_decel_descend_v_m_p_s, aircraft.mission.reserve_decel_descend_avg_h_m_p_s)

      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n*math.cos(theta)
      vehicle_cl = lift_n/(q*aircraft.wing_area_m2)

      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = aircraft.mission.reserve_cruise_h_m_p_s
      vf_h_m_p_s = 2.0*aircraft.mission.reserve_decel_descend_avg_h_m_p_s-v0_h_m_p_s
      d_h_m = aircraft.mission.reserve_decel_descend_avg_h_m_p_s*aircraft.mission.reserve_decel_descend_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical acceleration 
      v0_v_m_p_s = 0.0
      vf_v_m_p_s = aircraft.mission.reserve_decel_descend_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*aircraft.mission.reserve_decel_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)-aircraft.max_takeoff_mass_kg*a_v_m_p_s2 # physical: downward, speeding up

      # compute shaft power baseline
      shaft_power_kw = (force_h_n*aircraft.mission.reserve_decel_descend_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(aircraft.propulsion.rotor_effic*W_P_KW)
      
      # check vertical deficit: if gravity cannot provide enough, add vertical thrust assist shaft power
      vertical_deficit_n = aircraft.max_takeoff_mass_kg*a_v_m_p_s2-(weight_n-lift_n)
      shaft_power_deficit_kw = 0.0
      if vertical_deficit_n > 0.0:
        # convert deficit to power explicitly
        shaft_power_deficit_kw = (vertical_deficit_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(aircraft.propulsion.rotor_effic*W_P_KW)
      
      # total shaft power (baseline + vertical assist)
      shaft_power_kw += shaft_power_deficit_kw

      # check for negative power to add spoiler drag
      if shaft_power_kw < 0.0:
        # required additional horizontal force to neutralize negative power
        required_extra_force_n = -force_h_n
        # compute equivalent delta Cd
        delta_cd_spoiler = required_extra_force_n/(q*aircraft.wing_area_m2)
        if delta_cd_spoiler < 0.0:
          delta_cd_spoiler = 0.0
        # recompute with spoilers
        dp_spoiler_n = q*aircraft.wing_area_m2*delta_cd_spoiler
        total_drag_n = (di_n+dp_n+dp_spoiler_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor
        force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2
      
        # total shaft power
        shaft_power_kw = (force_h_n*aircraft.mission.reserve_decel_descend_avg_h_m_p_s+force_v_n*(0.5*(v0_v_m_p_s+vf_v_m_p_s)))/(aircraft.propulsion.rotor_effic*W_P_KW) + shaft_power_deficit_kw

      return shaft_power_kw
    else:
      return None

# requires aircraft reserve_decel_descend_avg_shaft_power_kw
# requires power epu_effic
# scale reserve_decel_descend_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_reserve_decel_descend_avg_electric_power_kw(aircraft):
    if aircraft.reserve_decel_descend_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.reserve_decel_descend_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft reserve_decel_descend_avg_electric_power_kw
# requires mission reserve_decel_descend_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_reserve_decel_descend_energy_kw_hr(aircraft):
    if aircraft.reserve_decel_descend_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.reserve_decel_descend_avg_electric_power_kw*aircraft.mission.reserve_decel_descend_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Transition Descend (Segment I') -----
# requires mission reserve_trans_descend_avg_h_m_p_s, reserve_trans_descend_v_m_p_s, reserve_trans_descend_s
# includes aerodynamic lift, induced drag, parasite drag, weight, descend forces,
# hover-induced thrust assist if gravity is insufficient, and spoiler drag if power is negative
# horizontal velocity: initial from reserve decel segment to 0; vertical velocity changes from previous segment to final
# return None if mission, propulsion, or environment object not populated
def _calc_reserve_trans_descend_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:    
      q = 0.5*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.mission.reserve_trans_descend_avg_h_m_p_s**2.0
      theta = math.atan2(aircraft.mission.reserve_trans_descend_v_m_p_s, aircraft.mission.reserve_trans_descend_avg_h_m_p_s)

      weight_n = aircraft.max_takeoff_mass_kg*aircraft.environ.g_m_p_s2
      lift_n = weight_n*math.cos(theta)
      vehicle_cl = lift_n/(q*aircraft.wing_area_m2)

      # induced drag
      di_n = (lift_n**2.0)/(q*aircraft.wing_area_m2*math.pi*aircraft.wing_aspect_ratio*aircraft.span_effic_factor)
      # parasite drag
      cd0 = aircraft._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*aircraft.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = 2.0*aircraft.mission.reserve_decel_descend_avg_h_m_p_s-aircraft.mission.reserve_cruise_h_m_p_s
      vf_h_m_p_s = 0.0
      d_h_m = aircraft.mission.reserve_trans_descend_avg_h_m_p_s*aircraft.mission.reserve_trans_descend_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical acceleration 
      v0_v_m_p_s = aircraft.mission.reserve_decel_descend_v_m_p_s
      vf_v_m_p_s = aircraft.mission.reserve_trans_descend_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*aircraft.mission.reserve_trans_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # horizontal force component
      force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2

      # required vertical thrust from rotors (Newton's 2nd law with lift)
      T_req_n = max(0.0, (weight_n - lift_n) + aircraft.max_takeoff_mass_kg*a_v_m_p_s2)

      # induced velocity (momentum theory)
      v_i_hover = math.sqrt(T_req_n/(2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3*aircraft.propulsion.disk_area_m2))

      # hover-induced (assist) power
      P_hover_W = T_req_n*v_i_hover

      # baseline shaft power (vertical assist + horizontal forces)
      shaft_power_kw = (P_hover_W+force_h_n*aircraft.mission.reserve_trans_descend_avg_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)
      
      # check for negative power → apply spoiler drag to dissipate excess
      if shaft_power_kw < 0.0:
        required_extra_force_n = -force_h_n
        delta_cd_spoiler = required_extra_force_n/(q*aircraft.wing_area_m2)
        if delta_cd_spoiler < 0.0:
          delta_cd_spoiler = 0.0
        dp_spoiler_n = q*aircraft.wing_area_m2*delta_cd_spoiler
        total_drag_n = (di_n+dp_n+dp_spoiler_n)*aircraft.trim_drag_factor*aircraft.excres_protub_factor
        force_h_n = total_drag_n+aircraft.max_takeoff_mass_kg*a_h_m_p_s2

        # recompute total shaft power with spoiler drag
        shaft_power_kw = (P_hover_W+force_h_n*aircraft.mission.reserve_trans_descend_avg_h_m_p_s)/(aircraft.propulsion.rotor_effic*W_P_KW)

      return shaft_power_kw
    else:
      return None

# requires aircraft reserve_trans_descend_avg_shaft_power_kw
# requires power epu_effic
# scale reserve_trans_descend_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_reserve_trans_descend_avg_electric_power_kw(aircraft):
    if aircraft.reserve_trans_descend_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.reserve_trans_descend_avg_shaft_power_kw / aircraft.power.epu_effic
    else:
      return None

# requires aircraft reserve_trans_descend_avg_electric_power_kw
# requires mission reserve_trans_descend_s
# calculate the total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_reserve_trans_descend_energy_kw_hr(aircraft):
    if aircraft.reserve_trans_descend_avg_electric_power_kw != None and aircraft.mission != None:
      return \
       (aircraft.reserve_trans_descend_avg_electric_power_kw * aircraft.mission.reserve_trans_descend_s) / \
       S_P_HR
    else:
      return None

# ----- Reserve Hover Descend (Segment J') -----
# requires mission reserve_hover_descend_avg_v_m_p_s, reserve_hover_descend_s
# vertical power component only, assumes drag effects are negligible
# initial vertical velocity = 2*avg (downward), final = 0.0
# upward positive convention → acceleration is negative
# compute induced power from actual thrust
# return None if mission, propulsion, or environment object not populated
def _calc_reserve_hover_descend_avg_shaft_power_kw(aircraft):
    if aircraft.mission != None and aircraft.propulsion != None and aircraft.environ != None:
        
        # vertical kinematics (upward positive)
        v0_v_m_p_s = 2.0*aircraft.mission.reserve_hover_descend_avg_v_m_p_s
        vf_v_m_p_s = 0.0
        d_v_m = aircraft.mission.reserve_hover_descend_avg_v_m_p_s*aircraft.mission.reserve_hover_descend_s
        a_v_m_p_s2 = (vf_v_m_p_s**2.0 - v0_v_m_p_s**2.0) / (2.0*d_v_m)

        # required thrust (Newton's 2nd law, upward positive)
        T_required_N = max(0.0, aircraft.max_takeoff_mass_kg * (aircraft.environ.g_m_p_s2 + a_v_m_p_s2))

        # induced velocity in hover (momentum theory)
        v_i_hover = math.sqrt(T_required_N / \
                              (2.0*aircraft.environ.air_density_sea_lvl_kg_p_m3 * aircraft.propulsion.disk_area_m2))

        # induced power from actual thrust
        P_hover_W = T_required_N * v_i_hover

        # total shaft power (apply rotor efficiency once)
        return P_hover_W / (aircraft.propulsion.rotor_effic * W_P_KW)
    else:
        return None

# requires aircraft reserve_hover_descend_avg_shaft_power_kw
# requires power epu_effic
# scale reserve_hover_descend_avg_shaft_power_kw by epu_effic
# return None if aircraft field or power object not populated
def _calc_reserve_hover_descend_avg_electric_power_kw(aircraft):
    if aircraft.reserve_hover_descend_avg_shaft_power_kw != None and aircraft.power != None:
      return aircraft.reserve_hover_descend_avg_shaft_power_kw/aircraft.power.epu_effic
    else:
      return None

# requires aircraft reserve_hover_descend_avg_electric_power_kw
# requires mission reserve_hover_descend_s
# calculate total energy and convert to kW*hr
# return None if aircraft field or power object not populated
def _calc_reserve_hover_descend_energy_kw_hr(aircraft):
    if aircraft.reserve_hover_descend_avg_electric_power_kw != None and aircraft.mission != None:
      return \
      (aircraft.reserve_hover_descend_avg_electric_power_kw*aircraft.mission.reserve_hover_descend_s)/\
      S_P_HR
    else:
      return None