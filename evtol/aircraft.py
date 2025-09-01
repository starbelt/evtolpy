# aircraft.py
#
# A Python class containing aircraft characteristics
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris
#
# See the LICENSE file for the license

# import Python modules
import copy # deepcopy
import json # json parsing
import math # log10, pi
import sys  # not needed when using as a package

# path to directory with other classes; use before deploying as package
sys.path.append('../evtol')
from environ import Environ
from mission import Mission
from power import Power
from propulsion import Propulsion

# comment above and uncomment below when ready to deploy as package
#from .environ import Environ
#from .mission import Mission
#from .power import Power
#from .propulsion import Propulsion

# constants
W_P_KW = 1000.0
S_P_HR = 3600.0

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
    # calculate initial values of derived fields
    self._payload_mass_frac = self._calc_payload_mass_frac()
    self._disk_loading_kg_p_m2 = self._calc_disk_loading_kg_p_m2()
    self._hover_shaft_power_kw = self._calc_hover_shaft_power_kw()
    self._hover_electric_power_kw = self._calc_hover_electric_power_kw()
    self._wing_area_m2 = self._calc_wing_area_m2()
    self._cruise_cl = self._calc_cruise_cl()
    ## fuselage_frontal_area_m2
    #self._fuselage_frontal_area_m2=self.fuselage_w_m*self.fuselage_h_m*math.pi
    self._fuselage_fineness_ratio = self._calc_fuselage_fineness_ratio()
    self._fuselage_cd0_p_cf = self._calc_fuselage_cd0_p_cf()
    self._fuselage_cruise_reynolds = self._calc_fuselage_cruise_reynolds()
    self._fuselage_cf = self._calc_fuselage_cf()
    ## fuselage_cda
    #self._fuselage_cda = None
    #if self.fuselage_cf != None:
    #  self._fuselage_cda = \
    #   self.fuselage_cd0_p_cf*self.fuselage_cf*self.fuselage_frontal_area_m2
    self._fuselage_cd0 = self._calc_fuselage_cd0()
    self._wing_aspect_ratio = self._calc_wing_aspect_ratio()
    self._induced_drag_cdi = self._calc_induced_drag_cdi()
    self._wing_root_chord_m = self._calc_wing_root_chord_m()
    self._wing_mac_m = self._calc_wing_mac_m()
    self._horiz_tail_area_m2 = self._calc_horiz_tail_area_m2()
    self._vert_tail_area_m2 = self._calc_vert_tail_area_m2()
    self._horiz_tail_cd0 = self._calc_horiz_tail_cd0()
    self._vert_tail_cd0 = self._calc_vert_tail_cd0()
    self._landing_gear_cd0 = self._calc_landing_gear_cd0()
    self._stopped_rotor_cd0 = self._calc_stopped_rotor_cd0()
    self._cruise_cd = self._calc_cruise_cd()
    self._cruise_l_p_d = self._calc_cruise_l_p_d()
    self._total_drag_coef = self._calc_total_drag_coef()

    #A Ground Taxi
    self._depart_taxi_avg_shaft_power_kw = \
     self._calc_depart_taxi_avg_shaft_power_kw()
    self._depart_taxi_avg_electric_power_kw = \
     self._calc_depart_taxi_avg_electric_power_kw()
    self._depart_taxi_energy_kw_hr = self._calc_depart_taxi_energy_kw_hr()

    #B Hover Climb
    self._hover_climb_avg_shaft_power_kw = \
     self._calc_hover_climb_avg_shaft_power_kw()
    self._hover_climb_avg_electric_power_kw = \
     self._calc_hover_climb_avg_electric_power_kw()
    self._hover_climb_energy_kw_hr = self._calc_hover_climb_energy_kw_hr()

    #C Transition + Climb
    self._trans_climb_avg_shaft_power_kw = \
     self._calc_trans_climb_avg_shaft_power_kw()
    self._trans_climb_avg_electric_power_kw = \
     self._calc_trans_climb_avg_electric_power_kw()
    self._trans_climb_energy_kw_hr = self._calc_trans_climb_energy_kw_hr()

    #D Departure Terminal Procedures
    self._depart_proc_avg_shaft_power_kw = \
     self._calc_depart_proc_avg_shaft_power_kw()
    self._depart_proc_avg_electric_power_kw = \
     self._calc_depart_proc_avg_electric_power_kw()
    self._depart_proc_energy_kw_hr = self._calc_depart_proc_energy_kw_hr()

    #E Accelerate + Climb
    self._accel_climb_avg_shaft_power_kw = \
     self._calc_accel_climb_avg_shaft_power_kw()
    self._accel_climb_avg_electric_power_kw = \
     self._calc_accel_climb_avg_electric_power_kw()
    self._accel_climb_energy_kw_hr = self._calc_accel_climb_energy_kw_hr()

    #F Cruise
    self._cruise_avg_shaft_power_kw = \
     self._calc_cruise_avg_shaft_power_kw()
    self._cruise_avg_electric_power_kw = \
     self._calc_cruise_avg_electric_power_kw()
    self._cruise_energy_kw_hr = self._calc_cruise_energy_kw_hr()

    #G Decelerate + Descend
    self._decel_descend_avg_shaft_power_kw = \
     self._calc_decel_descend_avg_shaft_power_kw()
    self._decel_descend_avg_electric_power_kw = \
     self._calc_decel_descend_avg_electric_power_kw()
    self._decel_descend_energy_kw_hr = self._calc_decel_descend_energy_kw_hr()

    #H Arrival Terminal Procedures
    self._arrive_proc_avg_shaft_power_kw = \
     self._calc_arrive_proc_avg_shaft_power_kw()
    self._arrive_proc_avg_electric_power_kw = \
     self._calc_arrive_proc_avg_electric_power_kw()
    self._arrive_proc_energy_kw_hr = self._calc_arrive_proc_energy_kw_hr()

    #I Transition +  Descend
    self._trans_descend_avg_shaft_power_kw = \
     self._calc_trans_descend_avg_shaft_power_kw()
    self._trans_descend_avg_electric_power_kw = \
     self._calc_trans_descend_avg_electric_power_kw()
    self._trans_descend_energy_kw_hr = self._calc_trans_descend_energy_kw_hr()

    #J Hover Descend
    self._hover_descend_avg_shaft_power_kw = \
     self._calc_hover_descend_avg_shaft_power_kw()
    self._hover_descend_avg_electric_power_kw = \
     self._calc_hover_descend_avg_electric_power_kw()
    self._hover_descend_energy_kw_hr = self._calc_hover_descend_energy_kw_hr()

    #K Ground Taxi
    self._arrive_taxi_avg_shaft_power_kw = \
     self._calc_arrive_taxi_avg_shaft_power_kw()
    self._arrive_taxi_avg_electric_power_kw = \
     self._calc_arrive_taxi_avg_electric_power_kw()
    self._arrive_taxi_energy_kw_hr = self._calc_arrive_taxi_energy_kw_hr()

    #B' Reserve Hover Climb
    self._reserve_hover_climb_avg_shaft_power_kw = \
     self._calc_reserve_hover_climb_avg_shaft_power_kw()
    self._reserve_hover_climb_avg_electric_power_kw = \
     self._calc_reserve_hover_climb_avg_electric_power_kw()
    self._reserve_hover_climb_energy_kw_hr = self._calc_reserve_hover_climb_energy_kw_hr()

    #C' Reserve Transition Climb
    self._reserve_trans_climb_avg_shaft_power_kw = \
     self._calc_reserve_trans_climb_avg_shaft_power_kw()
    self._reserve_trans_climb_avg_electric_power_kw = \
     self._calc_reserve_trans_climb_avg_electric_power_kw()
    self._reserve_trans_climb_energy_kw_hr = self._calc_reserve_trans_climb_energy_kw_hr()

    #E' Reserve Acceleration Climb
    self._reserve_accel_climb_avg_shaft_power_kw = \
     self._calc_reserve_accel_climb_avg_shaft_power_kw()
    self._reserve_accel_climb_avg_electric_power_kw = \
     self._calc_reserve_accel_climb_avg_electric_power_kw()
    self._reserve_accel_climb_energy_kw_hr = self._calc_reserve_accel_climb_energy_kw_hr()

    #F' Reserve Cruise
    self._reserve_cruise_avg_shaft_power_kw = \
     self._calc_reserve_cruise_avg_shaft_power_kw()
    self._reserve_cruise_avg_electric_power_kw = \
     self._calc_reserve_cruise_avg_electric_power_kw()
    self._reserve_cruise_energy_kw_hr = self._calc_reserve_cruise_energy_kw_hr()

    #G' Reserve Deceleration Descend
    self._reserve_decel_descend_avg_shaft_power_kw = \
     self._calc_reserve_decel_descend_avg_shaft_power_kw()
    self._reserve_decel_descend_avg_electric_power_kw = \
     self._calc_reserve_decel_descend_avg_electric_power_kw()
    self._reserve_decel_descend_energy_kw_hr = self._calc_reserve_decel_descend_energy_kw_hr()

    #I' Reserve Transition Descend
    self._reserve_trans_descend_avg_shaft_power_kw = \
     self._calc_reserve_trans_descend_avg_shaft_power_kw()
    self._reserve_trans_descend_avg_electric_power_kw = \
     self._calc_reserve_trans_descend_avg_electric_power_kw()
    self._reserve_trans_descend_energy_kw_hr = self._calc_reserve_trans_descend_energy_kw_hr()

    #J' Reserve Hover Descend
    self._reserve_hover_descend_avg_shaft_power_kw = \
     self._calc_reserve_hover_descend_avg_shaft_power_kw()
    self._reserve_hover_descend_avg_electric_power_kw = \
     self._calc_reserve_hover_descend_avg_electric_power_kw()
    self._reserve_hover_descend_energy_kw_hr = self._calc_reserve_hover_descend_energy_kw_hr()

    # close JSON file
    ifile.close()

  # ratio of payload mass to max takeoff mass
  def _calc_payload_mass_frac(self):
    return self.payload_kg/self.max_takeoff_mass_kg

  # requires disk_area_m2 from propulsion
  # use MTOM to calculate kg per disk area m2
  # return None if propulsion object not populated
  def _calc_disk_loading_kg_p_m2(self):
    if self.propulsion != None:
      return self.max_takeoff_mass_kg/self.propulsion.disk_area_m2
    else:
      return None

  # requires environ g_m_p_s2, air_density_sea_lvl_kg_p_m3
  # requires propulsion disk_area_m2, rotor_effic
  # prop thrust momentum theory:
  #   F = change in pressure * disk area
  #   change in pressure = 0.5 * air density * (v_e^2-v_0^2); hover means v_0=0
  #   now F = 0.5 * air density * v_e^2 * disk area
  #   for hover F = TOM*g: TOM*g = 0.5 * air density * v_e^2 * disk area
  #   solve for v_e. Power = F*v = g*TOM/1 * (g*TOM)^0.5/(0.5*airdensity*A)^0.5
  #   therefore hover shaft power in watts is given by
  #   ((g*TOM)^1.5/(0.5*airdensity*A)^0.5)/hover_power_effic
  # return None if environ or propulsion object not populated
  def _calc_hover_shaft_power_kw(self):
    if self.environ != None and self.propulsion != None:
      return \
       ((
        (self.environ.g_m_p_s2*self.max_takeoff_mass_kg)**1.5/
        (0.5*self.environ.air_density_sea_lvl_kg_p_m3*\
         self.propulsion.disk_area_m2)**0.5
       )/self.propulsion.rotor_effic)/W_P_KW
    else:
      return None

  # requires aircraft hover_shaft_power_kw
  # requires power epu_effic
  # scale hover_shaft_power by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_hover_electric_power_kw(self):
    if self.hover_shaft_power_kw != None and self.power != None:
      return self.hover_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires environ air_density_max_alt_kg_p_m3
  # stall speed equation solved for wing area
  # return None if environ object not populated
  def _calc_wing_area_m2(self):
    if self.environ != None:
      return \
       (2.0*self.max_takeoff_mass_kg*self.environ.g_m_p_s2)/\
       (self.environ.air_density_max_alt_kg_p_m3*(self.stall_speed_m_p_s**2.0)*\
        self.vehicle_cl_max)
    else:
      return None

  # requires mission cruise_h_m_p_s
  # this calculation replaces stall speed with cruise speed
  # see stall speed equation
  # return None if mission object not populated
  def _calc_cruise_cl(self):
    if self.mission != None:
      return \
       (self.stall_speed_m_p_s**2.0)*self.vehicle_cl_max/\
       (self.mission.cruise_h_m_p_s**2.0)
    else:
      return None

  # Hoerner Eq 13.1 (p 238)
  def _calc_fuselage_fineness_ratio(self):
    return 2.0*self.fuselage_l_m/(self.fuselage_w_m+self.fuselage_h_m)

  # Hoerner Eq 6.31 (p 111)
  def _calc_fuselage_cd0_p_cf(self):
    return \
     3.0*self.fuselage_fineness_ratio+4.5/self.fuselage_fineness_ratio**0.5+\
     21.0/self.fuselage_fineness_ratio**2.0

  # requires environ kinematic_viscosity_max_alt_m2_p_s
  # requires mission cruise_h_m_p_s
  # reynolds number = velocity*length/kinematic viscosity
  # return None if environ or mission object not populated
  def _calc_fuselage_cruise_reynolds(self):
    if self.environ != None and self.mission != None:
      return \
       self.mission.cruise_h_m_p_s*self.fuselage_l_m/\
       self.environ.kinematic_viscosity_max_alt_m2_p_s
    else:
      return None

  # requires aircraft fuselage_cruise_reynolds
  # Prandtl-Schlichting skin friction formula
  # where other additive terms are negligible in this regime
  # return None if aircraft field not populated
  def _calc_fuselage_cf(self):
    if self.fuselage_cruise_reynolds != None:
      return 0.455/math.log10(self.fuselage_cruise_reynolds)**2.58
      # negligible: 
      # +0.0016*self.fuselage_fineness_ratio/self.fuselage_cruise_reynolds**0.4
    else:
      return None

  # requires aircraft fuselage_cf and aircraft wing_area_m2
  # dimensional analysis
  # fuselage_cd0 = fuselage_cda/wing_area_m2
  # where fuselage_cda = fuselage_cd0_p_cf*fuselage_cf*fuselage_reference_area
  # where fuselage_reference_area = pi*((fuselage_w+fuselage_h)/4)**2
  # return None if aircraft field not populated
  def _calc_fuselage_cd0(self):
    if self.fuselage_cf != None and self.wing_area_m2 != None:
      fuselage_reference_area = math.pi*((self.fuselage_w_m+self.fuselage_h_m)/4.0)**2.0
      return (
        self.fuselage_cd0_p_cf*self.fuselage_cf*fuselage_reference_area/self.wing_area_m2
      )
    else:
      return None

  # requires aircraft wing_area_m2
  # wing aspect ratio = wingspan^2/wing area
  # return None if aircraft field not populated
  def _calc_wing_aspect_ratio(self):
    if self.wing_area_m2 != None:
      return self.wingspan_m**2.0/self.wing_area_m2
    else:
      return None

  # requires aircraft cruise_cl, wing_aspect_ratio
  # induced drag coefficient equation
  # return None if aircraft field not populated
  def _calc_induced_drag_cdi(self):
    if self.cruise_cl != None and self.wing_aspect_ratio != None:
      return \
       self.cruise_cl**2.0/\
       (math.pi*self.wing_aspect_ratio*self.span_effic_factor)
    else:
      return None

  # requires aircraft wing_area_m2
  # recall wing aspect ratio = wingspan^2/wing area
  # return None if aircraft field not populated
  def _calc_wing_root_chord_m(self):
    if self.wing_area_m2 != None:
      return 2.0*self.wing_area_m2/(self.wingspan_m*(1.0+self.wing_taper_ratio))
    else:
      return None

  # requires aircraft wing_root_chord_m
  # wing Mean Aerodynamic Chord formula
  # return None if aircraft field not populated
  def _calc_wing_mac_m(self):
    if self.wing_root_chord_m != None:
      return \
       (2.0/3.0)*self.wing_root_chord_m*\
       (1.0+self.wing_taper_ratio**2.0/(1.0+self.wing_taper_ratio))
    else:
      return None

  # requires aircraft wing_area_m2 and wing_mac_m
  # return None if aircraft field not populated
  def _calc_horiz_tail_area_m2(self):
    if self.wing_area_m2 != None and self.wing_mac_m != None:
      return \
       (self.horiz_tail_vol_coeff*self.wing_area_m2*self.wing_mac_m)/\
       (0.5*self.fuselage_l_m)
    else:
      return None

  # requires aircraft wing_area_m2
  # return None if aircraft field not populated
  def _calc_vert_tail_area_m2(self):
    if self.wing_area_m2 != None :
      return \
       (self.vert_tail_vol_coeff*self.wingspan_m*self.wing_area_m2)/\
       (0.5*self.fuselage_l_m)
    else:
      return None

  # requires aircraft horiz_tail_area_m2
  # return None if aircraft field not populated
  def _calc_horiz_tail_cd0(self):
    if self.horiz_tail_area_m2 != None and self.vert_tail_area_m2 != None:
      return (\
       self.horiz_tail_area_m2/(self.wing_area_m2)\
       )*self.empennage_airfoil_cd0
    else:
      return None

  # requires aircraft vert_tail_area_m2
  # return None if aircraft field not populated
  def _calc_vert_tail_cd0(self):
    if self.horiz_tail_area_m2 != None and self.vert_tail_area_m2 != None:
      return (\
       self.vert_tail_area_m2/(self.wing_area_m2)\
       )*self.empennage_airfoil_cd0
    else:
      return None

  # requires aircraft wing_area_m2
  # return None if aircraft field not populated
  def _calc_landing_gear_cd0(self):
    if self.wing_area_m2 != None:
      return self.landing_gear_drag_area_m2/self.wing_area_m2
    else:
      return None

  # requires aircraft wing_area_m2
  # requires propulsion disk_area_m2
  # return None if aircraft field or propulsion object not populated
  def _calc_stopped_rotor_cd0(self):
    if self.wing_area_m2 != None and self.propulsion.disk_area_m2 != None:
      return \
       (self.propulsion.disk_area_m2/self.ratio_disk_to_stopped_rotor_area)/\
       self.wing_area_m2
    else:
      return None

  # requires aircraft fuselage_cd0, induced_drag_cdi, horiz_tail_cd0,
  # vert_tail_cd0, landing_gear_cd0, stopped_rotor_cd0
  # per-component drag buildup
  # return None if aircraft field(s) not populated
  def _calc_cruise_cd(self):
    if self.fuselage_cd0 != None and self.induced_drag_cdi != None and \
       self.horiz_tail_cd0 != None and self.vert_tail_cd0 != None and \
       self.landing_gear_cd0 != None and self.stopped_rotor_cd0 != None:
      return (\
       self.fuselage_cd0+self.wing_airfoil_cd_at_cruise_cl+\
       self.induced_drag_cdi+self.horiz_tail_cd0+self.vert_tail_cd0+\
       self.landing_gear_cd0+self.stopped_rotor_cd0)*self.trim_drag_factor*\
       self.excres_protub_factor
    else:
      return None

  # requires aircraft cruise_cl and cruise_cd
  # dimensional analysis
  # return None if aircraft field not populated
  def _calc_cruise_l_p_d(self):
    if self.cruise_cl != None and self.cruise_cd != None:
      return self.cruise_cl/self.cruise_cd
    else:
      return None
  
  # requires aircraft fields for fuselage, empennage, landing gear, etc.
  # returns total drag coefficient
  def _calc_total_drag_coef(self):
    if self.environ == None or self.wing_area_m2 == None:
      return None
    cd0_sum = 0.0
    if self.fuselage_cd0 != None:
      cd0_sum += self.fuselage_cd0
    if self.horiz_tail_cd0 != None:
      cd0_sum += self.horiz_tail_cd0
    if self.vert_tail_cd0 != None:
      cd0_sum += self.vert_tail_cd0
    if self.landing_gear_cd0 != None:
      cd0_sum += self.landing_gear_cd0
    return cd0_sum

# ----- Depart Taxi (Segment A) -----
  # requires mission depart_taxi_avg_h_m_p_s, depart_taxi_s
  # horizontal power component only, assumes drag effects are negligible
  # assuming an initial velocity of zero, use horizontal distance and time to
  # determine a constant horizontal acceleration and the related end velocity
  # then use MTOM, acceleration, and average velocity to find average power
  # return None if mission object not populated
  def _calc_depart_taxi_avg_shaft_power_kw(self):
    if self.mission != None:
      d_h_m = self.mission.depart_taxi_avg_h_m_p_s*self.mission.depart_taxi_s
      vf_h_m_p_s = (2.0*d_h_m)/self.mission.depart_taxi_s
      a_h_m_p_s2 = vf_h_m_p_s**2.0/(2.0*d_h_m)
      return \
       (self.max_takeoff_mass_kg*a_h_m_p_s2*\
        self.mission.depart_taxi_avg_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft depart_taxi_avg_shaft_power_kw
  # requires power epu_effic
  # scale depart_taxi_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_depart_taxi_avg_electric_power_kw(self):
    if self._depart_taxi_avg_shaft_power_kw != None and self.power != None:
      return self._depart_taxi_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft depart_taxi_avg_electric_power_kw
  # requires mission depart_taxi_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_depart_taxi_energy_kw_hr(self):
    if self._depart_taxi_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._depart_taxi_avg_electric_power_kw*self.mission.depart_taxi_s)/\
       S_P_HR
    else:
      return None

# ----- Hover Climb (Segment B) -----
  # requires mission hover_climb_avg_v_m_p_s, hover_climb_s
  # vertical power component only, includes weight + acceleration effects
  # assuming drag effects are negligible
  # assuming an initial vertical velocity of zero, use vertical distance and time to
  # determine a constant vertical acceleration and the related end velocity
  # then use MTOM, gravity, acceleration, and average velocity to find average power
  # return None if mission or propulsion object not populated
  def _calc_hover_climb_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None:
      d_v_m = self.mission.hover_climb_avg_v_m_p_s*self.mission.hover_climb_s
      vf_v_m_p_s = (2.0*d_v_m)/self.mission.hover_climb_s
      a_v_m_p_s2 = vf_v_m_p_s**2.0/(2.0*d_v_m)
      return \
       (self.max_takeoff_mass_kg*(self.environ.g_m_p_s2+a_v_m_p_s2)*\
        self.mission.hover_climb_avg_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft hover_climb_avg_shaft_power_kw
  # requires power epu_effic
  # scale hover_climb_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_hover_climb_avg_electric_power_kw(self):
    if self._hover_climb_avg_shaft_power_kw != None and self.power != None:
      return self._hover_climb_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft hover_climb_avg_electric_power_kw
  # requires mission hover_climb_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_hover_climb_energy_kw_hr(self):
    if self._hover_climb_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._hover_climb_avg_electric_power_kw*self.mission.hover_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Transition Climb (Segment C) -----
  # requires mission trans_climb_avg_h_m_p_s, trans_climb_v_m_p_s, trans_climb_s
  # includes aerodynamic lift, induced drag, parasite drag, weight, and climb forces
  # return None if mission, propulsion, or environment object not populated
  def _calc_trans_climb_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.trans_climb_avg_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      vehicle_cl = weight_n/(q*self.wing_area_m2)
      lift_n = q*self.wing_area_m2*vehicle_cl

      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal acceleration
      v0_h_m_p_s = 0.0
      vf_h_m_p_s= self.mission.trans_climb_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.trans_climb_s 
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)
        
      # vertical acceleration
      v0_v_m_p_s = self.mission.hover_climb_avg_v_m_p_s
      vf_v_m_p_s = self.mission.trans_climb_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.trans_climb_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components 
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)+self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_h_n*self.mission.trans_climb_avg_h_m_p_s+force_v_n*self.mission.trans_climb_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft trans_climb_avg_shaft_power_kw
  # requires power epu_effic
  # scale trans_climb_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_trans_climb_avg_electric_power_kw(self):
    if self._trans_climb_avg_shaft_power_kw != None and self.power != None:
      return self._trans_climb_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft trans_climb_avg_electric_power_kw
  # requires mission trans_climb_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_trans_climb_energy_kw_hr(self):
    if self._trans_climb_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._trans_climb_avg_electric_power_kw*self.mission.trans_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Depart Procedures (Segment D) -----
  # requires mission depart_proc_h_m_p_s, depart_proc_s
  # horizontal power component only
  # includes aerodynamic lift, induced drag, parasite drag, weight, and horizontal motion
  # return None if mission, propulsion, or environment object not populated
  def _calc_depart_proc_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.depart_proc_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      lift_n = weight_n
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = self.mission.trans_climb_avg_h_m_p_s
      vf_h_m_p_s = self.mission.depart_proc_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.depart_proc_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # force components 
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2

      return (force_h_n*self.mission.depart_proc_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft depart_proc_avg_shaft_power_kw
  # requires power epu_effic
  # scale depart_proc_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_depart_proc_avg_electric_power_kw(self):
    if self._depart_proc_avg_shaft_power_kw != None and self.power != None:
      return self._depart_proc_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft depart_proc_avg_electric_power_kw
  # requires mission depart_proc_s
  # calculate total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_depart_proc_energy_kw_hr(self):
    if self._depart_proc_avg_electric_power_kw != None and self.mission != None:
      return (self._depart_proc_avg_electric_power_kw*self.mission.depart_proc_s)/S_P_HR
    else:
      return None

# ----- Accelerate Climb (Segment E) -----
  # requires mission accel_climb_avg_h_m_p_s, accel_climb_v_m_p_s, accel_climb_s
  # includes aerodynamic lift, induced drag, parasite drag, weight, and climb forces
  # return None if mission, propulsion, or environment object not populated
  def _calc_accel_climb_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.accel_climb_avg_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      vehicle_cl = weight_n/(q*self.wing_area_m2)
      lift_n = q*self.wing_area_m2*vehicle_cl
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = self.mission.depart_proc_h_m_p_s
      vf_h_m_p_s = self.mission.accel_climb_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.accel_climb_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical accelerations
      v0_v_m_p_s = 0.0
      vf_v_m_p_s = self.mission.accel_climb_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.accel_climb_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)+self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_h_n*self.mission.accel_climb_avg_h_m_p_s+force_v_n*self.mission.accel_climb_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft accel_climb_avg_shaft_power_kw
  # requires power epu_effic
  # scale accel_climb_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_accel_climb_avg_electric_power_kw(self):
    if self._accel_climb_avg_shaft_power_kw != None and self.power != None:
      return self._accel_climb_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft accel_climb_avg_electric_power_kw
  # requires mission accel_climb_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_accel_climb_energy_kw_hr(self):
    if self._accel_climb_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._accel_climb_avg_electric_power_kw*self.mission.accel_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Cruise (Segment F) -----
  # requires mission cruise_h_m_p_s, cruise_s
  # horizontal power component only
  # includes aerodynamic lift, induced drag, parasite drag, weight, and horizontal motion
  # return None if mission, propulsion, or environment object not populated
  def _calc_cruise_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_max_alt_kg_p_m3*self.mission.cruise_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      lift_n = weight_n
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      if self.wing_airfoil_cd_at_cruise_cl != None and self.stopped_rotor_cd0 != None:
        cd0_cruise = cd0+self.wing_airfoil_cd_at_cruise_cl+self.stopped_rotor_cd0
      else:
        cd0_cruise = cd0
      dp_n = q*self.wing_area_m2*cd0_cruise
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      return (total_drag_n*self.mission.cruise_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft cruise_shaft_power_kw
  # requires power epu_effic
  # scale cruise_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_cruise_avg_electric_power_kw(self):
    if self.cruise_avg_shaft_power_kw != None and self.power != None:
      return self.cruise_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None
    
  # requires aircraft cruise_avg_electric_power_kw
  # requires mission cruise_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_cruise_energy_kw_hr(self):
    if self._cruise_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._cruise_avg_electric_power_kw*self.mission.cruise_s)/\
       S_P_HR
    else:
      return None

# ----- Decelerate Descend (Segment G) -----
  # requires mission decel_descend_avg_h_m_p_s, decel_descend_v_m_p_s, decel_descend_s
  # includes aerodynamic lift, induced drag, parasite drag, weight, and descent forces
  # return None if mission, propulsion, or environment object not populated
  def _calc_decel_descend_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.decel_descend_avg_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      vehicle_cl = weight_n/(q*self.wing_area_m2)
      lift_n = q*self.wing_area_m2*vehicle_cl
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = self.mission.cruise_h_m_p_s
      vf_h_m_p_s = self.mission.decel_descend_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.decel_descend_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m) 

      # vertical accelerations
      v0_v_m_p_s = 0.0
      vf_v_m_p_s = self.mission.decel_descend_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.decel_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)-self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_h_n*self.mission.decel_descend_avg_h_m_p_s+force_v_n*self.mission.decel_descend_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft decel_descend_avg_shaft_power_kw
  # requires power epu_effic
  # scale decel_descend_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_decel_descend_avg_electric_power_kw(self):
    if self._decel_descend_avg_shaft_power_kw != None and self.power != None:
      return self._decel_descend_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft decel_descend_avg_electric_power_kw
  # requires mission decel_descend_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_decel_descend_energy_kw_hr(self):
    if self._decel_descend_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._decel_descend_avg_electric_power_kw*self.mission.decel_descend_s)/\
       S_P_HR
    else:
      return None

# ----- Arrive Procedures (Segment H) -----
  # requires mission arrive_proc_h_m_p_s, arrive_proc_s
  # horizontal power component only
  # includes aerodynamic lift, induced drag, parasite drag, weight, and horizontal motion
  # return None if mission, propulsion, or environment object not populated
  def _calc_arrive_proc_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.arrive_proc_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      # horizontal component
      lift_n = weight_n
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = self.mission.decel_descend_avg_h_m_p_s
      vf_h_m_p_s = self.mission.arrive_proc_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.arrive_proc_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # force components
      force_h_n = max(0.0, total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2)

      return (force_h_n*self.mission.arrive_proc_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft arrive_proc_avg_shaft_power_kw
  # requires power epu_effic
  # scale arrive_proc_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_arrive_proc_avg_electric_power_kw(self):
    if self._arrive_proc_avg_shaft_power_kw != None and self.power != None:
      return self._arrive_proc_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft arrive_proc_avg_electric_power_kw
  # requires mission arrive_proc_s
  # calculate total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_arrive_proc_energy_kw_hr(self):
    if self._arrive_proc_avg_electric_power_kw != None and self.mission != None:
      return (self._arrive_proc_avg_electric_power_kw*self.mission.arrive_proc_s)/S_P_HR
    else:
      return None

# ----- Transition Descend (Segment I) -----
  # requires mission trans_descend_avg_h_m_p_s, trans_descend_v_m_p_s, trans_descend_s
  # includes aerodynamic lift, induced drag, parasite drag, weight, and descent forces
  # return None if mission, propulsion, or environment object not populated
  def _calc_trans_descend_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.trans_descend_avg_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      vehicle_cl = weight_n/(q*self.wing_area_m2)
      lift_n = q*self.wing_area_m2*vehicle_cl

      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = self.mission.arrive_proc_h_m_p_s
      vf_h_m_p_s = self.mission.trans_descend_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.trans_descend_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical accelerations
      v0_v_m_p_s = 0.0
      vf_v_m_p_s = self.mission.trans_descend_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.trans_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)-self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_h_n*self.mission.trans_descend_avg_h_m_p_s+force_v_n*self.mission.trans_descend_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft trans_descend_avg_shaft_power_kw
  # requires power epu_effic
  # scale trans_descend_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_trans_descend_avg_electric_power_kw(self):
    if self._trans_descend_avg_shaft_power_kw != None and self.power != None:
      return self._trans_descend_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft trans_descend_avg_electric_power_kw
  # requires mission trans_descend_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_trans_descend_energy_kw_hr(self):
    if self._trans_descend_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._trans_descend_avg_electric_power_kw*self.mission.trans_descend_s)/\
       S_P_HR
    else:
      return None

# ----- Hover Descend (Segment J) -----
  # requires mission hover_descend_avg_v_m_p_s, hover_descend_s
  # vertical power component only, includes weight - acceleration effects
  # assuming drag effects are negligible
  # return None if mission or propulsion object not populated
  def _calc_hover_descend_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      # vertical accelerations
      v0_v_m_p_s = self.mission.trans_descend_v_m_p_s
      vf_v_m_p_s = self.mission.hover_descend_avg_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.hover_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force component
      force_v_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2-self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_v_n*vf_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)

  # requires aircraft hover_descend_avg_shaft_power_kw
  # requires power epu_effic
  # scale hover_descend_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_hover_descend_avg_electric_power_kw(self):
    if self._hover_descend_avg_shaft_power_kw != None and self.power != None:
      return self._hover_descend_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft hover_descend_avg_electric_power_kw
  # requires mission hover_descend_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_hover_descend_energy_kw_hr(self):
    if self._hover_descend_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._hover_descend_avg_electric_power_kw*self.mission.hover_descend_s)/\
       S_P_HR
    else:
      return None

# ----- Arrive Taxi (Segment K) -----
  # requires mission arrive_taxi_avg_h_m_p_s, arrive_taxi_s
  # horizontal power component only, assumes drag effects are negligible
  # assuming drag effects are negligible  
  # return None if mission object not populated
  def _calc_arrive_taxi_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      # horizontal accelerations
      v0_h_m_p_s = 0.0  
      vf_h_m_p_s = self.mission.arrive_taxi_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.arrive_taxi_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # horizontal force 
      force_h_n = self.max_takeoff_mass_kg*a_h_m_p_s2

      return (force_h_n*vf_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft arrive_taxi_avg_shaft_power_kw
  # requires power epu_effic
  # scale arrive_taxi_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_arrive_taxi_avg_electric_power_kw(self):
    if self._arrive_taxi_avg_shaft_power_kw != None and self.power != None:
      return self._arrive_taxi_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft arrive_taxi_avg_electric_power_kw
  # requires mission arrive_taxi_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_arrive_taxi_energy_kw_hr(self):
    if self._arrive_taxi_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._arrive_taxi_avg_electric_power_kw*self.mission.arrive_taxi_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Hover Climb (Segment B') -----
  # requires mission reserve_hover_climb_avg_v_m_p_s, reserve_hover_climb_s
  # vertical power component only, includes weight + acceleration effects
  # assuming drag effects are negligible
  # assuming an initial vertical velocity of zero, use vertical distance and time to
  # determine a constant vertical acceleration and the related end velocity
  # then use MTOM, gravity, acceleration, and average velocity to find average power
  # return None if mission or propulsion object not populated
  def _calc_reserve_hover_climb_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None:
      d_v_m = self.mission.reserve_hover_climb_avg_v_m_p_s*self.mission.reserve_hover_climb_s
      vf_v_m_p_s = (2.0*d_v_m)/self.mission.reserve_hover_climb_s
      a_v_m_p_s2 = vf_v_m_p_s**2.0/(2.0*d_v_m)
      return \
       (self.max_takeoff_mass_kg*(self.environ.g_m_p_s2+a_v_m_p_s2)*\
        self.mission.reserve_hover_climb_avg_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft reserve_hover_climb_avg_shaft_power_kw
  # requires power epu_effic
  # scale reserve_hover_climb_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_reserve_hover_climb_avg_electric_power_kw(self):
    if self._reserve_hover_climb_avg_shaft_power_kw != None and self.power != None:
      return self._reserve_hover_climb_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None
      
  # requires aircraft reserve_hover_climb_avg_electric_power_kw
  # requires mission reserve_hover_climb_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_reserve_hover_climb_energy_kw_hr(self):
    if self._reserve_hover_climb_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._reserve_hover_climb_avg_electric_power_kw*self.mission.reserve_hover_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Transition Climb (Segment C') -----
  # requires mission reserve_trans_climb_avg_h_m_p_s, reserve_trans_climb_v_m_p_s, reserve_trans_climb_s
  # includes aerodynamic lift, induced drag, parasite drag, weight, and climb forces
  # return None if mission, propulsion, or environment object not populated
  def _calc_reserve_trans_climb_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.reserve_trans_climb_avg_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      vehicle_cl = weight_n/(q*self.wing_area_m2)
      lift_n = q*self.wing_area_m2*vehicle_cl
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = 0.0
      vf_h_m_p_s = self.mission.reserve_trans_climb_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.reserve_trans_climb_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical accelerations
      v0_v_m_p_s = self.mission.reserve_hover_climb_avg_v_m_p_s
      vf_v_m_p_s = self.mission.reserve_trans_climb_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.reserve_trans_climb_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0 - v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)+self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_h_n*self.mission.reserve_trans_climb_avg_h_m_p_s+force_v_n*self.mission.reserve_trans_climb_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft reserve_trans_climb_avg_shaft_power_kw
  # requires power epu_effic
  # scale reserve_trans_climb_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_reserve_trans_climb_avg_electric_power_kw(self):
    if self._reserve_trans_climb_avg_shaft_power_kw != None and self.power != None:
      return self._reserve_trans_climb_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft reserve_trans_climb_avg_electric_power_kw
  # requires mission reserve_trans_climb_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_reserve_trans_climb_energy_kw_hr(self):
    if self._reserve_trans_climb_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._reserve_trans_climb_avg_electric_power_kw*self.mission.reserve_trans_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Acceleration Climb (Segment E') -----
  # requires mission reserve_accel_climb_avg_h_m_p_s, reserve_accel_climb_v_m_p_s, reserve_accel_climb_s
  # includes aerodynamic lift, induced drag, parasite drag, weight, and climb forces
  # return None if mission, propulsion, or environment object not populated
  def _calc_reserve_accel_climb_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.reserve_accel_climb_avg_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      vehicle_cl = weight_n/(q*self.wing_area_m2)
      lift_n = q*self.wing_area_m2*vehicle_cl
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor
      
      # horizontal accelerations
      v0_h_m_p_s = self.mission.reserve_trans_climb_avg_h_m_p_s
      vf_h_m_p_s = self.mission.reserve_accel_climb_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.reserve_accel_climb_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical accelerations
      v0_v_m_p_s = self.mission.reserve_trans_climb_v_m_p_s
      vf_v_m_p_s = self.mission.reserve_accel_climb_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.reserve_accel_climb_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0 - v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n + self.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n - lift_n) + self.max_takeoff_mass_kg*a_v_m_p_s2
      return (force_h_n*self.mission.reserve_accel_climb_avg_h_m_p_s + force_v_n*self.mission.reserve_accel_climb_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft reserve_accel_climb_avg_shaft_power_kw
  # requires power epu_effic
  # scale reserve_accel_climb_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_reserve_accel_climb_avg_electric_power_kw(self):
    if self._reserve_accel_climb_avg_shaft_power_kw != None and self.power != None:
      return self._reserve_accel_climb_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft reserve_accel_climb_avg_electric_power_kw
  # requires mission reserve_accel_climb_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_reserve_accel_climb_energy_kw_hr(self):
    if self._reserve_accel_climb_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._reserve_accel_climb_avg_electric_power_kw*self.mission.reserve_accel_climb_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Cruise (Segment F') -----
  # requires mission reserve_cruise_h_m_p_s, reserve_cruise_s
  # horizontal power component only
  # includes aerodynamic lift, induced drag, parasite drag, weight, and horizontal motion
  # return None if mission, propulsion, or environment object not populated
  def _calc_reserve_cruise_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_max_alt_kg_p_m3*self.mission.reserve_cruise_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      lift_n = weight_n
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      if self.wing_airfoil_cd_at_cruise_cl != None and self.stopped_rotor_cd0 != None:
        cd0_cruise = cd0+self.wing_airfoil_cd_at_cruise_cl+self.stopped_rotor_cd0
      else:
        cd0_cruise = cd0
      dp_n = q*self.wing_area_m2*cd0_cruise
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      return (total_drag_n*self.mission.reserve_cruise_h_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft reserve_cruise_shaft_power_kw
  # requires power epu_effic
  # scale reserve_cruise_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_reserve_cruise_avg_electric_power_kw(self):
    if self.reserve_cruise_avg_shaft_power_kw != None and self.power != None:
      return self.reserve_cruise_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None
    
  # requires aircraft reserve_cruise_avg_electric_power_kw
  # requires mission reserve_cruise_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_reserve_cruise_energy_kw_hr(self):
    if self._reserve_cruise_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._reserve_cruise_avg_electric_power_kw*self.mission.reserve_cruise_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Deceleration Descend (Segment G') -----
  # requires mission reserve_decel_descend_avg_h_m_p_s, reserve_decel_descend_v_m_p_s, reserve_decel_descend_s
  # includes aerodynamic lift, induced drag, parasite drag, weight, and descent forces
  # return None if mission, propulsion, or environment object not populated
  def _calc_reserve_decel_descend_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.reserve_decel_descend_avg_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      vehicle_cl = weight_n/(q*self.wing_area_m2)
      lift_n = q*self.wing_area_m2*vehicle_cl
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal acceleration
      v0_h_m_p_s = self.mission.reserve_cruise_h_m_p_s
      vf_h_m_p_s = self.mission.reserve_decel_descend_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.reserve_decel_descend_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0 - v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical acceleration 
      v0_v_m_p_s = 0.0
      vf_v_m_p_s = self.mission.reserve_decel_descend_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.reserve_decel_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n-self.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)-self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_h_n*self.mission.reserve_decel_descend_avg_h_m_p_s+force_v_n*self.mission.reserve_decel_descend_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft reserve_decel_descend_avg_shaft_power_kw
  # requires power epu_effic
  # scale reserve_decel_descend_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_reserve_decel_descend_avg_electric_power_kw(self):
    if self._reserve_decel_descend_avg_shaft_power_kw != None and self.power != None:
      return self._reserve_decel_descend_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft reserve_decel_descend_avg_electric_power_kw
  # requires mission reserve_decel_descend_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_reserve_decel_descend_energy_kw_hr(self):
    if self._reserve_decel_descend_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._reserve_decel_descend_avg_electric_power_kw*self.mission.reserve_decel_descend_s)/\
       S_P_HR
    else:
      return None

# ----- Reserve Transition Descend (Segment I') -----
  # requires mission reserve_trans_descend_avg_h_m_p_s, reserve_trans_descend_v_m_p_s, reserve_trans_descend_s
  # includes aerodynamic lift, induced drag, parasite drag, weight, and descend forces
  # return None if mission, propulsion, or environment object not populated
  def _calc_reserve_trans_descend_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:    
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*self.mission.reserve_trans_descend_avg_h_m_p_s**2.0
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      vehicle_cl = weight_n/(q*self.wing_area_m2)
      lift_n = q*self.wing_area_m2*vehicle_cl
      
      # induced drag
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)
      # parasite drag
      cd0 = self._calc_total_drag_coef()
      if cd0 == None:
        return None
      dp_n = q*self.wing_area_m2*cd0
      # total drag
      total_drag_n = (di_n+dp_n)*self.trim_drag_factor*self.excres_protub_factor

      # horizontal accelerations
      v0_h_m_p_s = self.mission.reserve_decel_descend_avg_h_m_p_s
      vf_h_m_p_s = self.mission.reserve_trans_descend_avg_h_m_p_s
      d_h_m = 0.5*(v0_h_m_p_s+vf_h_m_p_s)*self.mission.reserve_trans_descend_s
      a_h_m_p_s2 = (vf_h_m_p_s**2.0-v0_h_m_p_s**2.0)/(2.0*d_h_m)

      # vertical acceleration 
      v0_v_m_p_s = self.mission.reserve_decel_descend_v_m_p_s
      vf_v_m_p_s = self.mission.reserve_trans_descend_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.reserve_trans_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force components
      force_h_n = total_drag_n+self.max_takeoff_mass_kg*a_h_m_p_s2
      force_v_n = (weight_n-lift_n)-self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_h_n*self.mission.reserve_trans_descend_avg_h_m_p_s+force_v_n*self.mission.reserve_trans_descend_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft reserve_trans_descend_avg_shaft_power_kw
  # requires power epu_effic
  # scale reserve_trans_descend_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_reserve_trans_descend_avg_electric_power_kw(self):
    if self._reserve_trans_descend_avg_shaft_power_kw != None and self.power != None:
      return self._reserve_trans_descend_avg_shaft_power_kw / self.power.epu_effic
    else:
      return None

  # requires aircraft reserve_trans_descend_avg_electric_power_kw
  # requires mission reserve_trans_descend_s
  # calculate the total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_reserve_trans_descend_energy_kw_hr(self):
    if self._reserve_trans_descend_avg_electric_power_kw != None and self.mission != None:
      return \
       (self._reserve_trans_descend_avg_electric_power_kw * self.mission.reserve_trans_descend_s) / \
       S_P_HR
    else:
      return None

# ----- Reserve Hover Descend (Segment J') -----
  # requires mission reserve_hover_descend_avg_v_m_p_s, reserve_hover_descend_s
  # vertical power component only, includes weight - acceleration effects
  # assuming drag effects are negligible
  # assuming an initial vertical velocity of zero, use vertical distance and time to
  # determine a constant vertical acceleration and the related end velocity
  # then use MTOM, gravity, acceleration, and average velocity to find average power
  # return None if mission or propulsion object not populated
  def _calc_reserve_hover_descend_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None:
      # vertical accelerations
      v0_v_m_p_s = self.mission.reserve_trans_descend_v_m_p_s
      vf_v_m_p_s = self.mission.reserve_hover_descend_avg_v_m_p_s
      d_v_m = 0.5*(v0_v_m_p_s+vf_v_m_p_s)*self.mission.reserve_hover_descend_s
      a_v_m_p_s2 = (vf_v_m_p_s**2.0-v0_v_m_p_s**2.0)/(2.0*d_v_m)

      # force component
      force_v_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2-self.max_takeoff_mass_kg*a_v_m_p_s2

      return (force_v_n*vf_v_m_p_s)/(self.propulsion.rotor_effic*W_P_KW)

  # requires aircraft reserve_hover_descend_avg_shaft_power_kw
  # requires power epu_effic
  # scale reserve_hover_descend_avg_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_reserve_hover_descend_avg_electric_power_kw(self):
    if self._reserve_hover_descend_avg_shaft_power_kw != None and self.power != None:
      return self._reserve_hover_descend_avg_shaft_power_kw/self.power.epu_effic
    else:
      return None

  # requires aircraft reserve_hover_descend_avg_electric_power_kw
  # requires mission reserve_hover_descend_s
  # calculate total energy and convert to kW*hr
  # return None if aircraft field or power object not populated
  def _calc_reserve_hover_descend_energy_kw_hr(self):
    if self._reserve_hover_descend_avg_electric_power_kw != None and self.mission != None:
      return \
      (self._reserve_hover_descend_avg_electric_power_kw*self.mission.reserve_hover_descend_s)/\
      S_P_HR
    else:
      return None

  def _calc_total_mission_energy_kw_hr(self):
    segments = [
      self._depart_taxi_energy_kw_hr,
      self._hover_climb_energy_kw_hr,
      self._trans_climb_energy_kw_hr,
      self._depart_proc_energy_kw_hr,
      self._accel_climb_energy_kw_hr,
      self._cruise_energy_kw_hr,
      self._decel_descend_energy_kw_hr,
      self._arrive_proc_energy_kw_hr,
      self._trans_descend_energy_kw_hr,
      self._hover_descend_energy_kw_hr,
      self._arrive_taxi_energy_kw_hr,
      self._reserve_hover_climb_energy_kw_hr,
      self._reserve_trans_climb_energy_kw_hr,
      self._reserve_accel_climb_energy_kw_hr,
      self._reserve_cruise_energy_kw_hr,
      self._reserve_decel_descend_energy_kw_hr,
      self._reserve_trans_descend_energy_kw_hr,
      self._reserve_hover_descend_energy_kw_hr,
    ]
    total_energy_kw_hr = sum(e for e in segments if e is not None)
    if total_energy_kw_hr > 0:
      return total_energy_kw_hr  
    else:
      return None
    
  def _calc_battery_mass_kg(self):
    total_energy_kw_hr = self._calc_total_mission_energy_kw_hr()
    batt_inaccessible_energy_frac = 1-self.power.batt_inaccessible_energy_frac
    if total_energy_kw_hr != None and self.power != None:
      return (total_energy_kw_hr*1000.0)/(self.power.batt_spec_energy_w_h_p_kg*batt_inaccessible_energy_frac)
    else:
        return None

#   def _calc_empty_mass_kg(self):
#     structural_mass = (
#       self.wing_mass_kg +
#       self.horiz_tail_mass_kg +
#       self.vert_tail_mass_kg +
#       self.fuselage_mass_kg +
#       self.boom_mass_kg +
#       self.landing_gear_mass_kg +
#       self.epu_mass_kg +
#       self.lift_rotor_hub_mass_kg +
#       self.tilt_rotor_mass_kg
#     )    
#     subsys_mass = (
#       self.actuator_mass_kg +
#       self.furnishings_mass_kg +
#       self.environmental_control_system_mass_kg +
#       self.avionics_mass_kg +
#       self.hivolt_power_dist_mass_kg +
#       self.lovolt_power_coms_mass_kg
#     )
#     subtotal = structural_mass + subsys_mass
#     return subtotal * (1.0 + self.mass_margin_factor)

# def _iterate_mtow(self, tol=1e-3, max_iter=100):
#     mtow_guess = self.max_takeoff_mass_kg  

#     for i in range(max_iter):
#         self.max_takeoff_mass_kg = mtow_guess  

#         battery_mass = self._calc_battery_mass_kg()
#         empty_mass = self._calc_empty_mass_kg()
#         new_mtow = empty_mass + self.payload_kg + battery_mass

#         if abs(new_mtow - mtow_guess) < tol:
#             self.max_takeoff_mass_kg = new_mtow
#             return new_mtow

#         mtow_guess = new_mtow

#     self.max_takeoff_mass_kg = mtow_guess
#     return mtow_guess

  @property
  def max_takeoff_mass_kg(self):
    return self._max_takeoff_mass_kg

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

  @property
  def hover_shaft_power_kw(self):
    return self._hover_shaft_power_kw

  @property
  def wing_area_m2(self):
    return self._wing_area_m2
 
  @property
  def cruise_cl(self):
    return self._cruise_cl

  #@property
  #def fuselage_frontal_area_m2(self):
  #  return self._fuselage_frontal_area_m2

  @property
  def fuselage_fineness_ratio(self):
    return self._fuselage_fineness_ratio

  @property
  def fuselage_cd0_p_cf(self):
    return self._fuselage_cd0_p_cf

  @property
  def fuselage_cruise_reynolds(self):
    return self._fuselage_cruise_reynolds

  @property
  def fuselage_cf(self):
    return self._fuselage_cf

  #@property
  #def fuselage_cda(self):
  #  return self._fuselage_cda

  @property
  def fuselage_cd0(self):
    return self._fuselage_cd0

  @property
  def wing_aspect_ratio(self):
    return self._wing_aspect_ratio

  @property
  def induced_drag_cdi(self):
    return self._induced_drag_cdi

  @property
  def wing_root_chord_m(self):
    return self._wing_root_chord_m

  @property
  def wing_mac_m(self):
    return self._wing_mac_m

  @property
  def horiz_tail_area_m2(self):
    return self._horiz_tail_area_m2

  @property
  def vert_tail_area_m2(self):
    return self._vert_tail_area_m2

  @property
  def horiz_tail_cd0(self):
    return self._horiz_tail_cd0

  @property
  def vert_tail_cd0(self):
    return self._vert_tail_cd0

  @property
  def landing_gear_cd0(self):
    return self._landing_gear_cd0

  @property
  def stopped_rotor_cd0(self):
    return self._stopped_rotor_cd0

  @property
  def cruise_cd(self):
    return self._cruise_cd

  @property
  def cruise_l_p_d(self):
    return self._cruise_l_p_d
  
  @property
  def total_drag_coef(self):
    return self._total_drag_coef

  @property
  def depart_taxi_avg_shaft_power_kw(self):
    return self._depart_taxi_avg_shaft_power_kw

  @property
  def depart_taxi_avg_electric_power_kw(self):
    return self._depart_taxi_avg_electric_power_kw

  @property
  def depart_taxi_energy_kw_hr(self):
    return self._depart_taxi_energy_kw_hr

  @property
  def hover_climb_avg_shaft_power_kw(self):
    return self._hover_climb_avg_shaft_power_kw
  
  @property
  def hover_climb_avg_electric_power_kw(self):
    return self._hover_climb_avg_electric_power_kw
  
  @property
  def hover_climb_energy_kw_hr(self):
    return self._hover_climb_energy_kw_hr
    
  @property
  def trans_climb_avg_shaft_power_kw(self):
    return self._trans_climb_avg_shaft_power_kw
  
  @property
  def trans_climb_avg_electric_power_kw(self):
    return self._trans_climb_avg_electric_power_kw
  
  @property
  def trans_climb_energy_kw_hr(self):
    return self._trans_climb_energy_kw_hr

  @property
  def depart_proc_avg_shaft_power_kw(self):
    return self._depart_proc_avg_shaft_power_kw
  
  @property
  def depart_proc_avg_electric_power_kw(self):
    return self._depart_proc_avg_electric_power_kw
  
  @property
  def depart_proc_energy_kw_hr(self):
    return self._depart_proc_energy_kw_hr

  @property
  def accel_climb_avg_shaft_power_kw(self):
    return self._accel_climb_avg_shaft_power_kw
  
  @property
  def accel_climb_avg_electric_power_kw(self):
    return self._accel_climb_avg_electric_power_kw
  
  @property
  def accel_climb_energy_kw_hr(self):
    return self._accel_climb_energy_kw_hr

  @property
  def cruise_avg_shaft_power_kw(self):
    return self._cruise_avg_shaft_power_kw
  
  @property
  def cruise_avg_electric_power_kw(self):
    return self._cruise_avg_electric_power_kw

  @property
  def cruise_energy_kw_hr(self):
    return self._cruise_energy_kw_hr
  
  @property
  def decel_descend_avg_shaft_power_kw(self):
    return self._decel_descend_avg_shaft_power_kw
  
  @property
  def decel_descend_avg_electric_power_kw(self):
    return self._decel_descend_avg_electric_power_kw

  @property
  def decel_descend_energy_kw_hr(self):
    return self._decel_descend_energy_kw_hr
    
  @property
  def arrive_proc_avg_shaft_power_kw(self):
    return self._arrive_proc_avg_shaft_power_kw
  
  @property
  def arrive_proc_avg_electric_power_kw(self):
    return self._arrive_proc_avg_electric_power_kw

  @property
  def arrive_proc_energy_kw_hr(self):
    return self._arrive_proc_energy_kw_hr
  
  @property
  def trans_descend_avg_shaft_power_kw(self):
    return self._trans_descend_avg_shaft_power_kw
  
  @property
  def trans_descend_avg_electric_power_kw(self):
    return self._trans_descend_avg_electric_power_kw

  @property
  def trans_descend_energy_kw_hr(self):
    return self._trans_descend_energy_kw_hr

  @property
  def hover_descend_avg_shaft_power_kw(self):
    return self._hover_descend_avg_shaft_power_kw
  
  @property
  def hover_descend_avg_electric_power_kw(self):
    return self._hover_descend_avg_electric_power_kw

  @property
  def hover_descend_energy_kw_hr(self):
    return self._hover_descend_energy_kw_hr
  
  @property
  def arrive_taxi_avg_shaft_power_kw(self):
    return self._arrive_taxi_avg_shaft_power_kw
  
  @property
  def arrive_taxi_avg_electric_power_kw(self):
    return self._arrive_taxi_avg_electric_power_kw

  @property
  def arrive_taxi_energy_kw_hr(self):
    return self._arrive_taxi_energy_kw_hr

  @property
  def reserve_hover_climb_avg_shaft_power_kw(self):
    return self._reserve_hover_climb_avg_shaft_power_kw
  
  @property
  def reserve_hover_climb_avg_electric_power_kw(self):
    return self._reserve_hover_climb_avg_electric_power_kw

  @property
  def reserve_hover_climb_energy_kw_hr(self):
    return self._reserve_hover_climb_energy_kw_hr

  @property
  def reserve_trans_climb_avg_shaft_power_kw(self):
    return self._reserve_trans_climb_avg_shaft_power_kw
  
  @property
  def reserve_trans_climb_avg_electric_power_kw(self):
    return self._reserve_trans_climb_avg_electric_power_kw

  @property
  def reserve_trans_climb_energy_kw_hr(self):
    return self._reserve_trans_climb_energy_kw_hr
  
  @property
  def reserve_accel_climb_avg_shaft_power_kw(self):
    return self._reserve_accel_climb_avg_shaft_power_kw
  
  @property
  def reserve_accel_climb_avg_electric_power_kw(self):
    return self._reserve_accel_climb_avg_electric_power_kw

  @property
  def reserve_accel_climb_energy_kw_hr(self):
    return self._reserve_accel_climb_energy_kw_hr
  
  @property
  def reserve_cruise_avg_shaft_power_kw(self):
    return self._reserve_cruise_avg_shaft_power_kw
  
  @property
  def reserve_cruise_avg_electric_power_kw(self):
    return self._reserve_cruise_avg_electric_power_kw

  @property
  def reserve_cruise_energy_kw_hr(self):
    return self._reserve_cruise_energy_kw_hr

  @property
  def reserve_decel_descend_avg_shaft_power_kw(self):
    return self._reserve_decel_descend_avg_shaft_power_kw
  
  @property
  def reserve_decel_descend_avg_electric_power_kw(self):
    return self._reserve_decel_descend_avg_electric_power_kw

  @property
  def reserve_decel_descend_energy_kw_hr(self):
    return self._reserve_decel_descend_energy_kw_hr

  @property
  def reserve_trans_descend_avg_shaft_power_kw(self):
    return self._reserve_trans_descend_avg_shaft_power_kw
  
  @property
  def reserve_trans_descend_avg_electric_power_kw(self):
    return self._reserve_trans_descend_avg_electric_power_kw

  @property
  def reserve_trans_descend_energy_kw_hr(self):
    return self._reserve_trans_descend_energy_kw_hr
    
  @property
  def reserve_hover_descend_avg_shaft_power_kw(self):
    return self._reserve_hover_descend_avg_shaft_power_kw
  
  @property
  def reserve_hover_descend_avg_electric_power_kw(self):
    return self._reserve_hover_descend_avg_electric_power_kw

  @property
  def reserve_hover_descend_energy_kw_hr(self):
    return self._reserve_hover_descend_energy_kw_hr

  @property
  def total_mission_energy_kw_hr(self):
    return self._total_mission_energy_kw_hr



# Testing
aircraft = Aircraft(r'C:\Users\khoan\Code\evtolpy\analysis\mission-segment-energy\cfg\test-all.json')
print("total_energy_kw_hr", aircraft._calc_total_mission_energy_kw_hr())
print("\n")
# Checking: Cd0 (test_aircraft.py)
cd0_sum = 0.0
print("fuselage", aircraft.fuselage_cd0)
print("horiz_tail", aircraft.horiz_tail_cd0)
print("landing_gear", aircraft.landing_gear_cd0)
print("vert_tail", aircraft.vert_tail_cd0)
print("cd0_sum", cd0_sum)
print("\n")
cd0_sum += aircraft.wing_airfoil_cd_at_cruise_cl
cd0_sum += aircraft.stopped_rotor_cd0
print("stopped_rotor", aircraft.stopped_rotor_cd0)
print("wing_airfoil_cd_at_cruise_cl", aircraft.wing_airfoil_cd_at_cruise_cl)
print("cd0_sum_cruise", cd0_sum)
print("\n")
print("fuselage_fineness_ratio", aircraft.fuselage_fineness_ratio)
print("fuselage_cd0_p_cf", aircraft.fuselage_cd0_p_cf)
print("fuselage_cruise_reynolds", aircraft.fuselage_cruise_reynolds)
print("fuselage_cf", aircraft.fuselage_cf)
print("wing_area", aircraft.wing_area_m2)
print("horiz_tail_area_m2", aircraft.horiz_tail_area_m2)
print("vert_tail_area_m2", aircraft.vert_tail_area_m2)
print("disk_area", aircraft.propulsion.disk_area_m2)
