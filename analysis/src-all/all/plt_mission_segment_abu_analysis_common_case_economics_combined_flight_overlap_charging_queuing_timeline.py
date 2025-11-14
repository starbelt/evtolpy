# plt_mission_segment_abu_analysis_common_case_economics_combined_flight_overlap_charging_queuing_timeline.py
#
# Usage: python3 plt_mission_segment_abu_analysis_common_case_economics_combined_flight_overlap_charging_queuing_timeline.py /path/to/timeline.csv /path/to/plt/
#  Reads the timeline CSV file and saves operating-state timeline plots to the plt directory
#  Ensure that the Python virtual environment (venv) is enabled after running
#  setup_dependencies.sh: source p3-env/bin/activate
#
# Parameters:
#  /path/to/timeline.csv: path to timeline CSV file
#  /path/to/plt/: destination directory for plot files
#
# Output:
#  One PDF per (n_takeoff_abu_pool, n_cruise_abu_pool, E_abu_mission_cruise_per_abu_kwh) combination,
#  showing aircraft, takeoff ABU, and cruise ABU operating-state timelines over 24 hours.
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
    'python3 plt_mission_segment_abu_analysis_common_case_economics_combined_flight_overlap_charging_queuing_timeline.py '
    '/path/to/timeline.csv /path/to/plt/'
  )
  exit()

# create output subfolder
subfolder = "plot_common-case-combined-flight-overlap-charging-queuing-timeline/"
full_out = out_dir + subfolder
os.makedirs(full_out, exist_ok=True)

# read the timeline CSV file
with open(log_csv, 'r') as csvfile:
  reader = csv.DictReader(csvfile)
  timeline_rows = list(reader)

if len(timeline_rows) == 0:
  print("No timeline rows found in CSV.")
  exit()

# group rows by (n_takeoff_abu_pool, n_cruise_abu_pool, E_abu_mission_cruise_per_abu_kwh)
groups = {}  # key: (n_takeoff_pool, n_cruise_pool, E_abu), value: dict with "aircraft", "takeoff_abu", "cruise_abu"
for row in timeline_rows:
  # parse pool sizes
  try:
    n_takeoff_abu_pool = int(float(row.get("n_takeoff_abu_pool", 0.0) or 0.0))
  except (TypeError, ValueError):
    n_takeoff_abu_pool = 0

  try:
    n_cruise_abu_pool = int(float(row.get("n_cruise_abu_pool", 0.0) or 0.0))
  except (TypeError, ValueError):
    n_cruise_abu_pool = 0

  # parse cruise ABU mission energy
  try:
    E_abu = float(row.get("E_abu_mission_cruise_per_abu_kwh", 0.0) or 0.0)
  except (TypeError, ValueError):
    E_abu = 0.0

  key = (n_takeoff_abu_pool, n_cruise_abu_pool, E_abu)

  if key not in groups:
    groups[key] = {
      "aircraft": [],
      "takeoff_abu": [],
      "cruise_abu": [],
    }

  timeline_type = row.get("timeline_type", "").strip()

  # parse time
  try:
    t_hr = float(row.get("t_hr", 0.0) or 0.0)
  except (TypeError, ValueError):
    t_hr = 0.0

  # parse flight index 
  flight_index_raw = row.get("flight_index", "")
  try:
    flight_index = int(round(float(flight_index_raw))) if flight_index_raw not in ("", None) else None
  except (TypeError, ValueError):
    flight_index = None

  # parse ABU index
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
  elif timeline_type == "takeoff_abu":
    groups[key]["takeoff_abu"].append(entry)
  elif timeline_type == "cruise_abu":
    groups[key]["cruise_abu"].append(entry)
  else:
    continue

if len(groups) == 0:
  print("No valid aircraft or ABU timeline entries found.")
  exit()

# build a stepwise (time, state) series from discrete events.
def build_step_series_from_events(events, state_change_rules, t_end_hr=24.0, initial_state=0.0):

  events_sorted = sorted(events, key=lambda e: e["t_hr"])
  t_vals = []
  y_vals = []
  current_state = float(initial_state)
  current_time = 0.0

  # initial state at t=0
  t_vals.append(current_time)
  y_vals.append(current_state)

  for e in events_sorted:
    t_event = float(e.get("t_hr", 0.0) or 0.0)
    event_name = e.get("event", "")

    if t_event > t_end_hr:
      break

    # keep horizontal segment until event time
    if t_event >= current_time:
      t_vals.append(t_event)
      y_vals.append(current_state)

    # state change if event is known
    if event_name in state_change_rules:
      current_state = float(state_change_rules[event_name])

    # vertical jump at event time
    t_vals.append(t_event)
    y_vals.append(current_state)

    current_time = t_event

  # extend to t_end_hr
  if t_end_hr > current_time:
    t_vals.append(t_end_hr)
    y_vals.append(current_state)

  return t_vals, y_vals

# iterate over each (n_takeoff_abu_pool, n_cruise_abu_pool, E_abu) combination
for (n_takeoff_abu_pool, n_cruise_abu_pool, E_abu) in sorted(
  groups.keys(), key=lambda k: (k[0], k[1], k[2])
):

  grp = groups[(n_takeoff_abu_pool, n_cruise_abu_pool, E_abu)]
  aircraft_events     = grp["aircraft"]
  takeoff_abu_events  = grp["takeoff_abu"]
  cruise_abu_events   = grp["cruise_abu"]

  if len(aircraft_events) == 0 and len(takeoff_abu_events) == 0 and len(cruise_abu_events) == 0:
    continue

  # 24-hour horizon
  t_end_hr = 24.0

  # aircraft state rules: operating when in-flight, non-operating otherwise
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

  # group ABU events by index (for takeoff ABUs)
  takeoff_by_index = {}
  for e in takeoff_abu_events:
    idx = e.get("abu_index", None)
    if idx is None:
      continue
    if idx not in takeoff_by_index:
      takeoff_by_index[idx] = []
    takeoff_by_index[idx].append(e)

  # group ABU events by index (for cruise ABUs)
  cruise_by_index = {}
  for e in cruise_abu_events:
    idx = e.get("abu_index", None)
    if idx is None:
      continue
    if idx not in cruise_by_index:
      cruise_by_index[idx] = []
    cruise_by_index[idx].append(e)

  # build ABU series (operating / non-operating) for each index
  takeoff_abu_series = {}
  cruise_abu_series  = {}

  colors = plt.rcParams['axes.prop_cycle'].by_key().get('color', ['C0','C1','C2','C3','C4','C5','C6','C7','C8','C9'])

  # takeoff ABUs: operating when attached; non-operating after return / charge done
  for idx in sorted(takeoff_by_index.keys()):
    events_idx = takeoff_by_index[idx]

    takeoff_state_rules = {
      "takeoff_abu_attached": 1.0,
      "takeoff_abu_return_done": 0.0,
      "takeoff_abu_charge_done": 0.0,
    }

    t_to, y_to = build_step_series_from_events(
      events_idx,
      takeoff_state_rules,
      t_end_hr=t_end_hr,
      initial_state=0.0
    )
    takeoff_abu_series[idx] = (t_to, y_to)

  # cruise ABUs: operating when attached; non-operating after return / charge done
  for idx in sorted(cruise_by_index.keys()):
    events_idx = cruise_by_index[idx]

    cruise_state_rules = {
      "cruise_abu_attached": 1.0,
      "cruise_abu_return_done": 0.0,
      "cruise_abu_charge_done": 0.0,
    }

    t_cr, y_cr = build_step_series_from_events(
      events_idx,
      cruise_state_rules,
      t_end_hr=t_end_hr,
      initial_state=0.0
    )
    cruise_abu_series[idx] = (t_cr, y_cr)

  # create figure: 3 stacked subplots (aircraft, takeoff ABUs, cruise ABUs)
  fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(10, 8))

  # aircraft subplot
  ax1.step(t_air, y_air, where='post', label='Aircraft', linewidth=1.5)
  ax1.set_ylabel("Aircraft State\n(1=operating, 0=non-operating)")
  ax1.set_ylim(-0.1, 1.2)
  ax1.set_yticks([0, 1])
  ax1.grid(True, linestyle='--', alpha=0.4)

  title_str = (
    "Daily Operational Timeline\n"
    f"Takeoff ABU pool: {n_takeoff_abu_pool}, Cruise ABU pool: {n_cruise_abu_pool}, "
    f"Cruise ABU mission energy: {E_abu:.1f} kWh/ABU"
  )
  ax1.set_title(title_str)

  # takeoff ABU subplot
  if len(takeoff_abu_series) > 0:
    for idx in sorted(takeoff_abu_series.keys()):
      t_to, y_to = takeoff_abu_series[idx]
      color = colors[(idx - 1) % len(colors)]
      ax2.step(t_to, y_to, where='post', linewidth=1.5, color=color, label=f"Takeoff ABU #{idx}")
  ax2.set_ylabel("Takeoff ABU State\n(1=operating, 0=non-operating)")
  ax2.set_ylim(-0.1, 1.2)
  ax2.set_yticks([0, 1])
  ax2.grid(True, linestyle='--', alpha=0.4)
  if len(takeoff_abu_series) > 0:
    leg2 = ax2.legend(title="Operating Takeoff ABU", loc="upper right", fontsize=8)
    leg2.get_title().set_fontsize(9)

  # cruise ABU subplot
  if len(cruise_abu_series) > 0:
    for idx in sorted(cruise_abu_series.keys()):
      t_cr, y_cr = cruise_abu_series[idx]
      color = colors[(idx - 1) % len(colors)]
      ax3.step(t_cr, y_cr, where='post', linewidth=1.5, color=color, label=f"Cruise ABU #{idx}")
  ax3.set_xlabel("Time [hr]")
  ax3.set_ylabel("Cruise ABU State\n(1=operating, 0=non-operating)")
  ax3.set_ylim(-0.1, 1.2)
  ax3.set_yticks([0, 1])
  ax3.grid(True, linestyle='--', alpha=0.4)
  if len(cruise_abu_series) > 0:
    leg3 = ax3.legend(title="Operating Cruise ABU", loc="upper right", fontsize=8)
    leg3.get_title().set_fontsize(9)

  # x-axis limits and ticks
  ax3.set_xlim(-0.5, 24.0)
  ax3.set_xticks(np.arange(0, 25, 4))

  # choose only first, middle, and last flights for labeling
  n_flights = len(flight_markers)

  if n_flights == 0:
      labeled_markers = []
  elif n_flights == 1:
      labeled_markers = [flight_markers[0]]
  elif n_flights == 2:
      labeled_markers = [flight_markers[0], flight_markers[-1]]
  else:
      # first, middle, last
      mid_idx = n_flights // 2
      labeled_markers = [
          flight_markers[0],
          flight_markers[mid_idx],
          flight_markers[-1]
      ]

  # ensure sorted by time 
  labeled_markers = sorted(labeled_markers, key=lambda x: x[0])

  # add vertical dashed lines + flight number labels
  for (t_dep, fidx) in labeled_markers:
    # vertical dashed line spanning all three panels
    ax1.axvline(t_dep, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
    ax2.axvline(t_dep, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
    ax3.axvline(t_dep, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)

    # flight number label above aircraft plot
    ax1.text(
      t_dep, 1.05,
      f"F{fidx}",
      ha='center', va='bottom',
      fontsize=8, color='black'
    )

  plt.tight_layout()

  # clean E_abu_str for filename (remove unnecessary .0)
  if abs(E_abu - int(E_abu)) < 1e-9:
    E_abu_str = str(int(E_abu))
  else:
    E_abu_str = f"{E_abu:.1f}".replace('.', 'p')

  out_file = full_out + (
    f"nTakeoff{n_takeoff_abu_pool}-nCruise{n_cruise_abu_pool}-EABU{E_abu_str}.pdf"
  )

  fig.savefig(out_file, format="pdf")
  plt.close(fig)
