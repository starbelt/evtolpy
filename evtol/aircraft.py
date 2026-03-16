# aircraft.py
#
# A Python class containing aircraft characteristics
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import copy # deepcopy
import json # json parsing
import math # log10, pi
import sys  # not needed when using as a package

# path to directory with other classes; use before deploying as package
sys.path.append('../evtol')
from .environ import Environ
from .mission import Mission
from .power import Power
from .propulsion import Propulsion

# path to directory with other aircraft modules; use before deploying as package
from .aircraft_modules import aircraft_abu
from .aircraft_modules import aircraft_aero
from .aircraft_modules import aircraft_battery
from .aircraft_modules import aircraft_geometry
from .aircraft_modules import aircraft_iteration
from .aircraft_modules import aircraft_mass
from .aircraft_modules import aircraft_performance
from .aircraft_modules import aircraft_propulsion

# constants
W_P_KW = 1000.0
S_P_HR = 3600.0
KG_2_LB = 2.20462
M_2_FT = 3.28084
M_P_S_2_KTS = 1.9438
N_P_M2_2_LB_P_FT2 = 0.0209

# Aircraft class
class Aircraft:
  # class constructor
  def __init__(self, path_to_json: str):

    # open and load JSON specification
    ifile = open(path_to_json, 'r')
    ijson = json.load(ifile)

    # aircraft properties
    self._max_takeoff_mass_kg = ijson['aircraft']['max_takeoff_mass_kg']
    self._payload_kg = ijson['aircraft']['payload_kg']
    self._vehicle_cl_max = ijson['aircraft']['vehicle_cl_max']
    self._wing_taper_ratio = ijson['aircraft']['wing_taper_ratio']
    self._wingspan_m = ijson['aircraft']['wingspan_m']
    self._d_value_m = ijson['aircraft']['d_value_m']
    self._stall_speed_m_p_s = ijson['aircraft']['stall_speed_m_p_s']
    self._fuselage_l_m = ijson['aircraft']['fuselage_l_m']
    self._fuselage_w_m = ijson['aircraft']['fuselage_w_m']
    self._fuselage_h_m = ijson['aircraft']['fuselage_h_m']
    self._wing_airfoil_cd_at_cruise_cl = \
     ijson['aircraft']['wing_airfoil_cd_at_cruise_cl']
    self._empennage_airfoil_cd0 = ijson['aircraft']['empennage_airfoil_cd0']
    self._span_effic_factor = ijson['aircraft']['span_effic_factor']
    self._trim_drag_factor = ijson['aircraft']['trim_drag_factor']
    self._landing_gear_drag_area_m2 = \
     ijson['aircraft']['landing_gear_drag_area_m2']
    self._excres_protub_factor = ijson['aircraft']['excres_protub_factor']
    self._horiz_tail_vol_coeff = ijson['aircraft']['horiz_tail_vol_coeff']
    self._vert_tail_vol_coeff = ijson['aircraft']['vert_tail_vol_coeff']
    self._ratio_disk_to_stopped_rotor_area = \
     ijson['aircraft']['ratio_disk_to_stopped_rotor_area']
    self._wing_t_p_c = ijson['aircraft']['wing_t_p_c']
    self._actuator_mass_kg = ijson['aircraft']['actuator_mass_kg']
    self._furnishings_mass_kg = ijson['aircraft']['furnishings_mass_kg']
    self._environmental_control_system_mass_kg = \
     ijson['aircraft']['environmental_control_system_mass_kg']
    self._avionics_mass_kg = ijson['aircraft']['avionics_mass_kg']
    self._hivolt_power_dist_mass_kg = \
     ijson['aircraft']['hivolt_power_dist_mass_kg']
    self._lovolt_power_coms_mass_kg = \
     ijson['aircraft']['lovolt_power_coms_mass_kg']
    self._mass_margin_factor = ijson['aircraft']['mass_margin_factor']

    # has-a classes: add classes if they exist in JSON
    self._environ = None
    if 'environ' in ijson:
      self._environ = Environ(path_to_json)
    self._mission = None
    if 'mission' in ijson:
      self._mission = Mission(path_to_json)
    self._power = None
    if 'power' in ijson:
      self._power = Power(path_to_json)
    self._propulsion = None
    if 'propulsion' in ijson:
      self._propulsion = Propulsion(path_to_json)

    # close JSON file
    ifile.close()

  # Wrapper methods: aircraft_aero
  def _calc_cruise_cl(self):
    return aircraft_aero._calc_cruise_cl(self)

  def _calc_fuselage_cd0_p_cf(self):
    return aircraft_aero._calc_fuselage_cd0_p_cf(self)

  def _calc_fuselage_cruise_reynolds(self):
    return aircraft_aero._calc_fuselage_cruise_reynolds(self)

  def _calc_fuselage_cf(self):
    return aircraft_aero._calc_fuselage_cf(self)

  def _calc_fuselage_cd0(self):
    return aircraft_aero._calc_fuselage_cd0(self)

  def _calc_induced_drag_cdi(self):
    return aircraft_aero._calc_induced_drag_cdi(self)

  def _calc_horiz_tail_cd0(self):
    return aircraft_aero._calc_horiz_tail_cd0(self)

  def _calc_vert_tail_cd0(self):
    return aircraft_aero._calc_vert_tail_cd0(self)

  def _calc_landing_gear_cd0(self):
    return aircraft_aero._calc_landing_gear_cd0(self)

  def _calc_stopped_rotor_cd0(self):
    return aircraft_aero._calc_stopped_rotor_cd0(self)

  def _calc_cruise_cd(self):
    return aircraft_aero._calc_cruise_cd(self)

  def _calc_cruise_l_p_d(self):
    return aircraft_aero._calc_cruise_l_p_d(self)

  def _calc_total_drag_coef(self):
    return aircraft_aero._calc_total_drag_coef(self)


  # Wrapper methods: aircraft_battery
  def _estimate_cccv_charge_time_hr(
                                    self,
                                    E_pack_kwh,
                                    P_charger_ac_kw,
                                    eta_charger_dc=0.95,
                                    c_rate_max=1.0,
                                    v_pack_nom_v=800.0,
                                    i_term_c=0.05,
                                    soc_start=None,
                                    soc_target=1.0,
                                    soc_cc_end=0.80,
                                    dod=None,
                                    Q_Ah=None
  ):
      return aircraft_battery._estimate_cccv_charge_time_hr(
                                    self,
                                    E_pack_kwh,
                                    P_charger_ac_kw,
                                    eta_charger_dc=eta_charger_dc,
                                    c_rate_max=c_rate_max,
                                    v_pack_nom_v=v_pack_nom_v,
                                    i_term_c=i_term_c,
                                    soc_start=soc_start,
                                    soc_target=soc_target,
                                    soc_cc_end=soc_cc_end,
                                    dod=dod,
                                    Q_Ah=Q_Ah
      )

  # Wrapper methods: aircraft_geometry
  def _calc_wing_area_m2(self):
    return aircraft_geometry._calc_wing_area_m2(self)

  def _calc_fuselage_fineness_ratio(self):
    return aircraft_geometry._calc_fuselage_fineness_ratio(self)

  def _calc_wing_mac_m(self):
    return aircraft_geometry._calc_wing_mac_m(self)

  def _calc_wing_aspect_ratio(self):
    return aircraft_geometry._calc_wing_aspect_ratio(self)

  def _calc_wing_root_chord_m(self):
    return aircraft_geometry._calc_wing_root_chord_m(self)

  def _calc_horiz_tail_area_m2(self):
    return aircraft_geometry._calc_horiz_tail_area_m2(self)

  def _calc_vert_tail_area_m2(self):
    return aircraft_geometry._calc_vert_tail_area_m2(self)

  def _calc_fuselage_wetted_area_m2(self):
    return aircraft_geometry._calc_fuselage_wetted_area_m2(self)
  

  # Wrapper methods: aircraft_iteration
  def _iterate_mtow(self):
    return aircraft_iteration._iterate_mtow(self)


  # Wrapper methods: aircraft_mass
  def _calc_payload_mass_frac(self):
    return aircraft_mass._calc_payload_mass_frac(self)

  def _calc_single_epu_mass_kg(self):
    return aircraft_mass._calc_single_epu_mass_kg(self)

  def _calc_battery_mass_kg(self):
    return aircraft_mass._calc_battery_mass_kg(self)

  def _calc_wing_mass_kg(self):
    return aircraft_mass._calc_wing_mass_kg(self)

  def _calc_horiz_tail_mass_kg(self):
    return aircraft_mass._calc_horiz_tail_mass_kg(self)

  def _calc_vert_tail_mass_kg(self):
    return aircraft_mass._calc_vert_tail_mass_kg(self)

  def _calc_fuselage_mass_kg(self):
    return aircraft_mass._calc_fuselage_mass_kg(self)

  def _calc_boom_mass_kg(self):
    return aircraft_mass._calc_boom_mass_kg(self)

  def _calc_landing_gear_mass_kg(self):
    return aircraft_mass._calc_landing_gear_mass_kg(self)

  def _calc_epu_mass_kg(self):
    return aircraft_mass._calc_epu_mass_kg(self)

  def _calc_lift_rotor_hub_mass_kg(self):
    return aircraft_mass._calc_lift_rotor_hub_mass_kg(self)

  def _calc_tilt_rotor_mass_kg(self):
    return aircraft_mass._calc_tilt_rotor_mass_kg(self)

  def _calc_empty_mass_kg(self):
    return aircraft_mass._calc_empty_mass_kg(self)


  # Wrapper methods: aircraft_performance
  def _calc_hover_shaft_power_kw(self):
    return aircraft_performance._calc_hover_shaft_power_kw(self)

  def _calc_hover_electric_power_kw(self):
    return aircraft_performance._calc_hover_electric_power_kw(self)

  def _calc_total_mission_energy_kw_hr(self):
    return aircraft_performance._calc_total_mission_energy_kw_hr(self)

  def _calc_total_reserve_mission_energy_kw_hr(self):
    return aircraft_performance._calc_total_reserve_mission_energy_kw_hr(self)

  def _calc_depart_taxi_avg_shaft_power_kw(self):
    return aircraft_performance._calc_depart_taxi_avg_shaft_power_kw(self)

  def _calc_depart_taxi_avg_electric_power_kw(self):
    return aircraft_performance._calc_depart_taxi_avg_electric_power_kw(self)

  def _calc_depart_taxi_energy_kw_hr(self):
    return aircraft_performance._calc_depart_taxi_energy_kw_hr(self)

  def _calc_hover_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_hover_climb_avg_shaft_power_kw(self)

  def _calc_hover_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_hover_climb_avg_electric_power_kw(self)

  def _calc_hover_climb_energy_kw_hr(self):
    return aircraft_performance._calc_hover_climb_energy_kw_hr(self)

  def _calc_trans_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_trans_climb_avg_shaft_power_kw(self)

  def _calc_trans_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_trans_climb_avg_electric_power_kw(self)

  def _calc_trans_climb_energy_kw_hr(self):
    return aircraft_performance._calc_trans_climb_energy_kw_hr(self)

  def _calc_depart_proc_avg_shaft_power_kw(self):
    return aircraft_performance._calc_depart_proc_avg_shaft_power_kw(self)

  def _calc_depart_proc_avg_electric_power_kw(self):
    return aircraft_performance._calc_depart_proc_avg_electric_power_kw(self)

  def _calc_depart_proc_energy_kw_hr(self):
    return aircraft_performance._calc_depart_proc_energy_kw_hr(self)

  def _calc_accel_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_accel_climb_avg_shaft_power_kw(self)

  def _calc_accel_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_accel_climb_avg_electric_power_kw(self)

  def _calc_accel_climb_energy_kw_hr(self):
    return aircraft_performance._calc_accel_climb_energy_kw_hr(self)

  def _calc_cruise_avg_shaft_power_kw(self):
    return aircraft_performance._calc_cruise_avg_shaft_power_kw(self)

  def _calc_cruise_avg_electric_power_kw(self):
    return aircraft_performance._calc_cruise_avg_electric_power_kw(self)

  def _calc_cruise_energy_kw_hr(self):
    return aircraft_performance._calc_cruise_energy_kw_hr(self)

  def _calc_decel_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_decel_descend_avg_shaft_power_kw(self)

  def _calc_decel_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_decel_descend_avg_electric_power_kw(self)

  def _calc_decel_descend_energy_kw_hr(self):
    return aircraft_performance._calc_decel_descend_energy_kw_hr(self)

  def _calc_arrive_proc_avg_shaft_power_kw(self):
    return aircraft_performance._calc_arrive_proc_avg_shaft_power_kw(self)

  def _calc_arrive_proc_avg_electric_power_kw(self):
    return aircraft_performance._calc_arrive_proc_avg_electric_power_kw(self)

  def _calc_arrive_proc_energy_kw_hr(self):
    return aircraft_performance._calc_arrive_proc_energy_kw_hr(self)

  def _calc_trans_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_trans_descend_avg_shaft_power_kw(self)

  def _calc_trans_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_trans_descend_avg_electric_power_kw(self)

  def _calc_trans_descend_energy_kw_hr(self):
    return aircraft_performance._calc_trans_descend_energy_kw_hr(self)

  def _calc_hover_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_hover_descend_avg_shaft_power_kw(self)

  def _calc_hover_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_hover_descend_avg_electric_power_kw(self)

  def _calc_hover_descend_energy_kw_hr(self):
    return aircraft_performance._calc_hover_descend_energy_kw_hr(self)

  def _calc_arrive_taxi_avg_shaft_power_kw(self):
    return aircraft_performance._calc_arrive_taxi_avg_shaft_power_kw(self)

  def _calc_arrive_taxi_avg_electric_power_kw(self):
    return aircraft_performance._calc_arrive_taxi_avg_electric_power_kw(self)

  def _calc_arrive_taxi_energy_kw_hr(self):
    return aircraft_performance._calc_arrive_taxi_energy_kw_hr(self)

  def _calc_reserve_hover_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_hover_climb_avg_shaft_power_kw(self)

  def _calc_reserve_hover_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_hover_climb_avg_electric_power_kw(self)

  def _calc_reserve_hover_climb_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_hover_climb_energy_kw_hr(self)

  def _calc_reserve_trans_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_trans_climb_avg_shaft_power_kw(self)

  def _calc_reserve_trans_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_trans_climb_avg_electric_power_kw(self)

  def _calc_reserve_trans_climb_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_trans_climb_energy_kw_hr(self)

  def _calc_reserve_accel_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_accel_climb_avg_shaft_power_kw(self)

  def _calc_reserve_accel_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_accel_climb_avg_electric_power_kw(self)

  def _calc_reserve_accel_climb_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_accel_climb_energy_kw_hr(self)

  def _calc_reserve_cruise_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_cruise_avg_shaft_power_kw(self)

  def _calc_reserve_cruise_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_cruise_avg_electric_power_kw(self)

  def _calc_reserve_cruise_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_cruise_energy_kw_hr(self)

  def _calc_reserve_decel_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_decel_descend_avg_shaft_power_kw(self)

  def _calc_reserve_decel_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_decel_descend_avg_electric_power_kw(self)

  def _calc_reserve_decel_descend_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_decel_descend_energy_kw_hr(self)

  def _calc_reserve_trans_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_trans_descend_avg_shaft_power_kw(self)

  def _calc_reserve_trans_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_trans_descend_avg_electric_power_kw(self)

  def _calc_reserve_trans_descend_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_trans_descend_energy_kw_hr(self)

  def _calc_reserve_hover_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_hover_descend_avg_shaft_power_kw(self)

  def _calc_reserve_hover_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_hover_descend_avg_electric_power_kw(self)

  def _calc_reserve_hover_descend_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_hover_descend_energy_kw_hr(self)


  # Wrapper methods: aircraft_propulsion
  def _calc_disk_loading_kg_p_m2(self):
    return aircraft_propulsion._calc_disk_loading_kg_p_m2(self)

  def _calc_over_torque_factor(self):
    return aircraft_propulsion._calc_over_torque_factor(self)

  def _calc_rotor_solidity(self):
    return aircraft_propulsion._calc_rotor_solidity(self)


  # Wrapper methods: aircraft_abu
  def evaluate_abu_detach_candidates(self, candidates, abu_spec=None):
    return aircraft_abu.evaluate_abu_detach_candidates(
      self, candidates, abu_spec=abu_spec
    )

  def _evaluate_extended_flight(self, E_mission_kwh_per_abu_list, abu_spec=None):
    return aircraft_abu._evaluate_extended_flight(
      self, E_mission_kwh_per_abu_list, abu_spec=abu_spec
    )

  def _evaluate_extended_flight_detach_on_depletion_or_end(
    self, E_mission_kwh_per_abu_list, abu_spec=None
  ):
    return aircraft_abu._evaluate_extended_flight_detach_on_depletion_or_end(
      self, E_mission_kwh_per_abu_list, abu_spec=abu_spec
    )

  def _evaluate_landing_safety_loiter(
                                      self,
                                      E_mission_kwh_per_abu_list,
                                      divert_distance_mi,
                                      t_hover_s,
                                      t_hover_descend_s,
                                      abu_spec=None
                                    ):
    return aircraft_abu._evaluate_landing_safety_loiter(
                                      self,
                                      E_mission_kwh_per_abu_list,
                                      divert_distance_mi,
                                      t_hover_s,
                                      t_hover_descend_s,
                                      abu_spec=abu_spec
    )

  def _evaluate_landing_safety_divert_baseline(
                                              self,
                                              divert_distance_mi,
                                              t_hover_s,
                                              t_hover_descend_s,
                                              tol=1e-3,
                                              max_iter=100
  ):
    return aircraft_abu._evaluate_landing_safety_divert_baseline(
                                              self,
                                              divert_distance_mi,
                                              t_hover_s,
                                              t_hover_descend_s,
                                              tol=tol,
                                              max_iter=max_iter
    )

  def _evaluate_common_case_baseline(
                                    self,
                                    E_pack_kwh=None,
                                    P_charger_ac_kw=115.0,
                                    eta_charger_dc=0.95,
                                    c_rate_max=1.0,
                                    v_pack_nom_v=800.0,
                                    i_term_c=0.05,
                                    soc_start=None,
                                    soc_target=1.0,
                                    soc_cc_end=0.80,
                                    t_ground_ops_hr=0.2833,
                                    daily_operation_hr=24.0,
                                    mission_time_s=None
  ):
    return aircraft_abu._evaluate_common_case_baseline(
                                    self,
                                    E_pack_kwh=E_pack_kwh,
                                    P_charger_ac_kw=P_charger_ac_kw,
                                    eta_charger_dc=eta_charger_dc,
                                    c_rate_max=c_rate_max,
                                    v_pack_nom_v=v_pack_nom_v,
                                    i_term_c=i_term_c,
                                    soc_start=soc_start,
                                    soc_target=soc_target,
                                    soc_cc_end=soc_cc_end,
                                    t_ground_ops_hr=t_ground_ops_hr,
                                    daily_operation_hr=daily_operation_hr,
                                    mission_time_s=mission_time_s
    )

  def _evaluate_common_case_baseline_timeline(
                                              self,
                                              E_pack_kwh=None,
                                              P_charger_ac_kw=115.0,
                                              eta_charger_dc=0.95,
                                              c_rate_max=1.0,
                                              v_pack_nom_v=800.0,
                                              i_term_c=0.05,
                                              soc_start=None,
                                              soc_target=1.0,
                                              soc_cc_end=0.80,
                                              t_ground_ops_hr=0.2833,
                                              daily_operation_hr=24.0,
                                              mission_time_s=None
  ):
    return aircraft_abu._evaluate_common_case_baseline_timeline(
                                              self,
                                              E_pack_kwh=E_pack_kwh,
                                              P_charger_ac_kw=P_charger_ac_kw,
                                              eta_charger_dc=eta_charger_dc,
                                              c_rate_max=c_rate_max,
                                              v_pack_nom_v=v_pack_nom_v,
                                              i_term_c=i_term_c,
                                              soc_start=soc_start,
                                              soc_target=soc_target,
                                              soc_cc_end=soc_cc_end,
                                              t_ground_ops_hr=t_ground_ops_hr,
                                              daily_operation_hr=daily_operation_hr,
                                              mission_time_s=mission_time_s
    )

  def _evaluate_common_case_abu_assisted_takeoff_overlap_charging_queuing(
                                                                          self,
                                                                          candidates,
                                                                          abu_spec=None,
                                                                          n_abu_pool=1,
                                                                          P_charger_ac_kw=115.0,
                                                                          eta_charger_dc=0.95,
                                                                          c_rate_max=1.0,
                                                                          v_pack_nom_v_main=800.0,
                                                                          v_pack_nom_v_abu=400.0,
                                                                          i_term_c=0.05,
                                                                          soc_target=1.0,
                                                                          soc_cc_end=0.80,
                                                                          t_ground_ops_hr=0.2833,
                                                                          V_abu_horizontal_m_p_s=30.0,
                                                                          V_abu_vertical_m_p_s=5.1,
                                                                          h_detach_ft=3000.0,
                                                                          daily_operation_hr=24.0,
                                                                          mission_time_s=None
  ):
    return aircraft_abu._evaluate_common_case_abu_assisted_takeoff_overlap_charging_queuing(
                                                                          self,
                                                                          candidates,
                                                                          abu_spec=abu_spec,
                                                                          n_abu_pool=n_abu_pool,
                                                                          P_charger_ac_kw=P_charger_ac_kw,
                                                                          eta_charger_dc=eta_charger_dc,
                                                                          c_rate_max=c_rate_max,
                                                                          v_pack_nom_v_main=v_pack_nom_v_main,
                                                                          v_pack_nom_v_abu=v_pack_nom_v_abu,
                                                                          i_term_c=i_term_c,
                                                                          soc_target=soc_target,
                                                                          soc_cc_end=soc_cc_end,
                                                                          t_ground_ops_hr=t_ground_ops_hr,
                                                                          V_abu_horizontal_m_p_s=V_abu_horizontal_m_p_s,
                                                                          V_abu_vertical_m_p_s=V_abu_vertical_m_p_s,
                                                                          h_detach_ft=h_detach_ft,
                                                                          daily_operation_hr=daily_operation_hr,
                                                                          mission_time_s=mission_time_s
    )

  def _evaluate_common_case_abu_extended_flight_overlap_charging_queuing(
                                                                        self,
                                                                        E_mission_kwh_per_abu_list,
                                                                        abu_spec=None,
                                                                        n_abu_pool=3,
                                                                        P_charger_ac_kw=115.0,
                                                                        eta_charger_dc=0.95,
                                                                        c_rate_max=1.0,
                                                                        v_pack_nom_v_main=800.0,
                                                                        v_pack_nom_v_abu=400.0,
                                                                        i_term_c=0.05,
                                                                        soc_target=1.0,
                                                                        soc_cc_end=0.80,
                                                                        t_ground_ops_hr=0.2833,
                                                                        V_abu_horizontal_m_p_s=30.0,
                                                                        V_abu_vertical_m_p_s=5.1,
                                                                        h_detach_ft=3000.0,
                                                                        daily_operation_hr=24.0,
                                                                        mission_time_s=None
  ):
    return aircraft_abu._evaluate_common_case_abu_extended_flight_overlap_charging_queuing(
                                                                        self,
                                                                        E_mission_kwh_per_abu_list,
                                                                        abu_spec=abu_spec,
                                                                        n_abu_pool=n_abu_pool,
                                                                        P_charger_ac_kw=P_charger_ac_kw,
                                                                        eta_charger_dc=eta_charger_dc,
                                                                        c_rate_max=c_rate_max,
                                                                        v_pack_nom_v_main=v_pack_nom_v_main,
                                                                        v_pack_nom_v_abu=v_pack_nom_v_abu,
                                                                        i_term_c=i_term_c,
                                                                        soc_target=soc_target,
                                                                        soc_cc_end=soc_cc_end,
                                                                        t_ground_ops_hr=t_ground_ops_hr,
                                                                        V_abu_horizontal_m_p_s=V_abu_horizontal_m_p_s,
                                                                        V_abu_vertical_m_p_s=V_abu_vertical_m_p_s,
                                                                        h_detach_ft=h_detach_ft,
                                                                        daily_operation_hr=daily_operation_hr,
                                                                        mission_time_s=mission_time_s
    )

  def _evaluate_common_case_abu_combined_flight_overlap_charging_queuing(
                                                                        self,
                                                                        candidates,
                                                                        E_mission_kwh_per_abu_list,
                                                                        abu_spec_takeoff=None,
                                                                        abu_spec_cruise=None,
                                                                        n_abu_pool_takeoff=3,
                                                                        n_abu_pool_cruise=3,
                                                                        P_charger_ac_kw=115.0,
                                                                        eta_charger_dc=0.95,
                                                                        c_rate_max=1.0,
                                                                        v_pack_nom_v_main=800.0,
                                                                        v_pack_nom_v_abu=400.0,
                                                                        i_term_c=0.05,
                                                                        soc_target=1.0,
                                                                        soc_cc_end=0.80,
                                                                        t_ground_ops_hr=0.2833,
                                                                        V_takeoff_abu_horizontal_m_p_s=30.0,
                                                                        V_takeoff_abu_vertical_m_p_s=5.1,
                                                                        h_detach_takeoff_ft=3000.0,
                                                                        V_cruise_abu_horizontal_m_p_s=30.0,
                                                                        V_cruise_abu_vertical_m_p_s=5.1,
                                                                        h_detach_cruise_ft=3000.0,
                                                                        daily_operation_hr=24.0,
                                                                        mission_time_s=None
  ):
    return aircraft_abu._evaluate_common_case_abu_combined_flight_overlap_charging_queuing(
                                                                        self,
                                                                        candidates,
                                                                        E_mission_kwh_per_abu_list,
                                                                        abu_spec_takeoff=abu_spec_takeoff,
                                                                        abu_spec_cruise=abu_spec_cruise,
                                                                        n_abu_pool_takeoff=n_abu_pool_takeoff,
                                                                        n_abu_pool_cruise=n_abu_pool_cruise,
                                                                        P_charger_ac_kw=P_charger_ac_kw,
                                                                        eta_charger_dc=eta_charger_dc,
                                                                        c_rate_max=c_rate_max,
                                                                        v_pack_nom_v_main=v_pack_nom_v_main,
                                                                        v_pack_nom_v_abu=v_pack_nom_v_abu,
                                                                        i_term_c=i_term_c,
                                                                        soc_target=soc_target,
                                                                        soc_cc_end=soc_cc_end,
                                                                        t_ground_ops_hr=t_ground_ops_hr,
                                                                        V_takeoff_abu_horizontal_m_p_s=V_takeoff_abu_horizontal_m_p_s,
                                                                        V_takeoff_abu_vertical_m_p_s=V_takeoff_abu_vertical_m_p_s,
                                                                        h_detach_takeoff_ft=h_detach_takeoff_ft,
                                                                        V_cruise_abu_horizontal_m_p_s=V_cruise_abu_horizontal_m_p_s,
                                                                        V_cruise_abu_vertical_m_p_s=V_cruise_abu_vertical_m_p_s,
                                                                        h_detach_cruise_ft=h_detach_cruise_ft,
                                                                        daily_operation_hr=daily_operation_hr,
                                                                        mission_time_s=mission_time_s
    )


  # aircraft_aero properties
  @property
  def cruise_cl(self):
    return aircraft_aero._calc_cruise_cl(self)

  @property
  def fuselage_cd0_p_cf(self):
    return aircraft_aero._calc_fuselage_cd0_p_cf(self)

  @property
  def fuselage_cruise_reynolds(self):
    return aircraft_aero._calc_fuselage_cruise_reynolds(self)

  @property
  def fuselage_cf(self):
    return aircraft_aero._calc_fuselage_cf(self)

  @property
  def fuselage_cd0(self):
    return aircraft_aero._calc_fuselage_cd0(self)

  @property
  def induced_drag_cdi(self):
    return aircraft_aero._calc_induced_drag_cdi(self)

  @property
  def horiz_tail_cd0(self):
    return aircraft_aero._calc_horiz_tail_cd0(self)

  @property
  def vert_tail_cd0(self):
    return aircraft_aero._calc_vert_tail_cd0(self)

  @property
  def landing_gear_cd0(self):
    return aircraft_aero._calc_landing_gear_cd0(self)

  @property
  def stopped_rotor_cd0(self):
    return aircraft_aero._calc_stopped_rotor_cd0(self)

  @property
  def cruise_cd(self):
    return aircraft_aero._calc_cruise_cd(self)

  @property
  def cruise_l_p_d(self):
    return aircraft_aero._calc_cruise_l_p_d(self)

  @property
  def total_drag_coef(self):
    return aircraft_aero._calc_total_drag_coef(self)
  

  # aircraft_geometry properties
  @property
  def wing_area_m2(self):
    return aircraft_geometry._calc_wing_area_m2(self)

  @property
  def fuselage_fineness_ratio(self):
    return aircraft_geometry._calc_fuselage_fineness_ratio(self)

  @property
  def wing_mac_m(self):
    return aircraft_geometry._calc_wing_mac_m(self)

  @property
  def wing_aspect_ratio(self):
    return aircraft_geometry._calc_wing_aspect_ratio(self)

  @property
  def wing_root_chord_m(self):
    return aircraft_geometry._calc_wing_root_chord_m(self)

  @property
  def horiz_tail_area_m2(self):
    return aircraft_geometry._calc_horiz_tail_area_m2(self)

  @property
  def vert_tail_area_m2(self):
    return aircraft_geometry._calc_vert_tail_area_m2(self)
    
  @property
  def fuselage_wetted_area_m2(self):
    return aircraft_geometry._calc_fuselage_wetted_area_m2(self)


  # aircraft_iteration properties
  @property
  def iterate_mtow(self):
    return aircraft_iteration._iterate_mtow(self)
  

  # aircraft_mass properties
  @property
  def payload_mass_frac(self):
    return aircraft_mass._calc_payload_mass_frac(self)

  @property
  def single_epu_mass_kg(self):
    return aircraft_mass._calc_single_epu_mass_kg(self)

  @property
  def battery_mass_kg(self):
    return aircraft_mass._calc_battery_mass_kg(self)

  @property
  def wing_mass_kg(self):
    return aircraft_mass._calc_wing_mass_kg(self)

  @property
  def horiz_tail_mass_kg(self):
    return aircraft_mass._calc_horiz_tail_mass_kg(self)

  @property
  def vert_tail_mass_kg(self):
    return aircraft_mass._calc_vert_tail_mass_kg(self)

  @property
  def fuselage_mass_kg(self):
    return aircraft_mass._calc_fuselage_mass_kg(self)

  @property
  def boom_mass_kg(self):
    return aircraft_mass._calc_boom_mass_kg(self)

  @property
  def landing_gear_mass_kg(self):
    return aircraft_mass._calc_landing_gear_mass_kg(self)

  @property
  def epu_mass_kg(self):
    return aircraft_mass._calc_epu_mass_kg(self)

  @property
  def lift_rotor_hub_mass_kg(self):
    return aircraft_mass._calc_lift_rotor_hub_mass_kg(self)

  @property
  def tilt_rotor_mass_kg(self):
    return aircraft_mass._calc_tilt_rotor_mass_kg(self)

  @property
  def empty_mass_kg(self):
    return aircraft_mass._calc_empty_mass_kg(self)


  # aircraft_performance properties
  @property
  def hover_shaft_power_kw(self):
    return aircraft_performance._calc_hover_shaft_power_kw(self)

  @property
  def hover_electric_power_kw(self):
    return aircraft_performance._calc_hover_electric_power_kw(self)
  
  @property
  def total_mission_energy_kw_hr(self):
    return aircraft_performance._calc_total_mission_energy_kw_hr(self)

  @property
  def total_reserve_mission_energy_kw_hr(self):
    return aircraft_performance._calc_total_reserve_mission_energy_kw_hr(self)

  @property
  def depart_taxi_avg_shaft_power_kw(self):
    return aircraft_performance._calc_depart_taxi_avg_shaft_power_kw(self)

  @property
  def depart_taxi_avg_electric_power_kw(self):
    return aircraft_performance._calc_depart_taxi_avg_electric_power_kw(self)

  @property
  def depart_taxi_energy_kw_hr(self):
    return aircraft_performance._calc_depart_taxi_energy_kw_hr(self)

  @property
  def hover_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_hover_climb_avg_shaft_power_kw(self)

  @property
  def hover_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_hover_climb_avg_electric_power_kw(self)

  @property
  def hover_climb_energy_kw_hr(self):
    return aircraft_performance._calc_hover_climb_energy_kw_hr(self)
    
  @property
  def trans_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_trans_climb_avg_shaft_power_kw(self)
  
  @property
  def trans_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_trans_climb_avg_electric_power_kw(self)
  
  @property
  def trans_climb_energy_kw_hr(self):
    return aircraft_performance._calc_trans_climb_energy_kw_hr(self)

  @property
  def depart_proc_avg_shaft_power_kw(self):
    return aircraft_performance._calc_depart_proc_avg_shaft_power_kw(self)
  
  @property
  def depart_proc_avg_electric_power_kw(self):
    return aircraft_performance._calc_depart_proc_avg_electric_power_kw(self)
  
  @property
  def depart_proc_energy_kw_hr(self):
    return aircraft_performance._calc_depart_proc_energy_kw_hr(self)

  @property
  def accel_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_accel_climb_avg_shaft_power_kw(self)
  
  @property
  def accel_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_accel_climb_avg_electric_power_kw(self)
  
  @property
  def accel_climb_energy_kw_hr(self):
    return aircraft_performance._calc_accel_climb_energy_kw_hr(self)

  @property
  def cruise_avg_shaft_power_kw(self):
    return aircraft_performance._calc_cruise_avg_shaft_power_kw(self)
  
  @property
  def cruise_avg_electric_power_kw(self):
    return aircraft_performance._calc_cruise_avg_electric_power_kw(self)

  @property
  def cruise_energy_kw_hr(self):
    return aircraft_performance._calc_cruise_energy_kw_hr(self)
  
  @property
  def decel_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_decel_descend_avg_shaft_power_kw(self)
  
  @property
  def decel_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_decel_descend_avg_electric_power_kw(self)

  @property
  def decel_descend_energy_kw_hr(self):
    return aircraft_performance._calc_decel_descend_energy_kw_hr(self)
    
  @property
  def arrive_proc_avg_shaft_power_kw(self):
    return aircraft_performance._calc_arrive_proc_avg_shaft_power_kw(self)
  
  @property
  def arrive_proc_avg_electric_power_kw(self):
    return aircraft_performance._calc_arrive_proc_avg_electric_power_kw(self)

  @property
  def arrive_proc_energy_kw_hr(self):
    return aircraft_performance._calc_arrive_proc_energy_kw_hr(self)
  
  @property
  def trans_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_trans_descend_avg_shaft_power_kw(self)
  
  @property
  def trans_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_trans_descend_avg_electric_power_kw(self)

  @property
  def trans_descend_energy_kw_hr(self):
    return aircraft_performance._calc_trans_descend_energy_kw_hr(self)

  @property
  def hover_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_hover_descend_avg_shaft_power_kw(self)
  
  @property
  def hover_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_hover_descend_avg_electric_power_kw(self)

  @property
  def hover_descend_energy_kw_hr(self):
    return aircraft_performance._calc_hover_descend_energy_kw_hr(self)
  
  @property
  def arrive_taxi_avg_shaft_power_kw(self):
    return aircraft_performance._calc_arrive_taxi_avg_shaft_power_kw(self)
  
  @property
  def arrive_taxi_avg_electric_power_kw(self):
    return aircraft_performance._calc_arrive_taxi_avg_electric_power_kw(self)
  
  @property
  def arrive_taxi_energy_kw_hr(self):
    return aircraft_performance._calc_arrive_taxi_energy_kw_hr(self)

  @property
  def reserve_hover_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_hover_climb_avg_shaft_power_kw(self)
  
  @property
  def reserve_hover_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_hover_climb_avg_electric_power_kw(self)

  @property
  def reserve_hover_climb_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_hover_climb_energy_kw_hr(self)

  @property
  def reserve_trans_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_trans_climb_avg_shaft_power_kw(self)
  
  @property
  def reserve_trans_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_trans_climb_avg_electric_power_kw(self)

  @property
  def reserve_trans_climb_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_trans_climb_energy_kw_hr(self)
  
  @property
  def reserve_accel_climb_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_accel_climb_avg_shaft_power_kw(self)
  
  @property
  def reserve_accel_climb_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_accel_climb_avg_electric_power_kw(self)

  @property
  def reserve_accel_climb_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_accel_climb_energy_kw_hr(self)
  
  @property
  def reserve_cruise_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_cruise_avg_shaft_power_kw(self)
  
  @property
  def reserve_cruise_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_cruise_avg_electric_power_kw(self)

  @property
  def reserve_cruise_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_cruise_energy_kw_hr(self)

  @property
  def reserve_decel_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_decel_descend_avg_shaft_power_kw(self)
  
  @property
  def reserve_decel_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_decel_descend_avg_electric_power_kw(self)

  @property
  def reserve_decel_descend_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_decel_descend_energy_kw_hr(self)

  @property
  def reserve_trans_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_trans_descend_avg_shaft_power_kw(self)

  @property
  def reserve_trans_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_trans_descend_avg_electric_power_kw(self)

  @property
  def reserve_trans_descend_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_trans_descend_energy_kw_hr(self)

  @property
  def reserve_hover_descend_avg_shaft_power_kw(self):
    return aircraft_performance._calc_reserve_hover_descend_avg_shaft_power_kw(self)

  @property
  def reserve_hover_descend_avg_electric_power_kw(self):
    return aircraft_performance._calc_reserve_hover_descend_avg_electric_power_kw(self)

  @property
  def reserve_hover_descend_energy_kw_hr(self):
    return aircraft_performance._calc_reserve_hover_descend_energy_kw_hr(self)


  # aircraft_propulsion properties
  @property
  def disk_loading_kg_p_m2(self):
    return aircraft_propulsion._calc_disk_loading_kg_p_m2(self)
  
  @property
  def over_torque_factor(self):
    return aircraft_propulsion._calc_over_torque_factor(self)

  @property
  def rotor_solidity(self):
    return aircraft_propulsion._calc_rotor_solidity(self)


  # stored JSON-backed properties
  @property
  def max_takeoff_mass_kg(self):
    return self._max_takeoff_mass_kg
  
  @max_takeoff_mass_kg.setter
  def max_takeoff_mass_kg(self, value):
    self._max_takeoff_mass_kg = value

  @property
  def payload_kg(self):
    return self._payload_kg

  @property
  def vehicle_cl_max(self):
    return self._vehicle_cl_max

  @property
  def wing_taper_ratio(self):
    return self._wing_taper_ratio

  @property
  def wingspan_m(self):
    return self._wingspan_m

  @property
  def d_value_m(self):
    return self._d_value_m

  @property
  def stall_speed_m_p_s(self):
    return self._stall_speed_m_p_s

  @property
  def fuselage_l_m(self):
    return self._fuselage_l_m

  @property
  def fuselage_w_m(self):
    return self._fuselage_w_m

  @property
  def fuselage_h_m(self):
    return self._fuselage_h_m

  @property
  def wing_airfoil_cd_at_cruise_cl(self):
    return self._wing_airfoil_cd_at_cruise_cl

  @property
  def empennage_airfoil_cd0(self):
    return self._empennage_airfoil_cd0

  @property
  def span_effic_factor(self):
    return self._span_effic_factor

  @property
  def trim_drag_factor(self):
    return self._trim_drag_factor

  @property
  def landing_gear_drag_area_m2(self):
    return self._landing_gear_drag_area_m2

  @property
  def excres_protub_factor(self):
    return self._excres_protub_factor

  @property
  def horiz_tail_vol_coeff(self):
    return self._horiz_tail_vol_coeff

  @property
  def vert_tail_vol_coeff(self):
    return self._vert_tail_vol_coeff

  @property
  def ratio_disk_to_stopped_rotor_area(self):
    return self._ratio_disk_to_stopped_rotor_area

  @property
  def wing_t_p_c(self):
    return self._wing_t_p_c

  @property
  def actuator_mass_kg(self):
    return self._actuator_mass_kg

  @property
  def furnishings_mass_kg(self):
    return self._furnishings_mass_kg

  @property
  def environmental_control_system_mass_kg(self):
    return self._environmental_control_system_mass_kg

  @property
  def avionics_mass_kg(self):
    return self._avionics_mass_kg

  @property
  def hivolt_power_dist_mass_kg(self):
    return self._hivolt_power_dist_mass_kg

  @property
  def lovolt_power_coms_mass_kg(self):
    return self._lovolt_power_coms_mass_kg

  @property
  def mass_margin_factor(self):
    return self._mass_margin_factor


  @property
  def environ(self):
    return copy.deepcopy(self._environ)

  @property
  def mission(self):
    return copy.deepcopy(self._mission)

  @property
  def power(self):
    return copy.deepcopy(self._power)

  @property
  def propulsion(self):
    return copy.deepcopy(self._propulsion)