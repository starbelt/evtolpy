# test_aircraft.py
#
# Unit tests for Aircraft construction
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.environ import Environ # environment model
from evtol.mission import Mission # mission model
from evtol.power import Power # power model
from evtol.propulsion import Propulsion # propulsion model
from helpers import make_aircraft # shared constructors


class TestAircraft(unittest.TestCase):

  def test_constructor_loads_aircraft_and_subsystems(self):
    aircraft = make_aircraft()

    self.assertAlmostEqual(aircraft.max_takeoff_mass_kg, 3175.0)
    self.assertAlmostEqual(aircraft.payload_kg, 454.0)
    self.assertAlmostEqual(aircraft.vehicle_cl_max, 2.08)
    self.assertAlmostEqual(aircraft.cruise_wing_lift_fraction, 0.8)
    self.assertIsInstance(aircraft.environ, Environ)
    self.assertIsInstance(aircraft.mission, Mission)
    self.assertIsInstance(aircraft.power, Power)
    self.assertIsInstance(aircraft.propulsion, Propulsion)

  def test_max_takeoff_mass_setter_updates_value(self):
    aircraft = make_aircraft()

    aircraft.max_takeoff_mass_kg = 3200.0

    self.assertAlmostEqual(aircraft.max_takeoff_mass_kg, 3200.0)


if __name__ == '__main__':
  unittest.main()
