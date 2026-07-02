# test_aircraft_iteration.py
#
# Unit tests for aircraft MTOW iteration
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.aircraft_modules import aircraft_iteration # iteration functions
from helpers import make_aircraft # shared constructors


class TestAircraftIteration(unittest.TestCase):

  def test_iterate_mtow_converges_for_sample_input(self):
    aircraft = make_aircraft()

    mtow_kg, history = aircraft.iterate_mtow

    self.assertAlmostEqual(mtow_kg, 4076.0876439129397)
    self.assertEqual(len(history), 37)
    self.assertLess(abs(history[-1]['delta_kg']), 1e-3)
    self.assertAlmostEqual(history[-1]['payload_mass_kg'], aircraft.payload_kg)

  def test_invalid_initial_mtow_raises_value_error(self):
    aircraft = make_aircraft()
    aircraft.max_takeoff_mass_kg = 0.0

    with self.assertRaises(ValueError):
      aircraft_iteration._iterate_mtow(aircraft)


if __name__ == '__main__':
  unittest.main()
