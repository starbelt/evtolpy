# test_aircraft_propulsion.py
#
# Unit tests for aircraft propulsion calculations
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.aircraft_modules import aircraft_propulsion # propulsion functions
from helpers import make_aircraft # shared constructors


class TestAircraftPropulsion(unittest.TestCase):

  def test_propulsion_properties_match_sample_input(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft.disk_loading_kg_p_m2, 84.21949071946129)
    self.assertAlmostEqual(aircraft.over_torque_factor, 1.56)
    self.assertAlmostEqual(aircraft.rotor_solidity, 0.3613683845432632)
    self.assertAlmostEqual(aircraft.pusher_rotor_rpm, 2342.442452426516)
    self.assertAlmostEqual(aircraft.pusher_motor_torque_nm, 2472.3797046426025)

  def test_wrapper_delegates_to_propulsion_module(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft._calc_disk_loading_kg_p_m2(), aircraft_propulsion._calc_disk_loading_kg_p_m2(aircraft))
    self.assertAlmostEqual(aircraft._calc_over_torque_factor(), aircraft_propulsion._calc_over_torque_factor(aircraft))

  def test_invalid_rotor_count_returns_none_for_over_torque(self):
    class Propulsion:
      rotor_count = 2

    class DummyAircraft:
      propulsion = Propulsion()

    self.assertIsNone(aircraft_propulsion._calc_over_torque_factor(DummyAircraft()))

  def test_no_pusher_rotor_returns_zero_for_pusher_rpm(self):
    class Propulsion:
      pusher_rotor_count = 0

    class DummyAircraft:
      propulsion = Propulsion()
      environ = object()

    self.assertEqual(aircraft_propulsion._calc_pusher_rotor_rpm(DummyAircraft()), 0.0)


if __name__ == '__main__':
  unittest.main()
