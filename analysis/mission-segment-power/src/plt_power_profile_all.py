# plt_power_profile_all.py

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
        'Usage: '
        'python3 plt_power_profile_all.py '
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

# segment labels
segment_labels = [
    'Depart Taxi',
    'Hover Climb',
    'Transition Climb',
    'Depart Procedures',
    'Accelerate Climb',
    'Cruise',
    'Decelerate Descend',
    'Arrive Procedures',
    'Transition Descend',
    'Hover Descend',
    'Arrive Taxi',
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
segment_boundaries.append(len(time))  

# split into two parts
main_segments = segment_labels[:11]
reserve_segments = segment_labels[11:]
split_idx = segment_boundaries[11]   

# plotting 
plt.step(time[:split_idx], power[:split_idx], where='post', color='g', label='Main Mission')
plt.step(time[split_idx-1:], power[split_idx-1:], where='post', color='b', label='Reserve Mission')

# vertical dashed line separator
plt.axvline(x=time[split_idx], color='k', linestyle='--', linewidth=1)

# add labels
for i in range(len(segment_labels)):
    start_idx = segment_boundaries[i]
    end_idx = segment_boundaries[i+1]
    mid_time = (time[start_idx] + time[end_idx-1]) / 2
    mid_power = max(power[start_idx:end_idx]) + 5
    plt.text(
        mid_time, mid_power,
        segment_labels[i],
        ha='center', va='bottom',
        fontsize=8,
        color=('g' if i < 11 else 'b')
    )

# format plot
plt.title('Power Profile')
plt.xlabel('Flight Time (s)')
plt.ylabel('Average Electric Power (kW)')
plt.grid(True)
plt.legend()
plt.tight_layout()

# save to PDF
plt.savefig(out_dir + 'power-profile-all.pdf', format='pdf')
