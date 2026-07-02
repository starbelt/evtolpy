# test_power.py
#
# Unit tests for Power
#
# Written by First Last
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.power import Power # power model
from helpers import TEST_ALL_JSON # shared test paths


class TestPower(unittest.TestCase):

  def test_constructor_loads_sample_input(self):
    power = Power(str(TEST_ALL_JSON))

    self.assertAlmostEqual(power.batt_spec_energy_w_h_p_kg, 232.5)
    self.assertAlmostEqual(power.batt_inaccessible_energy_frac, 0.05)
    self.assertAlmostEqual(power.batt_eol_capacity, 0.80)
    self.assertAlmostEqual(power.batt_int_factor, 0.65)
    self.assertAlmostEqual(power.epu_effic, 0.90)
    self.assertAlmostEqual(power.hover_power_effic, 0.70)

  def test_usable_specific_energy_calculations(self):
    power = Power(str(TEST_ALL_JSON))

    self.assertAlmostEqual(power._calc_batt_bol_usable_spec_energy_w_h_p_kg(), 143.56875)
    self.assertAlmostEqual(power._calc_batt_eol_usable_spec_energy_w_h_p_kg(), 114.855)

  def test_equality_uses_power_fields(self):
    self.assertEqual(Power(str(TEST_ALL_JSON)), Power(str(TEST_ALL_JSON)))
    self.assertNotEqual(Power(str(TEST_ALL_JSON)), object())


if __name__ == '__main__':
  unittest.main()
