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
    self._cruise_shaft_power_kw = self._calc_cruise_shaft_power_kw()
    self._cruise_electric_power_kw = self._calc_cruise_electric_power_kw()

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


    #E Accelerate + Climb


    #F Cruise


    #G Decelerate + Descend


    #H Arrival Terminal Procedures


    #I Transition +  Descend


    #J Hover Descend


    #K Ground Taxi


    #L Reserves


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

  # requires aircraft fuselage_cf
  # dimensional analysis
  # alternative calculation:
  #   fuselage_cd0 = fuselage_cda/wing_area_m2
  #   where fuselage_cda = fuselage_cd0_p_cf*fuselage_cf*fuselage_reference_area
  #   where fuselage_reference_area = pi*((fuselage_w+fuselage_h)/4)**2
  # return None if aircraft field not populated
  def _calc_fuselage_cd0(self):
    if self.fuselage_cf != None:
      return self.fuselage_cd0_p_cf*self.fuselage_cf
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

  # requires aircraft horiz_tail_area_m2, vert_tail_area_m2
  # return None if aircraft field not populated
  def _calc_horiz_tail_cd0(self):
    if self.horiz_tail_area_m2 != None and self.vert_tail_area_m2 != None:
      return (\
       self.horiz_tail_area_m2/(self.horiz_tail_area_m2+self.vert_tail_area_m2)\
       )*self.empennage_airfoil_cd0
    else:
      return None

  # requires aircraft horiz_tail_area_m2, vert_tail_area_m2
  # return None if aircraft field not populated
  def _calc_vert_tail_cd0(self):
    if self.horiz_tail_area_m2 != None and self.vert_tail_area_m2 != None:
      return (\
       self.vert_tail_area_m2/(self.horiz_tail_area_m2+self.vert_tail_area_m2)\
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

  # requires aircraft cruise_l_p_d
  # Use MTOM*g/L/D for drag force, convert to power with cruise velocity (P=Fv),
  # and scale by rotor efficiency. Convert from W to kW.
  # return None if aircraft field not populated
  def _calc_cruise_shaft_power_kw(self):
    if self.cruise_l_p_d != None:
      return \
       ((self.max_takeoff_mass_kg*self.environ.g_m_p_s2)/self.cruise_l_p_d)*\
       self.mission.cruise_h_m_p_s/(self.propulsion.rotor_effic*W_P_KW)
    else:
      return None

  # requires aircraft cruise_shaft_power_kw
  # requires power epu_effic
  # scale cruise_shaft_power_kw by epu_effic
  # return None if aircraft field or power object not populated
  def _calc_cruise_electric_power_kw(self):
    if self.cruise_shaft_power_kw != None and self.power != None:
      return self.cruise_shaft_power_kw/self.power.epu_effic
    else:
      return None

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
        self.mission.depart_taxi_avg_h_m_p_s)/W_P_KW
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
  # assumes steady transition climb at average horizontal + vertical speeds
  # return None if mission, propulsion, or environment object not populated
  def _calc_trans_climb_avg_shaft_power_kw(self):
    if self.mission != None and self.propulsion != None and self.environ != None:
      v_h = self.mission.trans_climb_avg_h_m_p_s
      v_v = self.mission.trans_climb_v_m_p_s
      v_total = (v_h**2.0 + v_v**2.0)**0.5

      # weight and lift 
      weight_n = self.max_takeoff_mass_kg*self.environ.g_m_p_s2
      q = 0.5*self.environ.air_density_sea_lvl_kg_p_m3*v_total**2.0
      lift_n = q*self.wing_area_m2*self.vehicle_cl_max

      # induced drag 
      di_n = (lift_n**2.0)/(q*self.wing_area_m2*math.pi*self.wing_aspect_ratio*self.span_effic_factor)

      # parasite drag
      cd0_sum = 0.0
      if self.fuselage_cd0 != None:
        cd0_sum += self.fuselage_cd0
      cd0_sum += self.wing_airfoil_cd_at_cruise_cl
      if self.horiz_tail_cd0 != None:
        cd0_sum += self.horiz_tail_cd0
      if self.vert_tail_cd0 != None:
        cd0_sum += self.vert_tail_cd0
      if self.landing_gear_cd0 != None:
        cd0_sum += self.landing_gear_cd0
      if self.stopped_rotor_cd0 != None:
        cd0_sum += self.stopped_rotor_cd0
      dp_n = q*self.wing_area_m2*cd0_sum

      # total drag
      drag_n = (di_n + dp_n) * self.trim_drag_factor * self.excres_protub_factor

      # climb force
      if v_h != 0.0:
        climb_force_n = (weight_n-lift_n)*(v_v/v_h)
      else:
        climb_force_n = (weight_n-lift_n)*(v_v/(v_total if v_total != 0.0 else 1.0))

      # thrust required 
      thrust_n = drag_n + climb_force_n

      return (thrust_n * v_total) / (self.propulsion.rotor_effic * W_P_KW)
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
  def cruise_shaft_power_kw(self):
    return self._cruise_shaft_power_kw
  
  @property
  def cruise_electric_power_kw(self):
    return self._cruise_electric_power_kw

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
    