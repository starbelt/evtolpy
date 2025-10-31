# mission.py
#
# A Python class containing aircraft mission characteristics
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import json # json parsing

class Mission:
  # class constructor
  def __init__(self, path_to_json: str):
    # open and load JSON specification
    ifile = open(path_to_json, 'r')
    ijson = json.load(ifile)
    # mission properties
    self._depart_taxi_avg_h_m_p_s = ijson['mission']['depart_taxi_avg_h_m_p_s']
    self._depart_taxi_s = ijson['mission']['depart_taxi_s']
    self._hover_climb_avg_v_m_p_s = ijson['mission']['hover_climb_avg_v_m_p_s']
    self._hover_climb_s = ijson['mission']['hover_climb_s']
    self._trans_climb_avg_h_m_p_s = ijson['mission']['trans_climb_avg_h_m_p_s']
    self._trans_climb_v_m_p_s= ijson['mission']['trans_climb_v_m_p_s']
    self._trans_climb_s = ijson['mission']['trans_climb_s']
    self._depart_proc_h_m_p_s = ijson['mission']['depart_proc_h_m_p_s']
    self._depart_proc_s = ijson['mission']['depart_proc_s']
    self._accel_climb_avg_h_m_p_s = ijson['mission']['accel_climb_avg_h_m_p_s']
    self._accel_climb_v_m_p_s = ijson['mission']['accel_climb_v_m_p_s']
    self._accel_climb_s = ijson['mission']['accel_climb_s']
    self._cruise_h_m_p_s = ijson['mission']['cruise_h_m_p_s']
    self._cruise_s = ijson['mission']['cruise_s']
    self._decel_descend_avg_h_m_p_s = \
     ijson['mission']['decel_descend_avg_h_m_p_s']
    self._decel_descend_v_m_p_s = ijson['mission']['decel_descend_v_m_p_s']
    self._decel_descend_s = ijson['mission']['decel_descend_s']
    self._arrive_proc_h_m_p_s = ijson['mission']['arrive_proc_h_m_p_s']
    self._arrive_proc_s = ijson['mission']['arrive_proc_s']
    self._trans_descend_avg_h_m_p_s = \
     ijson['mission']['trans_descend_avg_h_m_p_s']
    self._trans_descend_v_m_p_s = ijson['mission']['trans_descend_v_m_p_s']
    self._trans_descend_s = ijson['mission']['trans_descend_s']
    self._hover_descend_avg_v_m_p_s = \
     ijson['mission']['hover_descend_avg_v_m_p_s']
    self._hover_descend_s = ijson['mission']['hover_descend_s']
    self._arrive_taxi_avg_h_m_p_s = ijson['mission']['arrive_taxi_avg_h_m_p_s']
    self._arrive_taxi_s = ijson['mission']['arrive_taxi_s']
    self._reserve_hover_climb_avg_v_m_p_s = \
     ijson['mission']['reserve_hover_climb_avg_v_m_p_s']
    self._reserve_hover_climb_s = ijson['mission']['reserve_hover_climb_s']
    self._reserve_trans_climb_avg_h_m_p_s = \
     ijson['mission']['reserve_trans_climb_avg_h_m_p_s']
    self._reserve_trans_climb_v_m_p_s = \
     ijson['mission']['reserve_trans_climb_v_m_p_s']
    self._reserve_trans_climb_s = ijson['mission']['reserve_trans_climb_s']
    self._reserve_accel_climb_avg_h_m_p_s = \
     ijson['mission']['reserve_accel_climb_avg_h_m_p_s']
    self._reserve_accel_climb_v_m_p_s = \
     ijson['mission']['reserve_accel_climb_v_m_p_s']
    self._reserve_accel_climb_s = ijson['mission']['reserve_accel_climb_s']
    self._reserve_cruise_h_m_p_s = ijson['mission']['reserve_cruise_h_m_p_s']
    self._reserve_cruise_s = ijson['mission']['reserve_cruise_s']
    self._reserve_decel_descend_avg_h_m_p_s = \
     ijson['mission']['reserve_decel_descend_avg_h_m_p_s']
    self._reserve_decel_descend_v_m_p_s = \
     ijson['mission']['reserve_decel_descend_v_m_p_s']
    self._reserve_decel_descend_s = ijson['mission']['reserve_decel_descend_s']
    self._reserve_trans_descend_avg_h_m_p_s = \
     ijson['mission']['reserve_trans_descend_avg_h_m_p_s']
    self._reserve_trans_descend_v_m_p_s = \
     ijson['mission']['reserve_trans_descend_v_m_p_s']
    self._reserve_trans_descend_s = ijson['mission']['reserve_trans_descend_s']
    self._reserve_hover_descend_avg_v_m_p_s = \
     ijson['mission']['reserve_hover_descend_avg_v_m_p_s']
    self._reserve_hover_descend_s = ijson['mission']['reserve_hover_descend_s']
    # close JSON file
    ifile.close()

  # defines equivalence check for this class
  def __eq__(self, other):
    if isinstance(other, Mission):
      return (\
       self.depart_taxi_avg_h_m_p_s == other.depart_taxi_avg_h_m_p_s and
       self.depart_taxi_s == other.depart_taxi_s and
       self.hover_climb_avg_v_m_p_s == other.hover_climb_avg_v_m_p_s and
       self.hover_climb_s == other.hover_climb_s and
       self.trans_climb_avg_h_m_p_s == other.trans_climb_avg_h_m_p_s and
       self.trans_climb_v_m_p_s == other.trans_climb_v_m_p_s and
       self.trans_climb_s == other.trans_climb_s and
       self.depart_proc_h_m_p_s == other.depart_proc_h_m_p_s and
       self.depart_proc_s == other.depart_proc_s and
       self.accel_climb_avg_h_m_p_s == other.accel_climb_avg_h_m_p_s and
       self.accel_climb_v_m_p_s == other.accel_climb_v_m_p_s and
       self.accel_climb_s == other.accel_climb_s and
       self.cruise_h_m_p_s == other.cruise_h_m_p_s and
       self.cruise_s == other.cruise_s and
       self.decel_descend_avg_h_m_p_s == other.decel_descend_avg_h_m_p_s and
       self.decel_descend_v_m_p_s == other.decel_descend_v_m_p_s and
       self.decel_descend_s == other.decel_descend_s and
       self.arrive_proc_h_m_p_s == other.arrive_proc_h_m_p_s and
       self.arrive_proc_s == other.arrive_proc_s and
       self.trans_descend_avg_h_m_p_s == other.trans_descend_avg_h_m_p_s and
       self.trans_descend_v_m_p_s == other.trans_descend_v_m_p_s and
       self.trans_descend_s == other.trans_descend_s and
       self.hover_descend_avg_v_m_p_s == other.hover_descend_avg_v_m_p_s and
       self.hover_descend_s == other.hover_descend_s and
       self.arrive_taxi_avg_h_m_p_s == other.arrive_taxi_avg_h_m_p_s and
       self.arrive_taxi_s == other.arrive_taxi_s and
       self.reserve_hover_climb_avg_v_m_p_s == \
        other.reserve_hover_climb_avg_v_m_p_s and
       self.reserve_hover_climb_s == other.reserve_hover_climb_s and
       self.reserve_trans_climb_avg_h_m_p_s == \
        other.reserve_trans_climb_avg_h_m_p_s and
       self.reserve_trans_climb_v_m_p_s == other.reserve_trans_climb_v_m_p_s and
       self.reserve_trans_climb_s == other.reserve_trans_climb_s and
       self.reserve_accel_climb_avg_h_m_p_s == \
        other.reserve_accel_climb_avg_h_m_p_s and
       self.reserve_accel_climb_v_m_p_s == other.reserve_accel_climb_v_m_p_s and
       self.reserve_accel_climb_s == other.reserve_accel_climb_s and
       self.reserve_cruise_h_m_p_s == other.reserve_cruise_h_m_p_s and
       self.reserve_cruise_s == other.reserve_cruise_s and
       self.reserve_decel_descend_avg_h_m_p_s == \
        other.reserve_decel_descend_avg_h_m_p_s and
       self.reserve_decel_descend_v_m_p_s == \
        other.reserve_decel_descend_v_m_p_s and
       self.reserve_decel_descend_s == other.reserve_decel_descend_s and
       self.reserve_trans_descend_avg_h_m_p_s == \
        other.reserve_trans_descend_avg_h_m_p_s and
       self.reserve_trans_descend_v_m_p_s == \
        other.reserve_trans_descend_v_m_p_s and
       self.reserve_trans_descend_s == other.reserve_trans_descend_s and
       self.reserve_hover_descend_avg_v_m_p_s == \
        other.reserve_hover_descend_avg_v_m_p_s and
       self.reserve_hover_descend_s == other.reserve_hover_descend_s
       )
    else:
      return NotImplemented

  @property
  def depart_taxi_avg_h_m_p_s(self):
    return self._depart_taxi_avg_h_m_p_s

  @property
  def depart_taxi_s(self):
    return self._depart_taxi_s

  @property
  def hover_climb_avg_v_m_p_s(self):
    return self._hover_climb_avg_v_m_p_s

  @property
  def hover_climb_s(self):
    return self._hover_climb_s

  @property
  def trans_climb_avg_h_m_p_s(self):
    return self._trans_climb_avg_h_m_p_s

  @property
  def trans_climb_v_m_p_s(self):
    return self._trans_climb_v_m_p_s

  @property
  def trans_climb_s(self):
    return self._trans_climb_s

  @property
  def depart_proc_h_m_p_s(self):
    return self._depart_proc_h_m_p_s

  @property
  def depart_proc_s(self):
    return self._depart_proc_s

  @property
  def accel_climb_avg_h_m_p_s(self):
    return self._accel_climb_avg_h_m_p_s

  @property
  def accel_climb_v_m_p_s(self):
    return self._accel_climb_v_m_p_s

  @property
  def accel_climb_s(self):
    return self._accel_climb_s

  @property
  def cruise_h_m_p_s(self):
    return self._cruise_h_m_p_s

  @property
  def cruise_s(self):
    return self._cruise_s

  @property
  def decel_descend_avg_h_m_p_s(self):
    return self._decel_descend_avg_h_m_p_s

  @property
  def decel_descend_v_m_p_s(self):
    return self._decel_descend_v_m_p_s

  @property
  def decel_descend_s(self):
    return self._decel_descend_s

  @property
  def arrive_proc_h_m_p_s(self):
    return self._arrive_proc_h_m_p_s

  @property
  def arrive_proc_s(self):
    return self._arrive_proc_s

  @property
  def trans_descend_avg_h_m_p_s(self):
    return self._trans_descend_avg_h_m_p_s

  @property
  def trans_descend_v_m_p_s(self):
    return self._trans_descend_v_m_p_s

  @property
  def trans_descend_s(self):
    return self._trans_descend_s

  @property
  def hover_descend_avg_v_m_p_s(self):
    return self._hover_descend_avg_v_m_p_s

  @property
  def hover_descend_s(self):
    return self._hover_descend_s

  @property
  def arrive_taxi_avg_h_m_p_s(self):
    return self._arrive_taxi_avg_h_m_p_s

  @property
  def arrive_taxi_s(self):
    return self._arrive_taxi_s

  @property
  def reserve_hover_climb_avg_v_m_p_s(self):
    return self._reserve_hover_climb_avg_v_m_p_s

  @property
  def reserve_hover_climb_s(self):
    return self._reserve_hover_climb_s

  @property
  def reserve_trans_climb_avg_h_m_p_s(self):
    return self._reserve_trans_climb_avg_h_m_p_s

  @property
  def reserve_trans_climb_v_m_p_s(self):
    return self._reserve_trans_climb_v_m_p_s

  @property
  def reserve_trans_climb_s(self):
    return self._reserve_trans_climb_s

  @property
  def reserve_accel_climb_avg_h_m_p_s(self):
    return self._reserve_accel_climb_avg_h_m_p_s

  @property
  def reserve_accel_climb_v_m_p_s(self):
    return self._reserve_accel_climb_v_m_p_s

  @property
  def reserve_accel_climb_s(self):
    return self._reserve_accel_climb_s

  @property
  def reserve_cruise_h_m_p_s(self):
    return self._reserve_cruise_h_m_p_s

  @property
  def reserve_cruise_s(self):
    return self._reserve_cruise_s

  @property
  def reserve_decel_descend_avg_h_m_p_s(self):
    return self._reserve_decel_descend_avg_h_m_p_s

  @property
  def reserve_decel_descend_v_m_p_s(self):
    return self._reserve_decel_descend_v_m_p_s

  @property
  def reserve_decel_descend_s(self):
    return self._reserve_decel_descend_s

  @property
  def reserve_trans_descend_avg_h_m_p_s(self):
    return self._reserve_trans_descend_avg_h_m_p_s

  @property
  def reserve_trans_descend_v_m_p_s(self):
    return self._reserve_trans_descend_v_m_p_s

  @property
  def reserve_trans_descend_s(self):
    return self._reserve_trans_descend_s

  @property
  def reserve_hover_descend_avg_v_m_p_s(self):
    return self._reserve_hover_descend_avg_v_m_p_s

  @property
  def reserve_hover_descend_s(self):
    return self._reserve_hover_descend_s
