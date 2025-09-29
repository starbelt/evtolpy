# log_mission_segment_abu_analysis_energy.py
#
# Usage: python3 log_mission_segment_abu_analysis_energy.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
# Output:
#  (1) mission-segment-abu-analysis-energy.csv 
#  (2) abu-detach-results.csv 
#  (3) abu-mass-breakdown.csv
#
# Written by First Last
# Other contributors:
#
# See the LICENSE file for the license

# import Python modules
import csv # csv
import sys # argv

# path to directory containing evtolpy package; use before deploying as package
sys.path.append('../../../evtol')
from aircraft import Aircraft

# initialize script arguments
cfg = '' # path to configuration JSON file
log = '' # destination directory for log files

# parse script arguments
if len(sys.argv)==3:
  cfg = sys.argv[1]
  log = sys.argv[2]
  if log[-1] != '/':
    log += '/'
else:
  print(
   'Usage: '
   'python3 log_mission_segment_abu_analysis_energy.py '
   '/path/to/cfg.json /path/to/log/'
  )
  exit()

# construct an aircraft object from the specified configuration
aircraft = Aircraft(cfg)

# define candidate detach points (user-defined)
candidates = [
  # {"name": "after_trans_climb", "segments": ["depart_taxi","hover_climb","trans_climb"]},
  {"name": "after_accel_climb", "segments": ["depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb"]},
]

# segment order for consistent CSV columns
ordered_segments = [
    "depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb",
    "cruise","decel_descend","arrive_proc","trans_descend","hover_descend","arrive_taxi",
    "reserve_hover_climb","reserve_trans_climb","reserve_accel_climb","reserve_cruise",
    "reserve_decel_descend","reserve_trans_descend","reserve_hover_descend"
]

# example ABU spec (user-defined)
abu_spec = {
    "n_abus": 1,
    "E_mission_kwh_per_abu": 10.0,
    "E_ops_kwh_per_abu": 0.5,
    "m_struct_kg_per_abu": 20.0,
    "m_integration_kg_per_abu": 2.0,
}

# run ABU detach analysis
results = aircraft.evaluate_abu_detach_candidates(candidates, abu_spec=abu_spec)

# write mission-segment-abu-analysis-energy.csv (pre & post segment energies)
with open(log + 'mission-segment-abu-analysis-energy.csv', 'w', newline='') as csvfile:
  writer = csv.writer(csvfile)
  header = ['candidate'] + [seg+"_pre" for seg in ordered_segments] + [seg+"_post" for seg in ordered_segments]
  writer.writerow(header)

  for res in results:
    row = [res["name"]]
    # pre-detach energies 
    for seg in ordered_segments:
      row.append(f"{res['pre_detach_segment_log'].get(seg, {}).get('seg_total_kwh',0.0):.6f}")
    # post-detach energies 
    for seg in ordered_segments:
      val = res['post_detach_segment_log'].get(seg, 0.0)
      if isinstance(val, dict):
        row.append(f"{val.get('seg_total_kwh',0.0):.6f}")
      else:
        row.append(f"{val:.6f}")
    writer.writerow(row)

# write abu-detach-results.csv
with open(log + 'abu-detach-results.csv', 'w', newline='') as csvfile:
  writer = csv.writer(csvfile)
  header = [
    "name",
    "E_abu_mission_total_kwh",
    "E_abu_ops_total_kwh",
    "E_abu_used_kwh",
    "batt_mass_offloaded_kg",
    "baseline_batt_mass_kg",
    "main_batt_new_kg",
    "MTOW_attached_kg",
    "MTOW_detached_kg",
    "feasible_ops",
    "baseline_total_mission_kwh",
    "aircraft_total_kwh_after",
    "total_system_kwh_after"
  ]
  writer.writerow(header)

  for res in results:
    row = [
      res["name"],
      f'{res["E_abu_mission_total_kwh"]:.6f}',
      f'{res["E_abu_ops_total_kwh"]:.6f}',
      f'{res["E_abu_used_kwh"]:.6f}',
      f'{res["batt_mass_offloaded_kg"]:.6f}',
      f'{res["baseline_batt_mass_kg"]:.6f}',
      f'{res["main_batt_new_kg"]:.6f}',
      f'{res["MTOW_attached_kg"]:.6f}',
      f'{res["MTOW_detached_kg"]:.6f}',
      str(res["feasible_ops"]),
      f'{res["baseline_total_mission_kwh"]:.6f}',
      f'{res["aircraft_total_kwh_after"]:.6f}',
      f'{res["total_system_kwh_after"]:.6f}',
    ]
    writer.writerow(row)

# write abu-mass-breakdown.csv
with open(log + 'abu-mass-breakdown.csv', 'w', newline='') as csvfile:
  writer = csv.writer(csvfile)
  header = [
    "name",
    "n_abus",
    "m_struct_total_kg",
    "m_integration_total_kg",
    "m_rotor_total_kg",
    "m_batt_mission_total_kg",
    "m_batt_ops_total_kg",
    "m_abu_total_per_abu_kg",
    "m_abu_total_all_kg",
  ]
  writer.writerow(header)

  for res in results:
    abu = res["abu_mass_breakdown"]
    row = [
      res["name"],
      abu["n_abus"],
      f'{abu["m_struct_total_kg"]:.6f}',
      f'{abu["m_integration_total_kg"]:.6f}',
      f'{abu["m_rotor_total_kg"]:.6f}',
      f'{abu["m_batt_mission_total_kg"]:.6f}',
      f'{abu["m_batt_ops_total_kg"]:.6f}',
      f'{abu["m_abu_total_per_abu_kg"]:.6f}',
      f'{abu["m_abu_total_all_kg"]:.6f}',
    ]
    writer.writerow(row)
