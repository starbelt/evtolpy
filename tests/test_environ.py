# test_environ.py
#
# Tests Environ class
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import sys      # not needed when using as a package
import unittest # unittest

# path to directory containing Environ class; use before deploying as package
sys.path.append('../evtol')
from environ import Environ

# comment above and uncomment below when ready to deploy as package
#from ..evtol.environ import Environ

class TestEnviron(unittest.TestCase):
  def test_environ_ctor(self):
    environ = Environ('../sample-inputs/test-environ.json')
    self.assertEqual(environ.g_m_p_s2, 9.81)
    self.assertEqual(environ.sound_speed_m_p_s, 334.5)
    self.assertEqual(environ.air_density_sea_lvl_kg_p_m3, 1.226)
    self.assertEqual(environ.air_density_max_alt_kg_p_m3, 1.056)
    self.assertEqual(environ.kinematic_viscosity_sea_lvl_m2_p_s, 1.412e-5)
    self.assertEqual(environ.kinematic_viscosity_max_alt_m2_p_s, 1.281e-5)

if __name__ == '__main__':
  unittest.main()
