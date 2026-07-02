# test_aircraft_aero.py
#
# Unit tests for aircraft aerodynamic calculations
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.aircraft_modules import aircraft_aero # aerodynamic functions
from helpers import make_aircraft # shared constructors


class TestAircraftAero(unittest.TestCase):

  def test_aero_properties_match_sample_input(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft.cruise_cl, 0.6092006369921888)
    self.assertAlmostEqual(aircraft.fuselage_cd0_p_cf, 21.04457034029739)
    self.assertAlmostEqual(aircraft.fuselage_cruise_reynolds, 43266666.666666664)
    self.assertAlmostEqual(aircraft.fuselage_cf, 0.002399909191678042)
    self.assertAlmostEqual(aircraft.fuselage_cd0, 0.0046991536977740965)
    self.assertAlmostEqual(aircraft.induced_drag_cdi, 0.009726020488818618)
    self.assertAlmostEqual(aircraft.landing_gear_cd0, 0.026539154701518457)
    self.assertAlmostEqual(aircraft.cruise_cd, 0.17841243176854113)
    self.assertAlmostEqual(aircraft.cruise_l_p_d, 3.8646029164002704)
    self.assertAlmostEqual(aircraft.total_drag_coef, 0.033332846678054404)

  def test_wrapper_delegates_to_aero_module(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft._calc_cruise_cl(), aircraft_aero._calc_cruise_cl(aircraft))
    self.assertAlmostEqual(aircraft._calc_cruise_cd(), aircraft_aero._calc_cruise_cd(aircraft))

  def test_missing_mission_returns_none_for_cruise_cl(self):
    class DummyAircraft:
      mission = None

    self.assertIsNone(aircraft_aero._calc_cruise_cl(DummyAircraft()))


if __name__ == '__main__':
  unittest.main()
