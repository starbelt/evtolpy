# plt_power_profile.py

import csv
import matplotlib.pyplot as plt
import sys

# parse script arguments
if len(sys.argv) == 3:
    log_csv = sys.argv[1]
    out_dir = sys.argv[2]
    if out_dir[-1] != '/':
        out_dir += '/'
else:
    print(
        'Usage: ' \
        'python3 plt_power_profile.py '
        '/path/to/log.csv /path/to/plt/'
    )
    exit()

# read the log CSV file
time = []
power = []
with open(log_csv, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # skip header
    for row in csvreader:
        time.append(float(row[0]))
        power.append(float(row[1]))

# generate plot
plt.figure(figsize=(12, 6))
plt.step(time, power, where='post', color='b')  # stepwise line per segment
plt.title('Power Profile')
plt.xlabel('Flight Time (s)')
plt.ylabel('Average Electric Power (kW)')
plt.grid(True)
plt.tight_layout()

# save to PDF
plt.savefig(out_dir + 'power-profile.pdf', format='pdf')
