# test_aircraft_battery.py
#
# Unit tests for aircraft battery calculations
#
# Written by First Last
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from helpers import make_aircraft # shared constructors


class TestAircraftBattery(unittest.TestCase):

  def test_cccv_charge_time_valid_input(self):
    aircraft = make_aircraft()

    result = aircraft._estimate_cccv_charge_time_hr(100.0, 50.0)

    self.assertAlmostEqual(result['t_cc_hr'], 1.6842105263157894)
    self.assertAlmostEqual(result['t_cv_hr'], 1.0594314346383504)
    self.assertAlmostEqual(result['t_charge_hr'], 2.7436419609541396)
    self.assertAlmostEqual(result['P_dc_kw'], 47.5)
    self.assertEqual(result['charger_limit_indicator_flag'], 'charger_limited')

  def test_cccv_charge_time_invalid_inputs_return_none(self):
    aircraft = make_aircraft()

    self.assertIsNone(aircraft._estimate_cccv_charge_time_hr(None, 50.0))
    self.assertIsNone(aircraft._estimate_cccv_charge_time_hr(100.0, 0.0))
    self.assertIsNone(aircraft._estimate_cccv_charge_time_hr(100.0, 50.0, eta_charger_dc=1.5))

  def test_cccv_charge_time_no_charge_needed(self):
    aircraft = make_aircraft()

    result = aircraft._estimate_cccv_charge_time_hr(100.0, 50.0, soc_start=1.0)

    self.assertEqual(result['t_cc_hr'], 0.0)
    self.assertEqual(result['t_cv_hr'], 0.0)
    self.assertEqual(result['t_charge_hr'], 0.0)


if __name__ == '__main__':
  unittest.main()
