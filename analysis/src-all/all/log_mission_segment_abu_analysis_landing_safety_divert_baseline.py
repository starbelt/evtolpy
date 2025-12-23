# log_mission_segment_abu_analysis_landing_safety_divert_baseline.py
#
# Usage: python3 log_mission_segment_abu_analysis_landing_safety_divert_baseline.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
#
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
#
# Output:
#  mission-segment-abu-analysis-landing-safety-divert-baseline.csv
#
# Written by 
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import csv  # csv
import sys  # argv
import os   # path

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
    'python3 log_mission_segment_abu_analysis_landing_safety_divert_baseline.py '
    '/path/to/cfg.json /path/to/log/'
  )
  exit()

# construct an aircraft object from the specified configuration
aircraft = Aircraft(cfg)

# landing safety (baseline divert) parameters
divert_distance_mi = 6.0     # horizontal distance to alternate [mi]
t_hover_s = 60.0             # required hover/loiter time before divert [s]
t_hover_descend_s = 20.0     # approximate hover descent time [s]

# MTOW iteration parameters
tol = 1e-3                   # convergence tolerance [kg]
max_iter = 100               # maximum iterations

# run baseline divert-capability evaluation (no ABU)
results = aircraft._evaluate_landing_safety_divert_baseline(
  divert_distance_mi = divert_distance_mi,
  t_hover_s          = t_hover_s,
  t_hover_descend_s  = t_hover_descend_s,
  tol                = tol,
  max_iter           = max_iter
)

if results is None:
  print("No results returned — check configuration or mission definition.")
  exit()

# define output CSV path
output_csv = os.path.join(log, 'mission-segment-abu-analysis-landing-safety-divert-baseline.csv')

# define CSV fieldnames
fieldnames = [
  "divert_distance_mi",
  "t_hover_s",
  "t_hover_descend_s",
  "tol",
  "max_iter",
  "baseline_mtow_kg",
  "mtow_converged_kg",
  "delta_battery_mass_converged_kg",
  "baseline_converged_total_mission_kwh",
  "total_required_kwh",
  "divert_required_kwh",
  "P_hover_kw",
  "P_cruise_kw",
  "t_divert_s",
  "E_hover_loiter_kwh",
  "E_divert_cruise_kwh",
  "E_hover_descend_kwh",
  "n_iterations",
  "note",
]

# write results to CSV file
with open(output_csv, mode='w', newline='') as csv_file:
  writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
  writer.writeheader()

  clean_row = {}

  # inputs
  clean_row["divert_distance_mi"] = f"{divert_distance_mi:.6f}"
  clean_row["t_hover_s"] = f"{t_hover_s:.6f}"
  clean_row["t_hover_descend_s"] = f"{t_hover_descend_s:.6f}"
  clean_row["tol"] = f"{tol:.6f}"
  clean_row["max_iter"] = int(max_iter)

  # outputs
  for key in fieldnames:
    if key in clean_row:
      continue

    if key == "n_iterations":
      hist = results.get("history", [])
      clean_row[key] = int(len(hist))
      continue

    val = results.get(key, None)
    if isinstance(val, (int, float)):
      clean_row[key] = f"{val:.6f}"
    else:
      try:
        clean_row[key] = f"{float(val):.6f}"
      except (TypeError, ValueError):
        clean_row[key] = val

  writer.writerow(clean_row)
