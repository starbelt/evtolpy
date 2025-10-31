# plt_mission_segment_abu_analysis_energy.py
# 
# Usage: python3 plt_mission_segment_abu_analysis_energy.py /path/to/log.csv /path/to/plt/
#  Reads the log CSV file and saves the plot to the plt directory
#  Ensure that the Python virtual environment (venv) is enabled after running
#  setup_dependencies.sh: source p3-env/bin/activate
#
# Parameters:
#  /path/to/log.csv: path to log CSV file
#  /path/to/plt/: destination directory for plot files
# Output:
#  Plot comparing segment energy for each detach candidate
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import csv                      # csv
import matplotlib.pyplot as plt # matplotlib
import numpy as np              # numpy
import sys                      # argv
import re
from math import isclose

# initialize script arguments
log = '' # path to log CSV file
out = '' # destination directory for plot files

# parse script arguments
if len(sys.argv) == 3:
  log_csv = sys.argv[1]
  out_dir = sys.argv[2]
  if out_dir[-1] != '/':
      out_dir += '/'
else:
  print(
    'Usage: '
    'python3 plt_mission_segment_abu_analysis_energy.py '
    '/path/to/log.csv /path/to/plt/'
  )
  exit()

# read the log CSV file
with open(log_csv, 'r') as csvfile:
  reader = csv.reader(csvfile)
  rows = list(reader)

# header and rows
header = rows[0]           # e.g. ['candidate','depart_taxi_pre','hover_climb_pre',...]
data_rows = rows[1:]       # one row per candidate

# mapping segment label
seg_label_map = {
  "depart_taxi": "Depart Taxi",
  "hover_climb": "Hover Climb",
  "trans_climb": "Transition Climb",
  "depart_proc": "Depart Procedures",
  "accel_climb": "Accelerate Climb",
  "cruise": "Cruise",
  "decel_descend": "Decelerate Descend",
  "arrive_proc": "Arrive Procedures",
  "trans_descend": "Transition Descend",
  "hover_descend": "Hover Descend",
  "arrive_taxi": "Arrive Taxi",
  "reserve_hover_climb": "Reserve Hover Climb",
  "reserve_trans_climb": "Reserve Transition Climb",
  "reserve_accel_climb": "Reserve Accelerate Climb",
  "reserve_cruise": "Reserve Cruise",
  "reserve_decel_descend": "Reserve Decelerate Descend",
  "reserve_trans_descend": "Reserve Transition Descend",
  "reserve_hover_descend": "Reserve Hover Descend",
}

## parse header into (segment_base, suffix)
# example: 'hover_climb_pre' → ('hover_climb','pre')
pattern = re.compile(r"^(?P<base>.+?)(?:_(?P<suffix>pre|post|remainder))?$")
col_info = []
for idx, col in enumerate(header):
  if idx == 0:
    col_info.append((idx, "candidate", None))
    continue
  match = pattern.match(col)
  base = match.group("base") if match else col
  suffix = match.group("suffix") if match else None
  col_info.append((idx, base, suffix))

# preserve order of base segments
base_order = []
for _, seg_base, _ in col_info[1:]:
  if seg_base not in base_order:
    base_order.append(seg_base)

# map base segment → column indices per suffix
base_col_indices = {b: {"pre": None, "post": None, "remainder": None, "none": None} for b in base_order}
for idx, seg_base, suffix in col_info[1:]:
  key = "none" if suffix is None else suffix
  base_col_indices[seg_base][key] = idx

## helper to safely parse floats
def safe_float(s):
  try:
    return float(s)
  except Exception:
    return 0.0

## main loop: process each candidate row
for cand_row in data_rows:
  if not cand_row:
    continue
  cand_name = cand_row[0]

  pre_energy, post_energy, total_energy = [], [], []

  # collect segment-wise values
  for seg_base in base_order:
    cols = base_col_indices[seg_base]
    pre_val = safe_float(cand_row[cols["pre"]]) if cols["pre"] else 0.0
    post_val = safe_float(cand_row[cols["post"]]) if cols["post"] else 0.0
    remainder_val = safe_float(cand_row[cols["remainder"]]) if cols["remainder"] else 0.0
    none_val = safe_float(cand_row[cols["none"]]) if cols["none"] else 0.0

    # handle "none" suffix (no pre/post distinction in CSV)
    if pre_val == 0.0 and post_val == 0.0 and not isclose(none_val, 0.0):
      pre_val = none_val  # assign entirely to pre-detach

    # remainder counts toward post-detach
    post_val += remainder_val

    pre_energy.append(pre_val)
    post_energy.append(post_val)
    total_energy.append(pre_val + post_val)

  # find last pre-detach segment index
  last_pre_idx = max((i for i, v in enumerate(pre_energy) if v > 1e-9), default=-1)


  ## plotting
  N = len(base_order)
  x = np.arange(N)

  fig, ax = plt.subplots(figsize=(14, 6))

  colors = []
  seg_vals = []
  for i, seg_base in enumerate(base_order):
    if pre_energy[i] > 1e-9:
      seg_vals.append(pre_energy[i])
      colors.append("tab:blue")
    elif post_energy[i] > 1e-9:
      seg_vals.append(post_energy[i])
      colors.append("tab:orange")
    else:
      seg_vals.append(0.0)
      colors.append("lightgrey")

  # draw bars
  bars = ax.bar(x, seg_vals, width=0.8, color=colors)

  # annotate values above bars
  for i, v in enumerate(seg_vals):
    if v > 1e-8:
      ax.text(
        x[i],
        v + 0.01 * max(1.0, max(seg_vals)),
        f"{v:.4f}",
        ha="center",
        va="bottom",
        fontsize=8,
      )

  # add dashed line at detach point
  if 0 <= last_pre_idx < N - 1:
    ax.axvline(last_pre_idx + 0.5, color="k", linestyle="--", linewidth=1.0)

  # labels
  human_labels = [seg_label_map.get(b, b.replace("_", " ").title()) for b in base_order]
  ax.set_xticks(x)
  ax.set_xticklabels(human_labels, rotation=45, ha="right")

  detach_label = human_labels[last_pre_idx] if last_pre_idx >= 0 else "Unknown"
  ax.set_title(f"Mission Segment Energy \nDetach After {detach_label}")
  ax.set_ylabel("Energy (kW·hr)")
  ax.set_xlabel("Mission Segment")

  # Legend
  legend_handles = [
    plt.Rectangle((0, 0), 1, 1, color="tab:blue", label="Pre-detach"),
    plt.Rectangle((0, 0), 1, 1, color="tab:orange", label="Post-detach"),
  ]
  ax.legend(handles=legend_handles, loc="upper right")

  plt.tight_layout()

  # save figure
  out_file = out_dir + f"mission-segment-abu-analysis-energy-{cand_name}.pdf"
  fig.savefig(out_file, format="pdf")
  plt.close(fig)