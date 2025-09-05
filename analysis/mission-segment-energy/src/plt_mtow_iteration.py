# plt_mtow_iteration.py

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
