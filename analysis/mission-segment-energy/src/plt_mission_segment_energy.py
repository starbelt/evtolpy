# plt_mission_segment_energy.py
#
# Usage: python3 plt_mission_segment_energy.py /path/to/log.csv /path/to/plt/
#  Reads the log CSV file and saves the plot to the plt directory
#  Ensure that the Python virtual environment (venv) is enabled after running
#  setup_dependencies.sh: source p3-env/bin/activate
# Parameters:
#  /path/to/log.csv: path to log CSV file
#  /path/to/plt/: destination directory for plot files
# Output:
#  Plot for energy needed for each mission segment
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris
#
# See the LICENSE file for the license

# import Python modules
import csv                      # csv
import matplotlib.pyplot as plt # matplotlib
import sys                      # argv

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
   'python3 plt_mission_segment_energy.py '\
   '/path/to/log.csv /path/to/plt/'\
  )
  exit()

# read the log CSV file
lines = []
with open(log, mode ='r')as csvfile:
  csvreader = csv.reader(csvfile)
  for line in csvreader:
    lines.append(line)

# generate plot
# TODO: fix this
# Fixed: Convert strings to float
# Initial code: plt.bar(lines[0], lines[1])
plt.bar(lines[0], [float(e) for e in lines[1]])
plt.title('Mission Segment Energy')
plt.xlabel('Mission Segment')
plt.ylabel('Energy (kW hr)')

# Rotate x-axis labels for readability
plt.xticks(rotation=45, ha='right')

# Add more space at the bottom to prevent labels from being cut off
plt.tight_layout()

# save to PDF
plt.savefig(out+'mission-segment-energy.pdf', format='pdf')
