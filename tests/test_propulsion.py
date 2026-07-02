# test_propulsion.py
#
# Unit tests for Propulsion
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import math # pi
import unittest # unit testing

# import eVTOLpy modules
from evtol.propulsion import Propulsion # propulsion model
from helpers import TEST_ALL_JSON # shared test paths


class TestPropulsion(unittest.TestCase):

  def test_constructor_loads_sample_input(self):
    propulsion = Propulsion(str(TEST_ALL_JSON))

    self.assertAlmostEqual(propulsion.rotor_effic, 0.80)
    self.assertEqual(propulsion.rotor_count, 12)
    self.assertEqual(propulsion.lift_rotor_count, 6)
    self.assertEqual(propulsion.tilt_rotor_count, 6)
    self.assertEqual(propulsion.pusher_rotor_count, 1)
    self.assertAlmostEqual(propulsion.rotor_diameter_m, 2.0)
    self.assertAlmostEqual(propulsion.pusher_rotor_diameter_m, 1.5)
    self.assertAlmostEqual(propulsion.tip_mach, 0.4)
    self.assertAlmostEqual(propulsion.pusher_rotor_tip_mach, 0.55)
    self.assertAlmostEqual(propulsion.rotor_avg_cl, 0.625)

  def test_disk_area_updates_when_rotor_count_changes(self):
    propulsion = Propulsion(str(TEST_ALL_JSON))
    propulsion.rotor_count = 4

    self.assertAlmostEqual(propulsion.disk_area_m2, 4.0*math.pi)

  def test_equality_uses_propulsion_fields(self):
    self.assertEqual(Propulsion(str(TEST_ALL_JSON)), Propulsion(str(TEST_ALL_JSON)))
    self.assertNotEqual(Propulsion(str(TEST_ALL_JSON)), object())


if __name__ == '__main__':
  unittest.main()
