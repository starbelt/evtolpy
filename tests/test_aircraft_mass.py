# test_aircraft_mass.py
#
# Unit tests for aircraft mass calculations
#
# Written by First Last
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.aircraft_modules import aircraft_mass # mass functions
from helpers import make_aircraft # shared constructors


class TestAircraftMass(unittest.TestCase):

  def test_mass_properties_match_sample_input(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft.payload_mass_frac, 0.14299212598425196)
    self.assertAlmostEqual(aircraft.landing_gear_mass_kg, 127.04445)
    self.assertAlmostEqual(aircraft.single_epu_mass_kg, 33.38511823097128)
    self.assertAlmostEqual(aircraft.epu_mass_kg, 400.6214187716554)
    self.assertAlmostEqual(aircraft.battery_mass_kg, 1161.6578149152995)
    self.assertAlmostEqual(aircraft.empty_mass_kg, 1855.8310771922668)

  def test_wrapper_delegates_to_mass_module(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft._calc_payload_mass_frac(), aircraft_mass._calc_payload_mass_frac(aircraft))
    self.assertAlmostEqual(aircraft._calc_landing_gear_mass_kg(), aircraft_mass._calc_landing_gear_mass_kg(aircraft))

  def test_missing_power_returns_none_for_battery_mass(self):
    class DummyAircraft:
      power = None

    self.assertIsNone(aircraft_mass._calc_battery_mass_kg(DummyAircraft()))


if __name__ == '__main__':
  unittest.main()
