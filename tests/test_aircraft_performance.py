# test_aircraft_performance.py
#
# Unit tests for aircraft performance calculations
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.aircraft_modules import aircraft_performance # performance functions
from helpers import make_aircraft # shared constructors


class TestAircraftPerformance(unittest.TestCase):

  def test_performance_properties_match_sample_input(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft.hover_shaft_power_kw, 816.7615284878701)
    self.assertAlmostEqual(aircraft.hover_electric_power_kw, 907.5128094309667)
    self.assertAlmostEqual(aircraft.depart_taxi_avg_shaft_power_kw, 0.47508583333333343)
    self.assertAlmostEqual(aircraft.depart_taxi_avg_electric_power_kw, 0.5278731481481482)
    self.assertAlmostEqual(aircraft.depart_taxi_energy_kw_hr, 0.004398942901234568)
    self.assertAlmostEqual(aircraft.total_mission_energy_kw_hr, 166.7777604151209)
    self.assertAlmostEqual(aircraft.total_reserve_mission_energy_kw_hr, 20.638472747045686)

  def test_wrapper_delegates_to_performance_module(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft._calc_hover_shaft_power_kw(), aircraft_performance._calc_hover_shaft_power_kw(aircraft))
    self.assertAlmostEqual(aircraft._calc_total_mission_energy_kw_hr(), aircraft_performance._calc_total_mission_energy_kw_hr(aircraft))

  def test_zero_duration_depart_taxi_returns_zero(self):
    class Mission:
      depart_taxi_avg_h_m_p_s = 1.0
      depart_taxi_s = 0.0

    class Propulsion:
      rotor_effic = 0.8

    class DummyAircraft:
      mission = Mission()
      propulsion = Propulsion()
      max_takeoff_mass_kg = 1000.0

    self.assertEqual(aircraft_performance._calc_depart_taxi_avg_shaft_power_kw(DummyAircraft()), 0.0)

  def test_missing_mission_returns_none_for_depart_taxi_power(self):
    class DummyAircraft:
      mission = None

    self.assertIsNone(aircraft_performance._calc_depart_taxi_avg_shaft_power_kw(DummyAircraft()))


if __name__ == '__main__':
  unittest.main()
