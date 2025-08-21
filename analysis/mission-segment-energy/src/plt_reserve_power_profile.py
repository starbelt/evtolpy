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
        'python3 plt_reserve_power_profile.py '\
        '/path/to/log.csv /path/to/plt/'\
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

# segment labels
segment_labels = [
    'Reserve Hover Climb', 
    'Reserve Transition Climb', 
    'Reserve Accelerate Climb',
    'Reserve Cruise', 
    'Reserve Decelerate Descend', 
    'Reserve Transition Descend', 
    'Reserve Hover Descend'
]

# approximate segment boundaries using the time vector
segment_boundaries = [0]
for i in range(1, len(time)):
    if power[i] != power[i-1]:
        segment_boundaries.append(i)
segment_boundaries.append(len(time))  # add end

# place labels at the middle of each segment
for i in range(len(segment_labels)):
    start_idx = segment_boundaries[i]
    end_idx = segment_boundaries[i+1]
    mid_time = (time[start_idx] + time[end_idx-1]) / 2
    mid_power = max(power[start_idx:end_idx]) + 5  # slightly above the segment
    plt.text(mid_time, mid_power, segment_labels[i], ha='center', va='bottom', rotation=0, fontsize=8)

# save to PDF
plt.savefig(out_dir + 'reserve-power-profile.pdf', format='pdf')
