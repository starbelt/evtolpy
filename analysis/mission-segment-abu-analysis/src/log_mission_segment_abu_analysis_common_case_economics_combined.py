# log_mission_segment_abu_analysis_common_case_economics_combined.py
#
# Usage: python3 log_mission_segment_abu_analysis_common_case_economics_combined.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
#
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
#
# Output:
#  mission-segment-abu-analysis-common-case-economics-combined.csv
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
    'python3 log_mission_segment_abu_analysis_common_case_economics_combined.py '
    '/path/to/cfg.json /path/to/log/'
  )
  exit()

# construct an aircraft object from the specified configuration
aircraft = Aircraft(cfg)

# ABU assisted-takeoff candidates
candidates = [
  {
    "name": "after_accel_climb",
    "segments": ["depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb"]
  }
]

# ABU mission energy sweep (for extended flight) [kWh per ABU]
start = 5
stop  = 50
step  = 5
E_mission_kwh_per_abu_list = list(range(start, stop + 1, step))

# common-case parameters
P_charger_ac_kw   = 115.0      # AC charger power [kW]
eta_charger_dc    = 0.95       # Charger AC->DC efficiency
c_rate_max        = 20.0       # max charge rate [C]
v_pack_nom_v_main = 800.0      # nominal voltage of main eVTOL battery [V]
v_pack_nom_v_abu  = 400.0      # nominal voltage of ABU battery [V]
i_term_c          = 0.05       # termination current (fraction of C)
soc_target        = 1.0        # target full charge
soc_cc_end        = 0.80       # SOC at CC to CV transition
t_ground_ops_hr   = 0.2833     # ground turnaround time [hr]
mission_time_s    = None       # auto-sum mission segments if None

# ABU specs
abu_spec_takeoff = {
  "n_abus": 1,
  "E_mission_kwh_per_abu": 15.0,
  "E_ops_kwh_per_abu": 6.0,
  "m_struct_kg_per_abu": 50.0,
  "m_integration_kg_per_abu": 10.0,
}

abu_spec_cruise = {
  "n_abus": 1,
  "E_ops_kwh_per_abu": 12.0,
  "struct_frac": 0.20,
  "integration_frac": 0.05,
}

# run combined ABU common-case economics evaluation
results = aircraft._evaluate_common_case_abu_combined(
  candidates          = candidates,
  E_mission_kwh_per_abu_list = E_mission_kwh_per_abu_list,
  abu_spec_takeoff    = abu_spec_takeoff,
  abu_spec_cruise     = abu_spec_cruise,
  P_charger_ac_kw     = P_charger_ac_kw,
  eta_charger_dc      = eta_charger_dc,
  c_rate_max          = c_rate_max,
  v_pack_nom_v_main   = v_pack_nom_v_main,
  v_pack_nom_v_abu    = v_pack_nom_v_abu,
  i_term_c            = i_term_c,
  soc_target          = soc_target,
  soc_cc_end          = soc_cc_end,
  t_ground_ops_hr     = t_ground_ops_hr,
  mission_time_s      = mission_time_s
)

if results is None or len(results) == 0:
  print("No results returned — check configuration or mission definition.")
  exit()

# define output CSV path
output_csv = os.path.join(log, 'mission-segment-abu-analysis-common-case-economics-combined.csv')

# define CSV fieldnames
fieldnames = [
  "candidate_name",
  "E_abu_mission_cruise_per_abu_kwh",
  "E_pack_kwh_main",
  "E_mission_kwh_main",
  "dod_main",
  "soc_start_main",
  "soc_target",
  "soc_cc_end",
  "n_abus_takeoff",
  "E_abu_used_takeoff_total_kwh",
  "E_ops_takeoff_per_abu_kwh",
  "E_pack_takeoff_abu_per_abu_kwh",
  "soc_start_abu_takeoff",
  "dod_abu_takeoff",
  "n_abus_cruise",
  "E_abu_used_cruise_total_kwh",
  "E_saved_kwh_cruise",
  "E_ops_cruise_per_abu_kwh",
  "E_pack_cruise_abu_per_abu_kwh",
  "soc_start_abu_cruise",
  "dod_abu_cruise",
  "t_charge_hr_main",
  "t_charge_hr_takeoff_abu_per_pack",
  "t_charge_hr_cruise_abu_per_pack",
  "t_charge_hr_total",
  "t_ground_ops_hr",
  "t_flight_hr",
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
  "i_term_c",
  "P_cc_kw_main",
  "P_cc_kw_takeoff_abu",
  "P_cc_kw_cruise_abu",
  "charger_limit_indicator_flag_main",
  "charger_limit_indicator_flag_takeoff_abu",
  "charger_limit_indicator_flag_cruise_abu",
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
