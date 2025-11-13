# plt_mission_segment_abu_analysis_common_case_economics_extended_flight_overlap_charging_queuing_timeline.py
#
# Usage: python3 plt_mission_segment_abu_analysis_common_case_economics_extended_flight_overlap_charging_queuing_timeline.py /path/to/timeline.csv /path/to/plt/
#  Reads the timeline CSV file and saves operating-state timeline plots to the plt directory
#  Ensure that the Python virtual environment (venv) is enabled after running
#  setup_dependencies.sh: source p3-env/bin/activate
#
# Parameters:
#  /path/to/timeline.csv: path to timeline CSV file
#  /path/to/plt/: destination directory for plot files
#
# Output:
#  One PDF per (n_abu_pool, E_abu_mission_kwh_per_abu) combination, showing aircraft and ABU operating state timelines over 24 hours.
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
import os                       # directory handling

# initialize script arguments
log_csv = '' # path to timeline CSV file
out_dir = '' # destination directory for plot files

# parse script arguments
if len(sys.argv) == 3:
  log_csv = sys.argv[1]
  out_dir = sys.argv[2]
  if out_dir[-1] != '/':
    out_dir += '/'
else:
  print(
    'Usage: '
    'python3 plt_mission_segment_abu_analysis_common_case_economics_extended_flight_overlap_charging_queuing_timeline.py '
    '/path/to/timeline.csv /path/to/plt/'
  )
  exit()

# create output subfolder
subfolder = "plot_common-case-extended-flight-overlap-charging-queuing-timeline/"
full_out = out_dir + subfolder
os.makedirs(full_out, exist_ok=True)

# read the timeline CSV file
with open(log_csv, 'r') as csvfile:
  reader = csv.DictReader(csvfile)
  timeline_rows = list(reader)

if len(timeline_rows) == 0:
  print("No timeline rows found in CSV.")
  exit()

# group rows by (n_abu_pool, E_abu_mission_kwh_per_abu)
groups = {}  # key: (n_abu_pool, E_abu), value: dict with "aircraft" and "abu"
for row in timeline_rows:
  try:
    n_abu_pool = int(float(row.get("n_abu_pool", 0.0) or 0.0))
  except (TypeError, ValueError):
    n_abu_pool = 0

  try:
    E_abu = float(row.get("E_abu_mission_kwh_per_abu", 0.0) or 0.0)
  except (TypeError, ValueError):
    E_abu = 0.0

  key = (n_abu_pool, E_abu)

  if key not in groups:
    groups[key] = {
      "aircraft": [],
      "abu": [],
    }

  timeline_type = row.get("timeline_type", "").strip()

  try:
    t_hr = float(row.get("t_hr", 0.0) or 0.0)
  except (TypeError, ValueError):
    t_hr = 0.0

  flight_index_raw = row.get("flight_index", "")
  try:
    flight_index = int(round(float(flight_index_raw))) if flight_index_raw not in ("", None) else None
  except (TypeError, ValueError):
    flight_index = None

  abu_index_raw = row.get("abu_index", "")
  try:
    abu_index_val = float(abu_index_raw) if abu_index_raw not in ("", None) else None
  except (TypeError, ValueError):
    abu_index_val = None

  if abu_index_val is not None:
    abu_index = int(round(abu_index_val))
    if abu_index < 1:
      abu_index = 1
  else:
    abu_index = None

  event = row.get("event", "")

  entry = {
    "t_hr": t_hr,
    "flight_index": flight_index,
    "abu_index": abu_index,
    "event": event,
  }

  if timeline_type == "aircraft":
    groups[key]["aircraft"].append(entry)
  elif timeline_type == "abu":
    groups[key]["abu"].append(entry)
  else:
    continue

if len(groups) == 0:
  print("No valid aircraft or ABU timeline entries found.")
  exit()

def build_step_series_from_events(events, state_change_rules, t_end_hr=24.0, initial_state=0.0):
  events_sorted = sorted(events, key=lambda e: e["t_hr"])
  t_vals = []
  y_vals = []
  current_state = float(initial_state)
  current_time = 0.0

  t_vals.append(current_time)
  y_vals.append(current_state)

  for e in events_sorted:
    t_event = float(e.get("t_hr", 0.0) or 0.0)
    event_name = e.get("event", "")

    if t_event > t_end_hr:
      break

    if t_event >= current_time:
      t_vals.append(t_event)
      y_vals.append(current_state)

    if event_name in state_change_rules:
      current_state = float(state_change_rules[event_name])

    t_vals.append(t_event)
    y_vals.append(current_state)

    current_time = t_event

  if t_end_hr > current_time:
    t_vals.append(t_end_hr)
    y_vals.append(current_state)

  return t_vals, y_vals

# iterate over each (n_abu_pool, E_abu_mission_kwh_per_abu) combination
for (n_abu_pool, E_abu) in sorted(groups.keys(), key=lambda k: (k[0], k[1])):

  grp = groups[(n_abu_pool, E_abu)]
  aircraft_events = grp["aircraft"]
  abu_events = grp["abu"]

  if len(aircraft_events) == 0 and len(abu_events) == 0:
    continue

  max_time_aircraft = max([e["t_hr"] for e in aircraft_events], default=0.0)
  max_time_abu = max([e["t_hr"] for e in abu_events], default=0.0)
  t_end_hr = min(24.0, max(max_time_aircraft, max_time_abu, 24.0))

  aircraft_state_rules = {
    "aircraft_depart": 1.0,
    "aircraft_arrive": 0.0,
  }
  t_air, y_air = build_step_series_from_events(
    aircraft_events,
    aircraft_state_rules,
    t_end_hr=t_end_hr,
    initial_state=0.0
  )

  # build list of flight start (depart) times for markers
  flight_markers = []
  for e in aircraft_events:
      if e.get("event", "") == "aircraft_depart":
          t_dep = float(e.get("t_hr", 0.0) or 0.0)
          idx   = e.get("flight_index", None)
          if idx is not None:
              flight_markers.append((t_dep, idx))

  abu_by_index = {}
  for e in abu_events:
    idx = e.get("abu_index", None)
    if idx is None:
      continue
    if idx not in abu_by_index:
      abu_by_index[idx] = []
    abu_by_index[idx].append(e)

  abu_series = {}

  colors = plt.rcParams['axes.prop_cycle'].by_key().get('color', ['C0','C1','C2','C3','C4','C5','C6','C7','C8','C9'])

  for idx in sorted(abu_by_index.keys()):
    events_idx = abu_by_index[idx]

    abu_state_rules = {
      "abu_attached": 1.0,
      "abu_return_done": 0.0,
    }

    t_abu, y_abu = build_step_series_from_events(
      events_idx,
      abu_state_rules,
      t_end_hr=t_end_hr,
      initial_state=0.0
    )
    abu_series[idx] = (t_abu, y_abu)

  # create figure
  fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))

  # aircraft subplot
  ax1.step(t_air, y_air, where='post', label='Aircraft', linewidth=1.5)
  ax1.set_ylabel("Aircraft State\n(1=operating, 0=non-operating)")
  ax1.set_ylim(-0.1, 1.2)
  ax1.set_yticks([0, 1])
  ax1.grid(True, linestyle='--', alpha=0.4)

  title_str = (
    "Daily Operational Timeline\n"
    f"Number of ABUs: {n_abu_pool}, ABU mission-energy: {E_abu:.1f} kWh/ABU"
  )
  ax1.set_title(title_str)

  for idx in sorted(abu_series.keys()):
    t_abu, y_abu = abu_series[idx]
    color = colors[(idx - 1) % len(colors)]
    ax2.step(t_abu, y_abu, where='post', linewidth=1.5, color=color, label=f"ABU #{idx}")

  ax2.set_xlabel("Time [hr]")
  ax2.set_ylabel("ABU State\n(1=operating, 0=non-operating)")
  ax2.set_ylim(-0.1, 1.2)
  ax2.set_yticks([0, 1])
  ax2.grid(True, linestyle='--', alpha=0.4)

  leg = ax2.legend(title="Operating ABU", loc="upper right", fontsize=8)
  leg.get_title().set_fontsize(9)

  ax2.set_xlim(-0.5, 24.0)
  ax2.set_xticks(np.arange(0, 25, 4))

  # add vertical dashed lines + flight number labels
  for (t_dep, fidx) in flight_markers:
      # vertical dashed line spanning both panels
      ax1.axvline(t_dep, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
      ax2.axvline(t_dep, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)

      # flight number label positioned above the aircraft plot
      ax1.text(
          t_dep, 1.05,  # slightly above the top
          f"F{fidx}",   # compact label: F1, F2, F3...
          ha='center', va='bottom',
          fontsize=8, rotation=0, color='black'
      )

  plt.tight_layout()

  # clean E_abu_str for filename (remove unnecessary .0)
  if abs(E_abu - int(E_abu)) < 1e-9:
    E_abu_str = str(int(E_abu))
  else:
    E_abu_str = f"{E_abu:.1f}".replace('.', 'p')

  out_file = full_out + (
    "mission-segment-abu-analysis-common-case-economics-extended-flight-"
    f"overlap-charging-queuing-timeline-nABU{n_abu_pool}-EABU{E_abu_str}.pdf"
  )

  fig.savefig(out_file, format="pdf")
  plt.close(fig)