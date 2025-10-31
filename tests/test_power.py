# test_power.py
#
# Tests Power class
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import sys      # not needed when using as a package
import unittest # unittest

# path to directory containing Power class; use before deploying as package
sys.path.append('../evtol')
from power import Power

# comment above and uncomment below when ready to deploy as package
#from ..evtol.power import Power

class TestPower(unittest.TestCase):
  def test_power_ctor(self):
    power = Power('../sample-inputs/test-power.json')
    self.assertEqual(power.batt_spec_energy_w_h_p_kg, 232.5)
    self.assertEqual(power.batt_inaccessible_energy_frac, 0.05)
    self.assertEqual(power.batt_eol_capacity, 0.80)
    self.assertEqual(power.batt_int_factor, 0.65)
    self.assertEqual(power.epu_effic, 0.90)
    self.assertEqual(power.hover_power_effic, 0.70)

if __name__ == '__main__':
  unittest.main()
