# plt_power_all.py
#
# Usage: python3 plt_power_all.py /path/to/log.csv /path/to/plt/
#  Reads the log CSV file and saves the plot to the plt directory
#  Ensure that the Python virtual environment (venv) is enabled after running
#  setup_dependencies.sh: source p3-env/bin/activate
# Parameters:
#  /path/to/log.csv: path to log CSV file
#  /path/to/plt/: destination directory for plot files
# Output:
#  Plot for average electric power needed for each mission segment
#
# Written by First Last
# Other contributors: 
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
   'python3 plt_power_all.py '\
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
plt.figure(figsize=(15, 6))
x_values = lines[0]
y_values = [float(e) for e in lines[1]]
plt.bar(x_values, y_values)
plt.title('Mission Segment Average Power')
plt.xlabel('Mission Segment')
plt.ylabel('Average Power (kW)')

# add energy values on top of each bar
for i in range(len(x_values)):
    plt.text(i, y_values[i], f'{y_values[i]:.4f}', ha='center', va='bottom')

# rotate x-axis labels for readability
plt.xticks(rotation=45, ha='right')
# add more space at the bottom to prevent labels from being cut off
plt.tight_layout()

# save to PDF
plt.savefig(out+'power-all.pdf', format='pdf')
