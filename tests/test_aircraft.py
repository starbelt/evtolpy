# test_aircraft.py
#
# Tests Aircraft class
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris
#
# See the LICENSE file for the license

# import Python modules
import sys      # not needed when using as a package
import unittest # unittest

# path to directory containing Aircraft class; use before deploying as package
sys.path.append('../evtol')
from aircraft import Aircraft
from environ import Environ
from mission import Mission
from power import Power
from propulsion import Propulsion

# comment above and uncomment below when ready to deploy as package
#from ..evtol.aircraft import Aircraft
#from ..evtol.environ import Environ
#from ..evtol.mission import Mission
#from ..evtol.power import Power
#from ..evtol.propulsion import Propulsion

class TestAircraft(unittest.TestCase):
  def test_aircraft_ctor1(self):
    aircraft = Aircraft('../sample-inputs/test-aircraft.json')
    self.assertEqual(aircraft.max_takeoff_mass_kg, 3175.0)
    self.assertEqual(aircraft.payload_kg, 454.0)
    self.assertEqual(aircraft.vehicle_cl_max, 2.08)
    self.assertEqual(aircraft.wing_taper_ratio, 0.278)
    self.assertEqual(aircraft.wingspan_m, 15.0)
    self.assertEqual(aircraft.d_value_m, 15.75)
    self.assertEqual(aircraft.stall_speed_m_p_s, 40.6)
    self.assertEqual(aircraft.fuselage_l_m, 8.26)
    self.assertEqual(aircraft.fuselage_w_m, 1.30)
    self.assertEqual(aircraft.fuselage_h_m, 1.35)
    self.assertEqual(aircraft.wing_airfoil_cd_at_cruise_cl, 0.007)
    self.assertEqual(aircraft.empennage_airfoil_cd0, 0.006)
    self.assertEqual(aircraft.span_effic_factor, 0.8)
    self.assertEqual(aircraft.trim_drag_factor, 1.02)
    self.assertEqual(aircraft.landing_gear_drag_area_m2, 0.3933)
    self.assertEqual(aircraft.excres_protub_factor, 1.02)
    self.assertEqual(aircraft.horiz_tail_vol_coeff, 0.7820)
    self.assertEqual(aircraft.vert_tail_vol_coeff, 0.03913)
    self.assertEqual(aircraft.ratio_disk_to_stopped_rotor_area, 20.95)
    self.assertEqual(aircraft.wing_t_p_c, 0.1208)
    self.assertEqual(aircraft.actuator_mass_kg, 81.6)
    self.assertEqual(aircraft.furnishings_mass_kg, 52.0)
    self.assertEqual(aircraft.environmental_control_system_mass_kg, 40.0)
    self.assertEqual(aircraft.avionics_mass_kg, 60.0)
    self.assertEqual(aircraft.hivolt_power_dist_mass_kg, 80.0)
    self.assertEqual(aircraft.lovolt_power_coms_mass_kg, 41.0)
    self.assertEqual(aircraft.mass_margin_factor, 0.05)
    self.assertEqual(aircraft.environ, None)
    self.assertEqual(aircraft.mission, None)
    self.assertEqual(aircraft.power, None)
    self.assertEqual(aircraft.propulsion, None)

  def test_aircraft_ctor2(self):
    aircraft = Aircraft('../sample-inputs/test-all.json')
    self.assertEqual(aircraft.max_takeoff_mass_kg, 3175.0)
    self.assertEqual(aircraft.payload_kg, 454.0)
    self.assertEqual(aircraft.vehicle_cl_max, 2.08)
    self.assertEqual(aircraft.wing_taper_ratio, 0.278)
    self.assertEqual(aircraft.wingspan_m, 15.0)
    self.assertEqual(aircraft.d_value_m, 15.75)
    self.assertEqual(aircraft.stall_speed_m_p_s, 40.6)
    self.assertEqual(aircraft.fuselage_l_m, 8.26)
    self.assertEqual(aircraft.fuselage_w_m, 1.30)
    self.assertEqual(aircraft.fuselage_h_m, 1.35)
    self.assertEqual(aircraft.wing_airfoil_cd_at_cruise_cl, 0.007)
    self.assertEqual(aircraft.empennage_airfoil_cd0, 0.006)
    self.assertEqual(aircraft.span_effic_factor, 0.8)
    self.assertEqual(aircraft.trim_drag_factor, 1.02)
    self.assertEqual(aircraft.landing_gear_drag_area_m2, 0.3933)
    self.assertEqual(aircraft.excres_protub_factor, 1.02)
    self.assertEqual(aircraft.horiz_tail_vol_coeff, 0.7820)
    self.assertEqual(aircraft.vert_tail_vol_coeff, 0.03913)
    self.assertEqual(aircraft.ratio_disk_to_stopped_rotor_area, 20.95)
    self.assertEqual(aircraft.wing_t_p_c, 0.1208)
    self.assertEqual(aircraft.actuator_mass_kg, 81.6)
    self.assertEqual(aircraft.furnishings_mass_kg, 52.0)
    self.assertEqual(aircraft.environmental_control_system_mass_kg, 40.0)
    self.assertEqual(aircraft.avionics_mass_kg, 60.0)
    self.assertEqual(aircraft.hivolt_power_dist_mass_kg, 80.0)
    self.assertEqual(aircraft.lovolt_power_coms_mass_kg, 41.0)
    self.assertEqual(aircraft.mass_margin_factor, 0.05)
    self.assertEqual(aircraft.environ,Environ('../sample-inputs/test-all.json'))
    self.assertEqual(aircraft.mission,Mission('../sample-inputs/test-all.json'))
    self.assertEqual(aircraft.power,Power('../sample-inputs/test-all.json'))
    self.assertEqual(
     aircraft.propulsion,Propulsion('../sample-inputs/test-all.json')
    )
    
if __name__ == '__main__':
  unittest.main()
