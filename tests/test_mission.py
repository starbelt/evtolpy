# test_mission.py
#
# Unit tests for Mission
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import unittest # unit testing

# import eVTOLpy modules
from evtol.mission import Mission # mission model
from helpers import TEST_ALL_JSON # shared test paths


class TestMission(unittest.TestCase):

  def test_constructor_loads_sample_input(self):
    mission = Mission(str(TEST_ALL_JSON))

    self.assertAlmostEqual(mission.depart_taxi_avg_h_m_p_s, 1.34)
    self.assertAlmostEqual(mission.depart_taxi_s, 30.0)
    self.assertAlmostEqual(mission.hover_climb_avg_v_m_p_s, 2.54)
    self.assertAlmostEqual(mission.trans_climb_avg_h_m_p_s, 24.4)
    self.assertAlmostEqual(mission.accel_climb_s, 143.0)
    self.assertAlmostEqual(mission.cruise_h_m_p_s, 67.1)
    self.assertAlmostEqual(mission.cruise_s, 664.0)
    self.assertAlmostEqual(mission.reserve_cruise_s, 54.0)
    self.assertAlmostEqual(mission.reserve_hover_descend_s, 12.0)

  def test_equality_uses_mission_fields(self):
    self.assertEqual(Mission(str(TEST_ALL_JSON)), Mission(str(TEST_ALL_JSON)))
    self.assertNotEqual(Mission(str(TEST_ALL_JSON)), object())


if __name__ == '__main__':
  unittest.main()
