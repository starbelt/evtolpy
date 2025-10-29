# plt_mtow_iteration.py
#
# Usage: python3 plt_mtow_iteration.py /path/to/log.csv /path/to/plt/
#  Reads the log CSV file and saves the plot to the plt directory
#  Ensure that the Python virtual environment (venv) is enabled after running
#  setup_dependencies.sh: source p3-env/bin/activate
# Parameters:
#  /path/to/log.csv: path to log CSV file
#  /path/to/plt/: destination directory for plot files
# Output:
#  Plot for Maximum Takeoff Weight (MTOW) iteration
#
# Written by First Last
# Other contributors: Khoa Nguyen
#
# See the LICENSE file for the license

# import Python modules
import csv
import matplotlib.pyplot as plt
import sys
import os

if len(sys.argv) == 3:
    log_csv = sys.argv[1]
    out_dir = sys.argv[2]
    if out_dir[-1] != '/':
        out_dir += '/'
else:
    print("Usage: python3 plt_mtow_iteration.py /path/to/mtow-iteration.csv /path/to/plt/")
    exit()

# read log
iteration = []
mtow_guess = []
new_mtow = []
delta = []

with open(log_csv, "r") as csvfile:
    csvreader = csv.reader(csvfile)
    header = next(csvreader)  # skip header
    for row in csvreader:
        iteration.append(int(row[0]))
        mtow_guess.append(float(row[1]))
        new_mtow.append(float(row[2]))
        delta.append(float(row[3]))

# plot MTOW convergence
plt.figure(figsize=(10, 6))
plt.plot(iteration, mtow_guess, "o-", label="MTOW Guess (kg)")
plt.plot(iteration, new_mtow, "s-", label="New MTOW (kg)")
plt.xlabel("Iteration")
plt.ylabel("MTOW (kg)")
plt.title("MTOW Iteration Convergence")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(out_dir + "mtow-iteration-convergence.pdf", format="pdf")

# plot delta (error)
plt.figure(figsize=(10, 6))
plt.plot(iteration, delta, "x-", label="Δ MTOW (kg)")
plt.axhline(0, color="black", linestyle="--")
plt.xlabel("Iteration")
plt.ylabel("Difference (kg)")
plt.title("MTOW Iteration Error")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(out_dir + "mtow-iteration-error.pdf", format="pdf")
