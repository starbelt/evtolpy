# power.py
#
# A Python class containing aircraft power characteristics
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris
#
# See the LICENSE file for the license

# import Python modules
import json # json parsing

class Power:
  # class constructor
  def __init__(self, path_to_json: str):
    # open and load JSON specification
    ifile = open(path_to_json, 'r')
    ijson = json.load(ifile)
    # power properties
    self._batt_spec_energy_w_h_p_kg = \
     ijson['power']['batt_spec_energy_w_h_p_kg']
    self._batt_inaccessible_energy_frac = \
     ijson['power']['batt_inaccessible_energy_frac']
    self._batt_eol_capacity = ijson['power']['batt_eol_capacity']
    self._batt_int_factor = ijson['power']['batt_int_factor']
    self._epu_effic = ijson['power']['epu_effic']
    self._hover_power_effic = ijson['power']['hover_power_effic']
    # calculate initial values of derived fields
    self._batt_bol_usable_spec_energy_w_h_p_kg = \
     self._calc_batt_bol_usable_spec_energy_w_h_p_kg()
    self._batt_eol_usable_spec_energy_w_h_p_kg = \
     self._calc_batt_eol_usable_spec_energy_w_h_p_kg()
    # close JSON file
    ifile.close()

  # scale the battery specific energy to the accessible energy fraction and
  # account for the integration factor; BOL = beginning of life
  def _calc_batt_bol_usable_spec_energy_w_h_p_kg(self):
    return \
     self.batt_int_factor*(1.0-self.batt_inaccessible_energy_frac)*\
     self.batt_spec_energy_w_h_p_kg

  # same as BOL with an additional factor accounting for end-of-life capacity
  def _calc_batt_eol_usable_spec_energy_w_h_p_kg(self):
    return \
     self.batt_eol_capacity*self._calc_batt_bol_usable_spec_energy_w_h_p_kg()

  # defines equivalence check for this class
  def __eq__(self, other):
    if isinstance(other, Power):
      return (\
       self.batt_spec_energy_w_h_p_kg == other.batt_spec_energy_w_h_p_kg and
       self.batt_inaccessible_energy_frac == \
        other.batt_inaccessible_energy_frac and
       self.batt_eol_capacity == other.batt_eol_capacity and
       self.batt_int_factor == other.batt_int_factor and
       self.epu_effic == other.epu_effic and
       self.hover_power_effic == other.hover_power_effic
       )
    else:
      return NotImplemented

  @property
  def batt_spec_energy_w_h_p_kg(self):
    return self._batt_spec_energy_w_h_p_kg

  @property
  def batt_inaccessible_energy_frac(self):
    return self._batt_inaccessible_energy_frac

  @property
  def batt_eol_capacity(self):
    return self._batt_eol_capacity

  @property
  def batt_int_factor(self):
    return self._batt_int_factor

  @property
  def epu_effic(self):
    return self._epu_effic

  @property
  def hover_power_effic(self):
    return self._hover_power_effic
