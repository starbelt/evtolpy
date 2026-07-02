# test_aircraft_geometry.py
#
# Unit tests for aircraft geometry calculations
#
# Written by First Last
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.aircraft_modules import aircraft_geometry # geometry functions
from helpers import make_aircraft # shared constructors


class TestAircraftGeometry(unittest.TestCase):

  def test_geometry_properties_match_sample_input(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft.wing_area_m2, 14.819612923749114)
    self.assertAlmostEqual(aircraft.wing_root_chord_m, 1.5461255006519679)
    self.assertAlmostEqual(aircraft.wing_aspect_ratio, 15.18258278118905)
    self.assertAlmostEqual(aircraft.wing_mac_m, 1.093082500274179)
    self.assertAlmostEqual(aircraft.horiz_tail_area_m2, 3.0672311298715753)
    self.assertAlmostEqual(aircraft.vert_tail_area_m2, 2.106143294332819)
    self.assertAlmostEqual(aircraft.fuselage_fineness_ratio, 6.233962264150942)

  def test_wrapper_delegates_to_geometry_module(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft._calc_wing_area_m2(), aircraft_geometry._calc_wing_area_m2(aircraft))
    self.assertAlmostEqual(aircraft._calc_wing_root_chord_m(), aircraft_geometry._calc_wing_root_chord_m(aircraft))

  def test_missing_environment_returns_none_for_wing_area(self):
    class DummyAircraft:
      environ = None

    self.assertIsNone(aircraft_geometry._calc_wing_area_m2(DummyAircraft()))


if __name__ == '__main__':
  unittest.main()
