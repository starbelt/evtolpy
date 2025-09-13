# plt_mass_breakdown.py

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
        'python3 plt_mass_breakdown.py '
        '/path/to/log.csv /path/to/plt/'
    )
    exit()

# read CSV
labels = []
masses = []
total_empty_mass = None

with open(log_csv, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # skip header
    for row in csvreader:
        if row[0] == "Total Empty Mass":
            total_empty_mass = float(row[1])
        else:
            labels.append(row[0])
            masses.append(float(row[1]))

# generate pie chart
plt.figure(figsize=(10, 10))
plt.pie(masses, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
plt.title(f'Aircraft Component Mass Breakdown\nTotal Empty Mass = {total_empty_mass:.1f} kg')
plt.tight_layout()

# save to PDF
plt.savefig(out_dir + 'mass-breakdown.pdf', format='pdf')
