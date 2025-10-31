# plt_mission_segment_abu_analysis_flight_extension.py
#
# Usage: python3 plt_mission_segment_abu_analysis_flight_extension.py /path/to/log.csv /path/to/plt/
#  Reads the log CSV file and saves the plot to the plt directory
#  Ensure that the Python virtual environment (venv) is enabled after running
#  setup_dependencies.sh: source p3-env/bin/activate
# Parameters:
#  /path/to/log.csv: path to log CSV file
#  /path/to/plt/: destination directory for plot files
# Output:
#  Plots for ABU mission benefits: range, time, and baseline energy saved
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import csv                       # csv
import matplotlib.pyplot as plt  # matplotlib
import sys                       # argv
import os                        # path 

# initialize script arguments
log = '' # path to log CSV file
out = '' # destination directory for plot files

# parse script arguments
if len(sys.argv)==3:
  log = sys.argv[1]
  out = sys.argv[2]
  if out[-1] != '/':
    out += '/'
else:
  print(\
   'Usage: '\
   'python3 plt_mission_segment_abu_analysis_flight_extension.py '\
   '/path/to/log.csv /path/to/plt/'\
  )
  exit()

# read the log CSV file
lines = []
with open(log, mode='r') as csvfile:
  csvreader = csv.reader(csvfile)
  for line in csvreader:
    lines.append(line)

# extract headers and data
headers = lines[0]
data = lines[1:]

# helper to safely convert to float
def safe_float(x):
  try:
    return float(x)
  except:
    return None

# build columns
columns = {h: [] for h in headers}
for row in data:
  for h, v in zip(headers, row):
    columns[h].append(v.strip())

# convert relevant fields
E_abu_mission_kwh  = [safe_float(e) for e in columns.get("E_abu_mission_kwh", [])]
extra_range_mi     = [safe_float(e) for e in columns.get("extra_range_mi", [])]
extra_time_s       = [safe_float(e) for e in columns.get("extra_time_s", [])]
E_saved_kwh        = [safe_float(e) for e in columns.get("E_saved_kwh", [])]

# helper for consistent line plot
def make_line_plot(x, y, xlabel, ylabel, title, filename, y_scale=1.0, value_format='{:.2f}'):
  # filter valid points
  valid = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
  if len(valid) == 0:
    print(f"No valid data for {filename}")
    return

  # sort by x for clean line
  valid.sort(key=lambda t: t[0])
  x_vals, y_vals = zip(*valid)
  y_vals = [yy / y_scale for yy in y_vals]

  # create plot
  plt.figure(figsize=(8, 6))
  plt.plot(x_vals, y_vals, '-o', linewidth=1.5, markersize=5)
  plt.title(title)
  plt.xlabel(xlabel)
  plt.ylabel(ylabel)
  plt.grid(True, linestyle='--', alpha=0.6)

  # add point labels
  for i, (xx, yy) in enumerate(zip(x_vals, y_vals)):
    plt.text(xx, yy, value_format.format(yy), ha='center', va='bottom', fontsize=8)

  plt.tight_layout()
  plt.savefig(os.path.join(out, filename), format='pdf')
  plt.close()

# plot 1 (combined): Extended Range and Flight Time vs. ABU Energy (time/distance powered by ABU)
valid_combined = [(a, b, c) for a, b, c in zip(E_abu_mission_kwh, extra_range_mi, extra_time_s)
                  if a is not None and b is not None and c is not None]

if len(valid_combined) > 0:
  valid_combined.sort(key=lambda t: t[0])
  x_vals, range_vals, time_vals = zip(*valid_combined)
  time_vals_min = [t / 60.0 for t in time_vals]

  fig, ax1 = plt.subplots(figsize=(8, 6))
  color1 = 'tab:blue'
  color2 = 'tab:red'

  ax1.plot(x_vals, range_vals, '-o', color=color1, linewidth=1.5, markersize=5, label='Distance Powered By ABU')
  ax1.set_xlabel('ABU Mission Energy (kWh)')
  ax1.set_ylabel('Distance Powered By ABU (miles)')
  ax1.tick_params(axis='y')
  ax1.grid(True, linestyle='--', alpha=0.6)

  # add point labels for range
  for xx, yy in zip(x_vals, range_vals):
    ax1.text(xx, yy + 0.3, f'{yy:.2f}', color=color1, ha='center', va='bottom', fontsize=8)

  # second axis for extended flight time
  ax2 = ax1.twinx()
  ax2.plot(x_vals, time_vals_min, '--s', color=color2, linewidth=1.5, markersize=5, label='Flight Time Powered By ABU')
  ax2.set_ylabel('Flight Time Powered By ABU (minutes)')
  ax2.tick_params(axis='y')

  # add point labels for time
  for xx, yy in zip(x_vals, time_vals_min):
    ax2.text(xx, yy - 0.3, f'{yy:.2f}', color=color2, ha='center', va='top', fontsize=8)

  # add combined legend
  lines1, labels1 = ax1.get_legend_handles_labels()
  lines2, labels2 = ax2.get_legend_handles_labels()
  ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9, frameon=True)

  plt.title('Flight Time And Distance Powered By ABU vs. ABU Mission Energy')
  fig.tight_layout()
  plt.savefig(os.path.join(out, 'flight_extension_range_time_combined.pdf'), format='pdf')
  plt.close()

# # plot 2: Extended Range vs. ABU Energy 
# make_line_plot(
#   x=E_abu_mission_kwh,
#   y=extra_range_mi,
#   xlabel='ABU Mission Energy (kWh)',
#   ylabel='Extended Range (miles)',
#   title='Extended Flight Range vs. ABU Mission Energy',
#   filename='flight_extension_range_vs_abu_energy.pdf'
# )

# # plot 3: Extra Flight Time vs. ABU Energy 
# make_line_plot(
#   x=E_abu_mission_kwh,
#   y=extra_time_s,
#   xlabel='ABU Mission Energy (kWh)',
#   ylabel='Extra Flight Time (minutes)',
#   title='Extra Flight Time vs. ABU Mission Energy',
#   filename='flight_extension_time_vs_abu_energy.pdf',
#   y_scale=60.0
# )

# # plot 4: Baseline Energy Saved vs. ABU Energy
# make_line_plot(
#   x=E_abu_mission_kwh,
#   y=E_saved_kwh,
#   xlabel='ABU Mission Energy (kWh)',
#   ylabel='Baseline Energy Saved (kWh)',
#   title='Baseline Energy Saved vs. ABU Mission Energy',
#   filename='baseline_saved_vs_abu_energy.pdf'
# )
