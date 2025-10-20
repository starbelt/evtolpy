# plt_mission_segment_abu_analysis_landing_safety_loiter.py
#
# Usage: python3 plt_mission_segment_abu_analysis_landing_safety_loiter.py /path/to/log.csv /path/to/plt/
#  Reads the log CSV file and saves the plot to the plt directory
#  Ensure that the Python virtual environment (venv) is enabled after running
#  setup_dependencies.sh: source p3-env/bin/activate
#
# Parameters:
#  /path/to/log.csv: path to log CSV file
#  /path/to/plt/: destination directory for plot files
# Output:
#  Plot of ABU Mission Energy vs. Maximum Extra Loiter Time (Landing Safety Benefit)
#
# Written by First Last
# Other contributors:
#
# See the LICENSE file for the license

import csv
import matplotlib.pyplot as plt
import sys
import os

# parse args
if len(sys.argv) == 3:
    input_csv_path = sys.argv[1]
    output_dir = sys.argv[2]
    if output_dir[-1] != '/':
        output_dir += '/'
else:
    print(
        "Usage:\n"
        "  python3 plt_mission_segment_abu_analysis_landing_safety_loiter.py "
        "/path/to/log.csv /path/to/plt/"
    )
    sys.exit(1)

# read CSV
rows = []
with open(input_csv_path, "r", newline="") as csv_file:
    reader = csv.reader(csv_file)
    rows = list(reader)

headers = [h.strip() for h in rows[0]]
data_rows = rows[1:]

# helpers
def safe_float(value):
    """Convert string to float safely."""
    try:
        return float(value)
    except Exception:
        return None

# build column map
columns = {h: [] for h in headers}
for row in data_rows:
    for h, v in zip(headers, row):
        columns[h].append(v.strip())

# extract primary fields
energy_list = [safe_float(x) for x in columns.get("E_abu_mission_kwh", [])]
loiter_time_list = [safe_float(x) for x in columns.get("t_loiter_hover_max_s", [])]
note_list = columns.get("note", [])

# parse and classify feasibility
data_points = []
for energy, loiter_time, note in zip(energy_list, loiter_time_list, note_list):
    if energy is None or loiter_time is None:
        continue

    note_text = note.strip().lower() if note else ""
    is_feasible = "feasible" in note_text and "insufficient" not in note_text

    data_points.append((energy, loiter_time, is_feasible))

# sort by energy and separate cases
data_points.sort(key=lambda x: x[0])

feasible_data = [(e, t) for (e, t, ok) in data_points if ok]
infeasible_data = [(e, t) for (e, t, ok) in data_points if not ok]

energy_feasible, loiter_feasible = zip(*feasible_data) if feasible_data else ([], [])
energy_infeasible, loiter_infeasible = zip(*infeasible_data) if infeasible_data else ([], [])

# plot configuration
plt.figure(figsize=(9, 6))

if energy_feasible:
    plt.plot(
        energy_feasible,
        loiter_feasible,
        "-o",
        color="tab:blue",
        label="Feasible",
        linewidth=1.8,
        markersize=5,
    )

if energy_infeasible:
    plt.plot(
        energy_infeasible,
        loiter_infeasible,
        "x",
        color="tab:red",
        label="Infeasible",
        markersize=7,
        mew=1.5,
    )

# annotate data values
def annotate_points(x_list, y_list, color):
    if not x_list or not y_list:
        return
    max_y = max(y_list)
    for x, y in zip(x_list, y_list):
        plt.text(
            x,
            y + 0.015 * max_y,  # small vertical offset
            f"{y:.1f}",         # display 1 decimal place
            ha="center",
            va="bottom",
            fontsize=8,
            color=color,
        )

annotate_points(energy_feasible, loiter_feasible, "tab:blue")
annotate_points(energy_infeasible, loiter_infeasible, "tab:red")

# title and labels
plt.title("ABU Landing Safety Benefit\nMaximum Extra Loiter Time vs. ABU Mission Energy")
plt.xlabel("ABU Mission Energy per Unit (kWh)")
plt.ylabel("Maximum Extra Loiter Time (seconds)")
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(loc="upper left", fontsize=9)
plt.margins(x=0.1, y=0.1)
plt.tight_layout()

# save figure
output_path = os.path.join(
    output_dir, "mission-segment-abu-analysis-landing-safety-loiter.pdf"
)
plt.savefig(output_path, format="pdf")
plt.close()