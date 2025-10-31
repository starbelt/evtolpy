# environ.py
#
# A Python class containing aircraft flight environment characteristics
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import json # json parsing

class Environ:
  # class constructor
  def __init__(self, path_to_json: str):
    # open and load JSON specification
    ifile = open(path_to_json, 'r')
    ijson = json.load(ifile)
    # environ properties
    self._g_m_p_s2 = ijson['environ']['g_m_p_s2']
    self._sound_speed_m_p_s = ijson['environ']['sound_speed_m_p_s']
    self._air_density_sea_lvl_kg_p_m3 = \
     ijson['environ']['air_density_sea_lvl_kg_p_m3']
    self._air_density_max_alt_kg_p_m3 = \
     ijson['environ']['air_density_max_alt_kg_p_m3']
    self._kinematic_viscosity_sea_lvl_m2_p_s = \
     ijson['environ']['kinematic_viscosity_sea_lvl_m2_p_s']
    self._kinematic_viscosity_max_alt_m2_p_s = \
     ijson['environ']['kinematic_viscosity_max_alt_m2_p_s']
    # close JSON file
    ifile.close()

  # defines equivalence check for this class
  def __eq__(self, other):
    if isinstance(other, Environ):
      return (\
       self.g_m_p_s2 == other.g_m_p_s2 and
       self.sound_speed_m_p_s == other.sound_speed_m_p_s and
       self.air_density_sea_lvl_kg_p_m3 == other.air_density_sea_lvl_kg_p_m3 and
       self.air_density_max_alt_kg_p_m3 == other.air_density_max_alt_kg_p_m3 and
       self.kinematic_viscosity_sea_lvl_m2_p_s == \
        other.kinematic_viscosity_sea_lvl_m2_p_s
       )
    else:
      return NotImplemented

  @property
  def g_m_p_s2(self):
    return self._g_m_p_s2

  @property
  def sound_speed_m_p_s(self):
    return self._sound_speed_m_p_s

  @property
  def air_density_sea_lvl_kg_p_m3(self):
    return self._air_density_sea_lvl_kg_p_m3

  @property
  def air_density_max_alt_kg_p_m3(self):
    return self._air_density_max_alt_kg_p_m3

  @property
  def kinematic_viscosity_sea_lvl_m2_p_s(self):
    return self._kinematic_viscosity_sea_lvl_m2_p_s

  @property
  def kinematic_viscosity_max_alt_m2_p_s(self):
    return self._kinematic_viscosity_max_alt_m2_p_s
