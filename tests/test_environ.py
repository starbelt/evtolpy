# test_environ.py
#
# Unit tests for Environ
#
# Written by First Last
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.environ import Environ # environment model
from helpers import TEST_ALL_JSON # shared test paths


class TestEnviron(unittest.TestCase):

  def test_constructor_loads_sample_input(self):
    environ = Environ(str(TEST_ALL_JSON))

    self.assertAlmostEqual(environ.g_m_p_s2, 9.81)
    self.assertAlmostEqual(environ.sound_speed_m_p_s, 334.5)
    self.assertAlmostEqual(environ.air_density_sea_lvl_kg_p_m3, 1.226)
    self.assertAlmostEqual(environ.air_density_max_alt_kg_p_m3, 1.056)
    self.assertAlmostEqual(environ.kinematic_viscosity_sea_lvl_m2_p_s, 1.412e-5)
    self.assertAlmostEqual(environ.kinematic_viscosity_max_alt_m2_p_s, 1.281e-5)

  def test_equality_uses_environment_fields(self):
    self.assertEqual(Environ(str(TEST_ALL_JSON)), Environ(str(TEST_ALL_JSON)))
    self.assertNotEqual(Environ(str(TEST_ALL_JSON)), object())


if __name__ == '__main__':
  unittest.main()
