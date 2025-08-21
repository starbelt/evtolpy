# log_power_profile.py

# import Python modules
import csv # csv
import sys # argv

# path to directory containing evtolpy package; use before deploying as package
sys.path.append('../../../evtol')
from aircraft import Aircraft
from mission import Mission

# parse script arguments
if len(sys.argv) == 3:
    cfg = sys.argv[1]
    log = sys.argv[2]
    if log[-1] != '/':
        log += '/'
else:
    print(
        'Usage: ' \
        'python3 log_reserve_power_profile.py '
        '/path/to/cfg.json /path/to/log/'
    )
    exit()

# create aircraft object 
aircraft = Aircraft(cfg)

# create mission object -
mission = Mission(cfg)

mission_segment_durations = [
    mission.reserve_hover_climb_s,
    mission.reserve_trans_climb_s,
    mission.reserve_accel_climb_s,
    mission.reserve_cruise_s,
    mission.reserve_decel_descend_s,
    mission.reserve_trans_descend_s,
    mission.reserve_hover_descend_s,
]

power_values_kw = [
    aircraft.reserve_hover_climb_avg_electric_power_kw,
    aircraft.reserve_trans_climb_avg_electric_power_kw,
    aircraft.reserve_accel_climb_avg_electric_power_kw,
    aircraft.reserve_cruise_avg_electric_power_kw,
    aircraft.reserve_decel_descend_avg_electric_power_kw,
    aircraft.reserve_trans_descend_avg_electric_power_kw,
    aircraft.reserve_hover_descend_avg_electric_power_kw,
]

time_steps = []
avg_power = []
current_time = 0.0

for power_kw, duration_s in zip(power_values_kw, mission_segment_durations):
    for t in range(int(duration_s)):
        time_steps.append(current_time + t)
        avg_power.append(power_kw)
    current_time += duration_s

with open(log + 'reserve-power-profile.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['time', 'avg_electric_power_kw'])
    for t, p in zip(time_steps, avg_power):
        csvwriter.writerow([f'{t:.3f}', f'{p:.6f}'])