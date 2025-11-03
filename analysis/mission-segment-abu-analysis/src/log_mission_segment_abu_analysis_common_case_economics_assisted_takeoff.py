# log_mission_segment_abu_analysis_common_case_economics_assisted_takeoff.py
#
# Usage: python3 log_mission_segment_abu_analysis_common_case_economics_assisted_takeoff.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
#
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
#
# Output:
#  mission-segment-abu-analysis-common-case-economics-assisted-takeoff.csv
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
    'python3 log_mission_segment_abu_analysis_common_case_economics_assisted_takeoff.py '
    '/path/to/cfg.json /path/to/log/'
  )
  exit()

# construct an aircraft object from the specified configuration
aircraft = Aircraft(cfg)

# assisted-takeoff ABU and charger parameters
P_charger_ac_kw   = 115.0       # AC charger power [kW]
eta_charger_dc    = 0.95        # Charger AC->DC efficiency
c_rate_max        = 15.0        # max charge rate [C]
v_pack_nom_v_main = 800.0       # main eVTOL pack nominal voltage [V]
v_pack_nom_v_abu  = 400.0       # ABU pack nominal voltage [V]
i_term_c          = 0.05        # CV termination current (fraction of C)
soc_target        = 1.0         # target SOC after charge
soc_cc_end        = 0.80        # SOC where CC->CV transition occurs
t_ground_ops_hr   = 0.2833      # ground turnaround time [hr]
mission_time_s    = None        # auto-sum post-detach mission segments if None
 
# ABU specification (example)
abu_spec = {
  "n_abus": 1,                    # number of ABUs per aircraft
  "E_mission_kwh_per_abu": 10.0,  # mission (assist) energy per ABU [kWh]
  "E_ops_kwh_per_abu": 0.5,       # ops/safety reserve per ABU [kWh]
  "m_struct_kg_per_abu": 20.0,    # structure [kg]
  "m_integration_kg_per_abu": 2.0 # integration hardware [kg]
}

# ABU detach candidates (example structure)
candidates = [
  {
    "name": "after_accel_climb",
    "segments": ["depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb"]
  }
]

# run evaluation
results = aircraft._evaluate_common_case_abu_assisted_takeoff(
  candidates           = candidates,
  abu_spec             = abu_spec,
  P_charger_ac_kw      = P_charger_ac_kw,
  eta_charger_dc       = eta_charger_dc,
  c_rate_max           = c_rate_max,
  v_pack_nom_v_main    = v_pack_nom_v_main,
  v_pack_nom_v_abu     = v_pack_nom_v_abu,
  i_term_c             = i_term_c,
  soc_target           = soc_target,
  soc_cc_end           = soc_cc_end,
  t_ground_ops_hr      = t_ground_ops_hr,
  mission_time_s       = mission_time_s
)

if results is None or len(results) == 0:
  print("No results returned — check configuration, ABU spec, or detach candidates.")
  exit()

# define output CSV path
output_csv = os.path.join(log, 'mission-segment-abu-analysis-common-case-economics-assisted-takeoff.csv')

# define CSV fieldnames
fieldnames = [
  "candidate_name",
  "E_pack_kwh_main",
  "E_pack_kwh_abu",
  "n_abus",
  "dod_main",
  "dod_abu",
  "soc_start_main",
  "soc_start_abu",
  "soc_target",
  "t_flight_hr",
  "t_charge_hr_main",
  "t_charge_hr_abu",
  "t_charge_hr_total",
  "t_ground_ops_hr",
  "t_cycle_hr",
  "n_feasible_flights",
  "t_flight_day_hr",
  "t_downtime_day_hr",
  "t_slack_hr",
  "charger_ac_kw",
  "eta_charger_dc",
  "c_rate_max",
  "v_pack_nom_v_main",
  "v_pack_nom_v_abu",
  "P_cc_kw_main",
  "P_cc_kw_abu",
  "charger_limit_indicator_flag_main",
  "charger_limit_indicator_flag_abu",
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
