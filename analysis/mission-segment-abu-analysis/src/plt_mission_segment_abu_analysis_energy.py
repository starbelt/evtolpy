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
# Other contributors: 
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
data_rows = rows[1:]       # each row is a candidate

# parse header columns into base_name and suffix (pre/post/remainder/none)
col_info = []  # list of tuples (col_index, base_name, suffix)
pattern = re.compile(r'^(?P<base>.+?)(?:_(?P<suffix>pre|post|remainder))?$')

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

segments = header[1:]
human_labels = [seg_label_map.get(seg, seg) for seg in segments]

for idx, col in enumerate(header):
  if idx == 0:
    # first column should be 'candidate' (name)
    col_info.append((idx, 'candidate', None))
    continue
  m = pattern.match(col)
  if not m:
    base = col
    suffix = None
  else:
    base = m.group('base')
    suffix = m.group('suffix')  # may be None
  col_info.append((idx, base, suffix))

# build ordered base list preserving header order
base_order = []
for _, base, _ in col_info[1:]:
  if base not in base_order:
    base_order.append(base)

# create mapping base -> dict of column indices for suffix types
base_col_indices = {b: {'pre': None, 'post': None, 'remainder': None, 'none': None} for b in base_order}
for idx, base, suffix in col_info[1:]:
  key = 'none' if suffix is None else suffix
  # if multiple same-named columns exist, prefer explicit pre/post over none, but keep last-seen
  base_col_indices[base][key] = idx

# helper to parse float robustly
def _to_float(s):
  try:
    return float(s)
  except Exception:
    return 0.0

# loop candidates and plot each
for row in data_rows:
  if len(row) == 0:
    continue
  cand_name = row[0]
  # arrays to hold pre and post numeric values per base segment
  pre_vals = []
  post_vals = []
  total_vals = []
  bases = base_order  # for plotting X axis

  for base in bases:
    cols = base_col_indices[base]
    pre_val = 0.0
    post_val = 0.0
    none_val = 0.0
    remainder_val = 0.0

    # fetch numbers if indices exist
    if cols['pre'] is not None and cols['pre'] < len(row):
      pre_val = _to_float(row[cols['pre']])
    if cols['post'] is not None and cols['post'] < len(row):
      post_val = _to_float(row[cols['post']])
    if cols['remainder'] is not None and cols['remainder'] < len(row):
      remainder_val = _to_float(row[cols['remainder']])
    if cols['none'] is not None and cols['none'] < len(row):
      none_val = _to_float(row[cols['none']])

    # interpret none_val:
    # - If both pre and post are zero and none_val exists, treat none_val as the segment's value (no explicit split).
    # - If pre or post are present, treat none_val as additional (rare).
    if pre_val == 0.0 and post_val == 0.0 and (not isclose(none_val, 0.0)):
      # single-column case, assume entire value is 'pre' if it's in the early segments
      # We'll treat it as 'pre' initially — split point determined below
      pre_val = none_val

    # remainder is a 'post' contribution to the same segment (e.g. fractional remainder of last segment)
    post_val += remainder_val

    pre_vals.append(pre_val)
    post_vals.append(post_val)
    total_vals.append(pre_val + post_val)

  # determine split index for dashed line:
  # find last index where pre_vals > 0 (meaning that segment was supplied pre-detach)
  last_pre_idx = -1
  for i, pv in enumerate(pre_vals):
    if pv > 1e-9:   # small tolerance
      last_pre_idx = i

  # If no explicit pre-post columns were present and pre_vals are all non-zero (single-column case),
  # try to detect split by finding a contiguous run of non-zero values at start that correspond to pre.
  # (but only if no explicit pre/post were present in header)
  explicit_prepost_present = any(('pre' in h or 'post' in h or 'remainder' in h) for h in header[1:])
  if (last_pre_idx == len(bases)-1) and (not explicit_prepost_present):
    # try to find reasonable split by searching for a big jump (this is heuristic)
    vals = total_vals
    # look for index where cumulative energy crosses 50% of total or a large drop in per-segment energy
    tot = sum(vals)
    if tot > 0:
      cum = 0.0
      split_candidate = -1
      for i, v in enumerate(vals):
        cum += v
        if cum >= 0.5*tot:
          split_candidate = i
          break
      if split_candidate >= 0:
          last_pre_idx = split_candidate

  # plotting
  N = len(bases)
  x = np.arange(N)
  width = 0.8

  fig, ax = plt.subplots(figsize=(14, 6))

  pre_color = 'tab:blue'
  post_color = 'tab:orange'

  # decide one value + one color per segment
  seg_vals = []
  seg_colors = []
  last_pre_idx = -1
  for i, base in enumerate(bases):
    pre_val = pre_vals[i]
    post_val = post_vals[i]
    total_val = total_vals[i]

    if pre_val > 1e-9:   # treat as pre-detach
      seg_vals.append(pre_val)
      seg_colors.append(pre_color)
      last_pre_idx = i
    elif post_val > 1e-9:  # treat as post-detach
      seg_vals.append(post_val)
      seg_colors.append(post_color)
    else:
      seg_vals.append(0.0)
      seg_colors.append('lightgrey')  # unused / zero

  # draw bars
  bars = ax.bar(x, seg_vals, width, color=seg_colors)

  # annotate values
  for i, v in enumerate(seg_vals):
    if v > 1e-8:
      ax.text(
        x[i],
        v + 0.01 * max(1.0, max(seg_vals)),
        f"{v:.4f}",
        ha='center',
        va='bottom',
        fontsize=8
      )

  # dashed vertical separator at detach point
  if last_pre_idx >= 0 and last_pre_idx < N - 1:
    ax.axvline(last_pre_idx + 0.5, color='k', linestyle='--', linewidth=1.0)

  # x tick labels: human-readable names
  human_labels = [seg_label_map.get(b, b.replace('_', ' ').title()) for b in bases]
  ax.set_xticks(x)
  ax.set_xticklabels(human_labels, rotation=45, ha='right')

  # title with full detach segment name
  detach_seg_label = human_labels[last_pre_idx] if last_pre_idx >= 0 else "Unknown"
  ax.set_title(f"Mission Segment Energy \nDetach After {detach_seg_label}")

  ax.set_ylabel("Energy (kW·hr)")
  ax.set_xlabel("Mission Segment")

  # add legend manually (since bars are colored by logic)
  legend_handles = [
    plt.Rectangle((0,0),1,1, color=pre_color, label="Pre-detach"),
    plt.Rectangle((0,0),1,1, color=post_color, label="Post-detach")
  ]
  ax.legend(handles=legend_handles, loc="upper right")

  plt.tight_layout()

  # save figure
  fname = out_dir + f"mission-segment-abu-analysis-energy-{cand_name}.pdf"
  fig.savefig(fname, format='pdf')
  plt.close(fig)