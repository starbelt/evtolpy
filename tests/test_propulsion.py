# test_propulsion.py
#
# Tests Propulsion class
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import sys      # not needed when using as a package
import unittest # unittest

# path to directory containing Propulsion class; use before deploying as package
sys.path.append('../evtol')
from propulsion import Propulsion

# comment above and uncomment below when ready to deploy as package
#from ..evtol.propulsion import Propulsion

class TestPropulsion(unittest.TestCase):
  def test_propulsion_ctor(self):
    propulsion = Propulsion('../sample-inputs/test-propulsion.json')
    self.assertEqual(propulsion.rotor_effic, 0.80)
    self.assertEqual(propulsion.rotor_count, 12)
    self.assertEqual(propulsion.lift_rotor_count, 6)
    self.assertEqual(propulsion.tilt_rotor_count, 6)
    self.assertEqual(propulsion.rotor_diameter_m, 2.0)
    self.assertEqual(propulsion.tip_mach, 0.4)
    self.assertEqual(propulsion.rotor_avg_cl, 0.625)

if __name__ == '__main__':
  unittest.main()
