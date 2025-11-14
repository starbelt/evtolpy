# log_mission_segment_abu_analysis_common_case_economics_extended_flight_overlap_charging_queuing.py
#
# Usage: python3 log_mission_segment_abu_analysis_common_case_economics_extended_flight_overlap_charging_queuing.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
#
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
#
# Output:
#  mission-segment-abu-analysis-common-case-economics-extended-flight-overlap-charging-queuing.csv
#  mission-segment-abu-analysis-common-case-economics-extended-flight-overlap-charging-queuing-timeline.csv
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
    'python3 log_mission_segment_abu_analysis_common_case_economics_extended_flight_overlap_charging_queuing.py '
    '/path/to/cfg.json /path/to/log/'
  )
  exit()

# construct an aircraft object from the specified configuration
aircraft = Aircraft(cfg)

# ABU mission energy sweep (kWh per ABU)
start = 5
stop  = 50
step  = 5
E_mission_kwh_per_abu_list = list(range(start, stop + 1, step))

# ABU pool sizes to sweep for queuing bottleneck
n_abu_pool_list = [1, 2]

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

# ABU flight return parameters
V_abu_horizontal_m_p_s = 30.0   # ABU horizontal return speed [m/s]
V_abu_vertical_m_p_s   = 5.1    # ABU vertical descent speed [m/s]
h_detach_ft            = 1500.0 # detach altitude [m]

# ABU specifications
abu_spec = {
  "n_abus": 1,
  "E_ops_kwh_per_abu": 12.0,   # energy reserved for ABU safe ops [kWh]
  "struct_frac": 0.20,         # structural fraction of battery mass
  "integration_frac": 0.05,    # integration hardware fraction
}

# prepare output storage
all_results = []
timeline_rows = []  

# run evaluator for each ABU pool size
for n_abu_pool in n_abu_pool_list:

  results = aircraft._evaluate_common_case_abu_extended_flight_overlap_charging_queuing(
    E_mission_kwh_per_abu_list = E_mission_kwh_per_abu_list,
    abu_spec                   = abu_spec,
    n_abu_pool                 = n_abu_pool,
    P_charger_ac_kw            = P_charger_ac_kw,
    eta_charger_dc             = eta_charger_dc,
    c_rate_max                 = c_rate_max,
    v_pack_nom_v_main          = v_pack_nom_v_main,
    v_pack_nom_v_abu           = v_pack_nom_v_abu,
    i_term_c                   = i_term_c,
    soc_target                 = soc_target,
    soc_cc_end                 = soc_cc_end,
    t_ground_ops_hr            = t_ground_ops_hr,
    V_abu_horizontal_m_p_s     = V_abu_horizontal_m_p_s,
    V_abu_vertical_m_p_s       = V_abu_vertical_m_p_s,
    h_detach_ft                = h_detach_ft,
    mission_time_s             = mission_time_s
  )

  if results is None or len(results) == 0:
    print(f"No results returned for n_abu_pool = {n_abu_pool}")
    continue

  # tag each row with the ABU pool size
  for row in results:
    row["n_abu_pool"] = n_abu_pool
    all_results.append(row)

    # timeline extraction 
    aircraft_tl = row.get("aircraft_timeline", [])
    abu_tls     = row.get("abu_timelines", {})

    # aircraft timeline events
    for entry in aircraft_tl:
      timeline_rows.append({
      "n_abu_pool": n_abu_pool,
      "E_abu_mission_kwh_per_abu": row.get("E_abu_mission_kwh_per_abu"),
      "timeline_type": "aircraft",
      "abu_index": "",
      "flight_index": (entry.get("flight_index") + 1) if entry.get("flight_index") is not None else "",
      "t_hr": entry.get("t_hr"),
      "event": entry.get("event"),
    })

    # ABU timelines
    for abu_idx, event_list in abu_tls.items():
      for entry in event_list:
        timeline_rows.append({
          "n_abu_pool": n_abu_pool,
          "E_abu_mission_kwh_per_abu": row.get("E_abu_mission_kwh_per_abu"),
          "timeline_type": "abu",
          "abu_index": (abu_idx + 1),
          "flight_index": (entry.get("flight_index") + 1) if entry.get("flight_index") is not None else "",
          "t_hr": entry.get("t_hr"),
          "event": entry.get("event"),
        })

if len(all_results) == 0:
  print("No results produced — check configuration or mission definition.")
  exit()

# define output CSV path (main results)
output_csv = os.path.join(
  log,
  'mission-segment-abu-analysis-common-case-economics-extended-flight-overlap-charging-queuing.csv'
)

# define CSV fieldnames
fieldnames = [
  "n_abu_pool",
  "E_abu_mission_kwh_per_abu",
  "E_abu_total_kwh_per_abu",
  "E_abu_used_kwh_total",
  "E_saved_kwh",
  "E_mission_kwh_main",
  "E_pack_kwh_main",
  "E_pack_kwh_abu",
  "dod_main",
  "dod_abu",
  "soc_start_main",
  "soc_start_abu",
  "soc_target",
  "t_flight_hr",
  "t_attached_hr",
  "t_return_cruise_abu_hr",
  "t_charge_hr_main",
  "t_charge_hr_abu",
  "t_cycle_nominal_hr",
  "n_flights_nominal_no_abu_limit",
  "n_flights_completed",
  "t_flight_day_hr",
  "t_slack_hr",
  "t_wait_abu_day_hr",
  "abu_utilization_avg",
  "abu_bottleneck_flag",
  "P_cc_kw_main",
  "P_cc_kw_abu",
  "charger_limit_indicator_flag_main",
  "charger_limit_indicator_flag_abu",
]

# write results to main CSV file
with open(output_csv, mode='w', newline='') as csv_file:
  writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
  writer.writeheader()

  for row in all_results:
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

# write timeline CSV
timeline_csv = os.path.join(
  log,
  'mission-segment-abu-analysis-common-case-economics-extended-flight-overlap-charging-queuing-timeline.csv'
)

timeline_fieldnames = [
  "n_abu_pool",
  "E_abu_mission_kwh_per_abu",
  "timeline_type",
  "abu_index",
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
