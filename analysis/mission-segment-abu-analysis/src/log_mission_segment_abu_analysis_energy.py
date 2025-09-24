# log_mission_segment_abu_analysis_energy.py
#
# Usage: python3 log_mission_segment_abu_analysis_energy.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
# Output:
#  (1) mission-segment-abu-energy.csv -> per-candidate energy breakdown
#  (2) abu-detach-results.csv -> per-candidate summary
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

# define candidate detach points (example list — change as needed)
candidates = [
  {"name": "after_trans_climb", "segments": ["depart_taxi","hover_climb","trans_climb"]},
  {"name": "after_accel_climb", "segments": ["depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb"]},
  {"name": "mid_accel_50pct", "segments": ["depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb"], "frac_last_segment":0.5}
]

# segment order for consistent CSV columns
ordered_segments = [
    "depart_taxi","hover_climb","trans_climb","depart_proc","accel_climb",
    "cruise","decel_descend","arrive_proc","trans_descend","hover_descend","arrive_taxi",
    "reserve_hover_climb","reserve_trans_climb","reserve_accel_climb","reserve_cruise",
    "reserve_decel_descend","reserve_trans_descend","reserve_hover_descend"
]

# run ABU detach analysis
results = aircraft.evaluate_abu_detach_candidates(candidates)

# # write a single CSV: candidate + per-segment energies
# with open(log + 'mission-segment-abu-energy.csv', 'w', newline='') as csvfile:
#   writer = csv.writer(csvfile)
#   header = ['candidate'] + ordered_segments
#   writer.writerow(header)

#   for res in results:
#     # merge pre + post dicts to cover all segments
#     seg_energy_map = {}
#     seg_energy_map.update(res["pre_detach_energy_log"])
#     seg_energy_map.update(res["post_detach_energy_log"])

#     row = [res["name"]]
#     for seg in ordered_segments:
#       val = seg_energy_map.get(seg, 0.0)
#       row.append(f"{val:.6f}")
#     writer.writerow(row)

# write a single CSV: candidate + per-segment energies (seperate pre & post)
with open(log + 'mission-segment-abu-analysis-energy.csv', 'w', newline='') as csvfile:
  writer = csv.writer(csvfile)
  header = ['candidate'] + [seg+"_pre" for seg in ordered_segments] + [seg+"_post" for seg in ordered_segments]
  writer.writerow(header)

  for res in results:
      row = [res["name"]]
      for seg in ordered_segments:
          row.append(f"{res['pre_detach_energy_log'].get(seg,0.0):.6f}")
      for seg in ordered_segments:
          row.append(f"{res['post_detach_energy_log'].get(seg,0.0):.6f}")
      writer.writerow(row)

# write abu-detach-results.csv
with open(log + 'abu-detach-results.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    header = [
      "name",
      "energy_until_detach_kwh",
      "batt_mass_for_assist_kg",
      "baseline_batt_mass_kg",
      "batt_new_kg",
      "new_mtow_kg",
      "remaining_mission_kwh_est",
      "total_mission_kwh_with_new_mtow_est",
    ]
    writer.writerow(header)
    for res in results:
      row = [
        res["name"],
        f'{res["energy_until_detach_kwh"]:.6f}',
        f'{res["batt_mass_for_assist_kg"]:.6f}',
        f'{res["baseline_batt_mass_kg"]:.6f}',
        f'{res["batt_new_kg"]:.6f}',
        f'{res["new_mtow_kg"]:.6f}',
        f'{res["remaining_mission_kwh_est"]:.6f}',
        f'{res["total_mission_kwh_with_new_mtow_est"]:.6f}',
      ]
      writer.writerow(row)