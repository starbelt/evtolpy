# log_power_all.py

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
        'python3 log_power_all.py '
        '/path/to/cfg.json /path/to/log/'
    )
    exit()

# create aircraft object 
aircraft = Aircraft(cfg)

# data labels
mission_segment_labels = [\
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
    aircraft.reserve_hover_climb_avg_electric_power_kw,
    aircraft.reserve_trans_climb_avg_electric_power_kw,
    aircraft.reserve_accel_climb_avg_electric_power_kw,
    aircraft.reserve_cruise_avg_electric_power_kw,
    aircraft.reserve_decel_descend_avg_electric_power_kw,
    aircraft.reserve_trans_descend_avg_electric_power_kw,
    aircraft.reserve_hover_descend_avg_electric_power_kw,
]

# write the mission segment energy values to a CSV file in the log directory
with open(log+'power-all.csv', 'w', newline='') as csvfile:
  csvwriter = csv.writer(csvfile)
  csvwriter.writerows([mission_segment_labels,power_values_kw])
