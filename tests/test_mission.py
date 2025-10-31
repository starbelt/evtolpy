# test_mission.py
#
# Tests Mission class
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import sys      # not needed when using as a package
import unittest # unittest

# path to directory containing Mission class; use before deploying as package
sys.path.append('../evtol')
from mission import Mission

# comment above and uncomment below when ready to deploy as package
#from ..evtol.mission import Mission

class TestMission(unittest.TestCase):
  def test_mission_ctor(self):
    mission = Mission('../sample-inputs/test-mission.json')
    self.assertEqual(mission.depart_taxi_avg_h_m_p_s, 1.34)
    self.assertEqual(mission.depart_taxi_s, 30.0)
    self.assertEqual(mission.hover_climb_avg_v_m_p_s, 2.54)
    self.assertEqual(mission.hover_climb_s, 12.0)
    self.assertEqual(mission.trans_climb_avg_h_m_p_s, 24.4)
    self.assertEqual(mission.trans_climb_v_m_p_s, 5.1)
    self.assertEqual(mission.trans_climb_s, 30.0)
    self.assertEqual(mission.depart_proc_h_m_p_s, 48.8)
    self.assertEqual(mission.depart_proc_s, 18.0)
    self.assertEqual(mission.accel_climb_avg_h_m_p_s, 58.0)
    self.assertEqual(mission.accel_climb_v_m_p_s, 5.1)
    self.assertEqual(mission.accel_climb_s, 143.0)
    self.assertEqual(mission.cruise_h_m_p_s, 67.1)
    self.assertEqual(mission.cruise_s, 664.0)
    self.assertEqual(mission.decel_descend_avg_h_m_p_s, 58.0)
    self.assertEqual(mission.decel_descend_v_m_p_s, 5.1)
    self.assertEqual(mission.decel_descend_s, 143.0)
    self.assertEqual(mission.arrive_proc_h_m_p_s, 48.8)
    self.assertEqual(mission.arrive_proc_s, 18.0)
    self.assertEqual(mission.trans_descend_avg_h_m_p_s, 24.4)
    self.assertEqual(mission.trans_descend_v_m_p_s, 5.1)
    self.assertEqual(mission.trans_descend_s, 30.0)
    self.assertEqual(mission.hover_descend_avg_v_m_p_s, 2.54)
    self.assertEqual(mission.hover_descend_s, 12.0)
    self.assertEqual(mission.arrive_taxi_avg_h_m_p_s, 1.34)
    self.assertEqual(mission.arrive_taxi_s, 30.0)
    self.assertEqual(mission.reserve_hover_climb_avg_v_m_p_s, 2.54)
    self.assertEqual(mission.reserve_hover_climb_s, 12.0)
    self.assertEqual(mission.reserve_trans_climb_avg_h_m_p_s, 24.4)
    self.assertEqual(mission.reserve_trans_climb_v_m_p_s, 5.1)
    self.assertEqual(mission.reserve_trans_climb_s, 30.0)
    self.assertEqual(mission.reserve_accel_climb_avg_h_m_p_s, 58.0)
    self.assertEqual(mission.reserve_accel_climb_v_m_p_s, 5.1)
    self.assertEqual(mission.reserve_accel_climb_s, 24.0)
    self.assertEqual(mission.reserve_cruise_h_m_p_s, 67.1)
    self.assertEqual(mission.reserve_cruise_s, 54.0)
    self.assertEqual(mission.reserve_decel_descend_avg_h_m_p_s, 58.0)
    self.assertEqual(mission.reserve_decel_descend_v_m_p_s, 5.1)
    self.assertEqual(mission.reserve_decel_descend_s, 24.0)
    self.assertEqual(mission.reserve_trans_descend_avg_h_m_p_s, 24.4)
    self.assertEqual(mission.reserve_trans_descend_v_m_p_s, 5.1)
    self.assertEqual(mission.reserve_trans_descend_s, 30.0)
    self.assertEqual(mission.reserve_hover_descend_avg_v_m_p_s, 2.54)
    self.assertEqual(mission.reserve_hover_descend_s, 12.0)

if __name__ == '__main__':
  unittest.main()
