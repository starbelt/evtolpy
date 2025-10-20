# log_mission_segment_abu_analysis_landing_safety_loiter.py
#
# Usage: python3 log_mission_segment_abu_analysis_landing_safety_loiter.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
#
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
#
# Output:
#  mission-segment-abu-analysis-landing-safety-loiter.csv
#
# Written by 
# Other contributors:
#
# See the LICENSE file for the license

# import Python modules
import csv  # csv
import sys  # argv

# path to directory containing evtolpy package; use before deploying as package
sys.path.append('../../../evtol')
from aircraft import Aircraft

# initialize script arguments
cfg = ''  # path to configuration JSON file
log = ''  # destination directory for log files

# parse script arguments
if len(sys.argv) == 3:
  cfg = sys.argv[1]
  log = sys.argv[2]
  if log[-1] != '/':
    log += '/'
else:
  print(
    'Usage: '
    'python3 log_mission_segment_abu_analysis_landing_safety_loiter.py '
    '/path/to/cfg.json /path/to/log/'
  )
  exit()

# construct an aircraft object from the specified configuration
aircraft = Aircraft(cfg)

# sweep ABU mission energies (kWh per ABU)
start = 5
stop  = 50
step  = 5
E_mission_kwh_per_abu_list = list(range(start, stop + 1, step))

# example ABU spec (user-defined)
abu_spec = {
  "n_abus": 1,                     # number of ABUs attached (default 1)
  "E_ops_kwh_per_abu": 1.0,        # energy reserved for ABU's own safe ops [kWh]
  "struct_frac": 0.20,             # structural fraction of battery mass
  "integration_frac": 0.05,        # integration hardware fraction of battery mass
}

# alternate divert scenario (user-defined)
divert_distance_mi = 6.0           # example alternate site distance [mi]
t_hover_s = 60.0                   # required hover time [s]
t_hover_descend_s = 40.0           # approximate hover descent time [s]

# evaluate ABU-assisted landing safety loiter
results = aircraft._evaluate_landing_safety_loiter(
  E_mission_kwh_per_abu_list = E_mission_kwh_per_abu_list,
  divert_distance_mi         = divert_distance_mi,
  t_hover_s                  = t_hover_s,
  t_hover_descend_s          = t_hover_descend_s,
  abu_spec                   = abu_spec
)

# define output CSV path
output_csv = log + 'mission-segment-abu-analysis-landing-safety-loiter.csv'

# define CSV fieldnames
fieldnames = [
  "n_abus",
  "E_abu_mission_kwh",
  "E_abu_total_kwh",
  "m_abu_batt_kg",
  "m_abu_struct_kg",
  "m_abu_integ_kg",
  "m_rot_hub_kg",
  "m_abu_total_all_kg",
  "P_hover_attach_kw",
  "P_cruise_attach_kw",
  "t_divert_s",
  "divert_distance_mi",
  "E_divert_kwh",
  "t_hover_s",
  "E_hover_kwh",
  "t_hover_descend_s",
  "E_hover_descend_kwh",
  "E_ops_kwh_total",
  "t_loiter_hover_max_s",
  "feasible",
  "margin_kwh",
  "note"
]

# write results to CSV file
with open(output_csv, mode='w', newline='') as csv_file:
  writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
  writer.writeheader()

  for row in results:
    clean_row = {}
    for key in fieldnames:
      val = row.get(key, None)
      if isinstance(val, (int, float)):
        clean_row[key] = f"{val:.6f}"
      else:
        try:
          clean_row[key] = f"{float(val):.6f}"
        except (TypeError, ValueError):
          clean_row[key] = val
    writer.writerow(clean_row)
