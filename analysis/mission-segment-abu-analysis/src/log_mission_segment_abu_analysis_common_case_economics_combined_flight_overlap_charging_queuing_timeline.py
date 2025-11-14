# log_mission_segment_abu_analysis_common_case_economics_combined_flight_overlap_charging_queuing_timeline.py
#
# Usage: python3 log_mission_segment_abu_analysis_common_case_economics_combined_flight_overlap_charging_queuing_timeline.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
#
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
#
# Output:
#  mission-segment-abu-analysis-common-case-economics-combined-flight-overlap-charging-queuing.csv
#  mission-segment-abu-analysis-common-case-economics-combined-flight-overlap-charging-queuing-timeline.csv
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
    'python3 log_mission_segment_abu_analysis_common_case_economics_combined_flight_overlap_charging_queuing_timeline.py '
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

# ABU mission energy sweep for cruise-ABUs (kWh per ABU)
start = 5
stop  = 50
step  = 5
E_mission_kwh_per_abu_list = list(range(start, stop + 1, step))

# ABU pool sizes to sweep for queuing bottleneck
n_takeoff_abu_pool_list = [1, 2]   # pool at takeoff LZ (takeoff-ABUs)
n_cruise_abu_pool_list  = [1, 2]   # pool at landing LZ (cruise-ABUs)

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

# ABU flight return parameters (takeoff ABUs)
V_takeoff_abu_horizontal_m_p_s = 30.0   # takeoff-ABU horizontal return speed [m/s]
V_takeoff_abu_vertical_m_p_s   = 5.1    # takeoff-ABU vertical descent speed [m/s]
h_takeoff_detach_ft            = 1500.0 # takeoff-ABU detach altitude [ft]

# ABU flight return parameters (cruise ABUs)
V_cruise_abu_horizontal_m_p_s = 30.0    # cruise-ABU horizontal return speed [m/s]
V_cruise_abu_vertical_m_p_s   = 5.1     # cruise-ABU vertical descent speed [m/s]
h_cruise_detach_ft            = 1500.0  # cruise-ABU detach altitude [ft]

# ABU specifications (takeoff ABUs)
abu_spec_takeoff = {
  "n_abus": 1,
  "E_mission_kwh_per_abu": 15.0,
  "E_ops_kwh_per_abu": 6.0,
  "m_struct_kg_per_abu": 50.0,
  "m_integration_kg_per_abu": 10.0,
}

# ABU specifications (cruise ABUs)
abu_spec_cruise = {
  "n_abus": 1,
  "E_ops_kwh_per_abu": 12.0,
  "struct_frac": 0.20,
  "integration_frac": 0.05,
}

# prepare output storage
all_results   = []
timeline_rows = []

# sweep ABU pool sizes at takeoff & landing LZs
for n_takeoff_abu_pool in n_takeoff_abu_pool_list:
  for n_cruise_abu_pool in n_cruise_abu_pool_list:

    results = aircraft._evaluate_common_case_abu_combined_flight_overlap_charging_queuing(
      candidates                        = candidates,
      E_mission_kwh_per_abu_list       = E_mission_kwh_per_abu_list,
      abu_spec_takeoff                 = abu_spec_takeoff,
      abu_spec_cruise                  = abu_spec_cruise,
      n_abu_pool_takeoff               = n_takeoff_abu_pool,
      n_abu_pool_cruise                = n_cruise_abu_pool,
      P_charger_ac_kw                  = P_charger_ac_kw,
      eta_charger_dc                   = eta_charger_dc,
      c_rate_max                       = c_rate_max,
      v_pack_nom_v_main                = v_pack_nom_v_main,
      v_pack_nom_v_abu                 = v_pack_nom_v_abu,
      i_term_c                         = i_term_c,
      soc_target                       = soc_target,
      soc_cc_end                       = soc_cc_end,
      t_ground_ops_hr                  = t_ground_ops_hr,
      V_takeoff_abu_horizontal_m_p_s   = V_takeoff_abu_horizontal_m_p_s,
      V_takeoff_abu_vertical_m_p_s     = V_takeoff_abu_vertical_m_p_s,
      h_detach_takeoff_ft              = h_takeoff_detach_ft,
      V_cruise_abu_horizontal_m_p_s    = V_cruise_abu_horizontal_m_p_s,
      V_cruise_abu_vertical_m_p_s      = V_cruise_abu_vertical_m_p_s,
      h_detach_cruise_ft               = h_cruise_detach_ft,
      mission_time_s                   = mission_time_s
    )

    if results is None or len(results) == 0:
      print(
        f"No results returned for "
        f"n_takeoff_abu_pool = {n_takeoff_abu_pool}, "
        f"n_cruise_abu_pool = {n_cruise_abu_pool}"
      )
      continue

    # tag each row with the ABU pool sizes
    for row in results:
      row["n_takeoff_abu_pool"] = n_takeoff_abu_pool
      row["n_cruise_abu_pool"]  = n_cruise_abu_pool
      all_results.append(row)

      # timeline extraction
      aircraft_tl         = row.get("aircraft_timeline", [])
      takeoff_abu_tls     = row.get("takeoff_abu_timelines", {})
      cruise_abu_tls      = row.get("cruise_abu_timelines", {})

      # aircraft timeline events
      for entry in aircraft_tl:
        timeline_rows.append({
          "n_takeoff_abu_pool": n_takeoff_abu_pool,
          "n_cruise_abu_pool":  n_cruise_abu_pool,
          "E_abu_mission_cruise_per_abu_kwh": row.get("E_abu_mission_cruise_per_abu_kwh"),
          "timeline_type": "aircraft",
          "abu_index": "",
          "flight_index": (entry.get("flight_index") + 1) if entry.get("flight_index") is not None else "",
          "t_hr": entry.get("t_hr"),
          "event": entry.get("event"),
        })

      # takeoff ABU timelines
      for abu_idx, event_list in takeoff_abu_tls.items():
        for entry in event_list:
          timeline_rows.append({
            "n_takeoff_abu_pool": n_takeoff_abu_pool,
            "n_cruise_abu_pool":  n_cruise_abu_pool,
            "E_abu_mission_cruise_per_abu_kwh": row.get("E_abu_mission_cruise_per_abu_kwh"),
            "timeline_type": "takeoff_abu",
            "abu_index": (abu_idx + 1),
            "flight_index": (entry.get("flight_index") + 1) if entry.get("flight_index") is not None else "",
            "t_hr": entry.get("t_hr"),
            "event": entry.get("event"),
          })

      # cruise ABU timelines
      for abu_idx, event_list in cruise_abu_tls.items():
        for entry in event_list:
          timeline_rows.append({
            "n_takeoff_abu_pool": n_takeoff_abu_pool,
            "n_cruise_abu_pool":  n_cruise_abu_pool,
            "E_abu_mission_cruise_per_abu_kwh": row.get("E_abu_mission_cruise_per_abu_kwh"),
            "timeline_type": "cruise_abu",
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
  'mission-segment-abu-analysis-common-case-economics-combined-flight-overlap-charging-queuing.csv'
)

# define CSV fieldnames (must match evaluator 4.4.3 outputs)
fieldnames = [
  "n_takeoff_abu_pool",
  "n_cruise_abu_pool",

  # cruise ABU sweep parameter
  "E_abu_mission_cruise_per_abu_kwh",

  # main pack (post-takeoff + post-cruise-ABU)
  "E_pack_kwh_main",
  "E_mission_kwh_main",
  "dod_main",
  "soc_start_main",
  "soc_target",
  "soc_cc_end",

  # takeoff ABUs (per flight)
  "E_abu_used_takeoff_total_kwh",
  "E_ops_takeoff_per_abu_kwh",
  "E_pack_takeoff_abu_per_abu_kwh",
  "soc_start_abu_takeoff",
  "dod_abu_takeoff",
  "t_takeoff_attach_hr",
  "t_return_takeoff_abu_hr",

  # cruise ABUs (per flight)
  "E_abu_used_cruise_total_kwh",
  "E_saved_kwh_cruise",
  "E_ops_cruise_per_abu_kwh",
  "E_pack_cruise_abu_per_abu_kwh",
  "soc_start_abu_cruise",
  "dod_abu_cruise",
  "t_cruise_attach_hr",
  "t_cruise_attach_start_hr",
  "t_return_cruise_abu_hr",

  # combined timing
  "t_flight_hr",
  "t_charge_hr_main",
  "t_charge_hr_takeoff_abu",
  "t_charge_hr_cruise_abu",
  "t_cycle_nominal_hr",
  "n_flights_nominal_no_abu_limit",

  # 24-hour queuing simulation
  "n_flights_completed",
  "t_flight_day_hr",
  "t_slack_hr",
  "t_wait_takeoff_abu_day_hr",
  "t_wait_cruise_abu_day_hr",
  "abu_utilization_avg_takeoff",
  "abu_utilization_avg_cruise",
  "abu_bottleneck_takeoff_flag",
  "abu_bottleneck_cruise_flag",

  # CC–CV details (for reference)
  "P_cc_kw_main",
  "P_cc_kw_takeoff_abu",
  "P_cc_kw_cruise_abu",
  "charger_limit_indicator_flag_main",
  "charger_limit_indicator_flag_takeoff_abu",
  "charger_limit_indicator_flag_cruise_abu",
  
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
  'mission-segment-abu-analysis-common-case-economics-combined-flight-overlap-charging-queuing-timeline.csv'
)

timeline_fieldnames = [
  "n_takeoff_abu_pool",
  "n_cruise_abu_pool",
  "E_abu_mission_cruise_per_abu_kwh",
  "timeline_type",   # "aircraft", "takeoff_abu", "cruise_abu"
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
