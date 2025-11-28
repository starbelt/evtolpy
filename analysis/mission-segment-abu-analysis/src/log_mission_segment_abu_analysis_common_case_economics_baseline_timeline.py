# log_mission_segment_abu_analysis_common_case_economics_baseline_timeline.py
#
# Usage: python3 log_mission_segment_abu_analysis_common_case_economics_baseline_timeline.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the timeline results to the log directory
#
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
#
# Output:
#  mission-segment-baseline-common-case-economics-timeline.csv
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
    'python3 log_mission_segment_abu_analysis_common_case_economics_baseline_timeline.py '
    '/path/to/cfg.json /path/to/log/'
  )
  exit()

# construct an aircraft object from the specified configuration
aircraft = Aircraft(cfg)

# baseline common-case parameters
P_charger_ac_kw     = 115.0
eta_charger_dc      = 0.95
c_rate_max          = 5.0
v_pack_nom_v_main   = 800.0
i_term_c            = 0.05
soc_target          = 1.0
soc_cc_end          = 0.80
t_ground_ops_hr     = 0.2833
daily_operation_hr  = 8.0
mission_time_s      = None

# prepare output storage
timeline_rows = []

# run baseline evaluation with timeline
result = aircraft._evaluate_common_case_baseline_timeline(
  E_pack_kwh          = None,
  P_charger_ac_kw     = P_charger_ac_kw,
  eta_charger_dc      = eta_charger_dc,
  c_rate_max          = c_rate_max,
  v_pack_nom_v        = v_pack_nom_v_main,
  i_term_c            = i_term_c,
  soc_start           = None,
  soc_target          = soc_target,
  soc_cc_end          = soc_cc_end,
  t_ground_ops_hr     = t_ground_ops_hr,
  daily_operation_hr  = daily_operation_hr,
  mission_time_s      = mission_time_s
)

if result is None:
  print("No results returned for baseline evaluation.")
  exit()

# extract aircraft timeline
aircraft_tl = result.get("aircraft_timeline", [])

for entry in aircraft_tl:
  timeline_rows.append({
    "timeline_type": "aircraft",
    "flight_index": (entry.get("flight_index") + 1) if entry.get("flight_index") is not None else "",
    "t_hr": entry.get("t_hr"),
    "event": entry.get("event"),
  })

# write timeline CSV
timeline_csv = os.path.join(
  log,
  'mission-segment-baseline-common-case-economics-timeline.csv'
)

timeline_fieldnames = [
  "timeline_type",   # "aircraft"
  "flight_index",
  "t_hr",
  "event",
]

with open(timeline_csv, mode='w', newline='') as csv_file:
  writer = csv.DictWriter(csv_file, fieldnames=timeline_fieldnames)
  writer.writeheader()

  for entry in timeline_rows:
    clean_row = {}
    for key in timeline_fieldnames:
      val = entry.get(key, None)
      if isinstance(val, (int, float)):
        clean_row[key] = f"{val:.6f}"
      else:
        try:
          clean_row[key] = f"{float(val):.6f}"
        except (TypeError, ValueError):
          clean_row[key] = val
    writer.writerow(clean_row)
