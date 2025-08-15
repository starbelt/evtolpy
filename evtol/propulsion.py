# propulsion.py
#
# A Python class containing aircraft propulsion characteristics
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris
#
# See the LICENSE file for the license

# import Python modules
import json # json parsing
import math # pi

class Propulsion:
  # class constructor
  def __init__(self, path_to_json: str):
    # open and load JSON specification
    ifile = open(path_to_json, 'r')
    ijson = json.load(ifile)
    # propulsion properties
    self._rotor_effic = ijson['propulsion']['rotor_effic']
    self._rotor_count = ijson['propulsion']['rotor_count']
    self._rotor_diameter_m = ijson['propulsion']['rotor_diameter_m']
    self._tip_mach = ijson['propulsion']['tip_mach']
    self._rotor_avg_cl = ijson['propulsion']['rotor_avg_cl']
    # calculate initial values of derived fields
    self._disk_area_m2 = self._calc_disk_area_m2()
    # close JSON file
    ifile.close()

  # area of circle swept by rotor times rotor count
  def _calc_disk_area_m2(self):
    return self.rotor_count*math.pi*(self.rotor_diameter_m/2.0)**2.0

  # defines equivalence check for this class
  def __eq__(self, other):
    if isinstance(other, Propulsion):
      return (\
       self.rotor_effic == other.rotor_effic and
       self.rotor_count == other.rotor_count and
       self.rotor_diameter_m == other.rotor_diameter_m and
       self.tip_mach == other.tip_mach and
       self.rotor_avg_cl == other.rotor_avg_cl
       )
    else:
      return NotImplemented

  @property
  def rotor_effic(self):
    return self._rotor_effic

  @property
  def rotor_count(self):
    return self._rotor_count

  # the setter is called automatically with the code p.rotor_count = 4
  @rotor_count.setter
  def rotor_count(self, new_count):
    # TODO: ensure cascading update calculations if rotor count changes
    self._rotor_count = new_count
    self._disk_area_m2 = self._calc_disk_area_m2()

  @property
  def rotor_diameter_m(self):
    return self._rotor_diameter_m

  @property
  def tip_mach(self):
    return self._tip_mach

  @property
  def rotor_avg_cl(self):
    return self._rotor_avg_cl

  @property
  def disk_area_m2(self):
    return self._disk_area_m2
