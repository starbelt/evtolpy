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
        'python3 log_power_profile.py '
        '/path/to/cfg.json /path/to/log/'
    )
    exit()

# create aircraft object 
aircraft = Aircraft(cfg)

# create mission object -
mission = Mission(cfg)

mission_segment_durations = [
    mission.depart_taxi_s,
    mission.hover_climb_s,
    mission.trans_climb_s,
    mission.depart_proc_s,
    mission.accel_climb_s,
    mission.cruise_s,
    mission.decel_descend_s,
    mission.arrive_proc_s,
    mission.trans_descend_s,
    mission.hover_descend_s,
    mission.arrive_taxi_s,
    # 0.0,  # reserve_hover_climb
    # 0.0,  # reserve_trans_climb
    # 0.0,  # reserve_accel_climb
    # 0.0,  # reserve_cruise
    # 0.0,  # reserve_decel_descend
    # 0.0,  # reserve_trans_descend
    # 0.0   # reserve_hover_descend
]

power_values_kw = [
    aircraft.depart_taxi_avg_electric_power_kw,
    aircraft.hover_climb_avg_electric_power_kw,
    aircraft.trans_climb_avg_electric_power_kw,
    aircraft.depart_proc_avg_electric_power_kw,
    aircraft.accel_climb_avg_electric_power_kw,
    aircraft.cruise_avg_electric_power_kw,
    aircraft.decel_descend_avg_electric_power_kw,
    aircraft.arrive_proc_avg_electric_power_kw,
    aircraft.trans_descend_avg_electric_power_kw,
    aircraft.hover_descend_avg_electric_power_kw,
    aircraft.arrive_taxi_avg_electric_power_kw,
    # 0.0,  # reserve_hover_climb
    # 0.0,  # reserve_trans_climb
    # 0.0,  # reserve_accel_climb
    # 0.0,  # reserve_cruise
    # 0.0,  # reserve_decel_descend
    # 0.0,  # reserve_trans_descend
    # 0.0   # reserve_hover_descend
]

time_steps = []
avg_power = []
current_time = 0.0

for power_kw, duration_s in zip(power_values_kw, mission_segment_durations):
    for t in range(int(duration_s)):
        time_steps.append(current_time + t)
        avg_power.append(power_kw)
    current_time += duration_s

with open(log + 'power-profile.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['time', 'avg_electric_power_kw'])
    for t, p in zip(time_steps, avg_power):
        csvwriter.writerow([f'{t:.3f}', f'{p:.6f}'])