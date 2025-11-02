# log_mission_segment_abu_analysis_common_case_economics.py
#
# Usage: python3 log_mission_segment_abu_analysis_common_case_economics.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
#
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
#
# Output:
#  mission-segment-abu-analysis-common-case-economics.csv
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
    'python3 log_mission_segment_abu_analysis_common_case_economics.py '
    '/path/to/cfg.json /path/to/log/'
  )
  exit()

# construct an aircraft object from the specified configuration
aircraft = Aircraft(cfg)

# baseline common-case parameters
P_charger_ac_kw = 115.0       # AC charger power [kW]
eta_charger_dc  = 0.95        # Charger AC->DC efficiency
c_rate_max      = 5.0         # max charge rate [C]
v_pack_nom_v    = 800.0       # nominal pack voltage [V]
i_term_c        = 0.05        # termination current (fraction of C)
soc_target      = 1.0         # target full charge
soc_cc_end      = 0.80        # SOC at CC to CV transition
t_ground_ops_hr = 0.2833      # ground turnaround time [hr]
E_pack_kwh      = None        # use mission-based sizing if None
mission_time_s  = None        # auto-sum mission segments if None

## initial SOC from energy ratio (reserve vs total)
E_total_kwh = aircraft._calc_total_mission_energy_kw_hr()
E_reserve_kwh = aircraft._calc_total_reserve_mission_energy_kw_hr()
soc_start = E_reserve_kwh / E_total_kwh if E_total_kwh > 0 else 0.0

# ## initial SOC from energy ratio (reserve vs total)
# E_total_kwh = aircraft._calc_total_mission_energy_kw_hr()
# E_reserve_kwh = 0.0
# soc_start = E_reserve_kwh / E_total_kwh if E_total_kwh > 0 else 0.0

# run baseline evaluation (no ABU)
results = aircraft._evaluate_common_case_baseline(
  E_pack_kwh      = E_pack_kwh,
  P_charger_ac_kw = P_charger_ac_kw,
  eta_charger_dc  = eta_charger_dc,
  c_rate_max      = c_rate_max,
  v_pack_nom_v    = v_pack_nom_v,
  i_term_c        = i_term_c,
  soc_start       = soc_start,
  soc_target      = soc_target,
  soc_cc_end      = soc_cc_end,
  t_ground_ops_hr = t_ground_ops_hr,
  mission_time_s  = mission_time_s
)

if results is None:
  print("No results returned — check configuration or mission definition.")
  exit()

# define output CSV path
output_csv = os.path.join(log, 'mission-segment-abu-analysis-common-case-economics.csv')

# define CSV fieldnames
fieldnames = [
  "E_mission_kwh",
  "E_pack_kwh",
  "dod",
  "soc_start",
  "soc_target",
  "soc_cc_end",
  "t_flight_hr",
  "t_charge_hr",
  "t_cc_hr",
  "t_cv_hr",
  "t_ground_ops_hr",
  "t_cycle_hr",
  "n_feasible_flights",
  "t_flight_day_hr",
  "t_downtime_day_hr",
  "t_slack_hr",
  "charger_ac_kw",
  "eta_charger_dc",
  "c_rate_max",
  "v_pack_nom_v",
  "i_term_c",
  "P_dc_kw",
  "P_cc_cap_kw",
  "P_cc_kw",
  "I_cc_A",
  "I_term_A",
  "charger_limit_indicator_flag",
]

# write results to CSV file
with open(output_csv, mode='w', newline='') as csv_file:
  writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
  writer.writeheader()

  clean_row = {}
  for key in fieldnames:
    val = results.get(key, None)
    if isinstance(val, (int, float)):
      clean_row[key] = f"{val:.6f}"
    else:
      try:
        clean_row[key] = f"{float(val):.6f}"
      except (TypeError, ValueError):
        clean_row[key] = val
  writer.writerow(clean_row)
