# log_mtow_iteration.py
#
# Usage: python3 log_mtow_iteration.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
# Output:
#  Maximum Takeoff Weight (MTOW) iteration results
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import csv
import sys
import os

# path to evtolpy package
sys.path.append('../../../evtol')
from aircraft import Aircraft

if len(sys.argv) == 3:
    cfg = sys.argv[1]
    log_dir = sys.argv[2]
    if log_dir[-1] != '/':
        log_dir += '/'
else:
    print("Usage: python3 log_mtow_iteration.py /path/to/cfg.json /path/to/log/")
    exit()

# create aircraft object
aircraft = Aircraft(cfg)

# run iteration
final_mtow, history = aircraft._iterate_mtow()

# write CSV log
log_path = os.path.join(log_dir, "mtow-iteration.csv")
with open(log_path, "w", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow([
        "iteration", "mtow_guess_kg", "new_mtow_kg", "delta_kg", 
        "empty_mass_kg", "battery_mass_kg", "payload_mass_kg", "total_energy_converged_kw_hr"
    ])
    for row in history:
        csvwriter.writerow([
            row["iteration"],
            f"{row['mtow_guess_kg']:.6f}",
            f"{row['new_mtow_kg']:.6f}",
            f"{row['delta_kg']:.6f}",
            f"{row['empty_mass_kg']:.6f}",
            f"{row['battery_mass_kg']:.6f}",
            f"{row['payload_mass_kg']:.6f}",
            f"{row['total_energy_converged_kw_hr']:.6f}"

        ])

