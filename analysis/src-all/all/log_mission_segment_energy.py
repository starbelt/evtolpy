# log_mission_segment_energy.py
#
# Usage: python3 log_mission_segment_energy.py /path/to/cfg.json /path/to/log/
#  Reads the configuration JSON file and writes the results to the log directory
# Parameters:
#  /path/to/cfg.json: path to configuration JSON file
#  /path/to/log/: destination directory for log files
# Output:
#  Energy needed for each mission segment
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris
#
# See the LICENSE file for the license

# import Python modules
import csv # csv
import sys # argv

# path to directory containing evtolpy package; use before deploying as package
sys.path.append('../../../evtol')
from aircraft import Aircraft

# comment above and uncomment below when ready to deploy as package
#from ... import Aircraft

# "constants"
EPS_S = 1.0e-6 # a microsecond of differentiating mission segment endpoints

# initialize script arguments
cfg = '' # path to configuration JSON file
log = '' # destination directory for log files

# parse script arguments
if len(sys.argv)==3:
  cfg = sys.argv[1]
  log = sys.argv[2]
  if log[-1] != '/':
    log += '/'
else:
  print(\
   'Usage: '\
   'python3 log_mission_segment_energy.py '\
   '/path/to/cfg.json /path/to/log/'\
  )
  exit()

# construct an aircraft object from the specified configuration
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

# collate data
mission_segment_values = [\
 '{:.6f}'.format(aircraft.depart_taxi_energy_kw_hr),
 '{:.6f}'.format(aircraft.hover_climb_energy_kw_hr),
 '{:.6f}'.format(aircraft.trans_climb_energy_kw_hr),
 '{:.6f}'.format(aircraft.depart_proc_energy_kw_hr),
 '{:.6f}'.format(aircraft.accel_climb_energy_kw_hr),
 '{:.6f}'.format(aircraft.cruise_energy_kw_hr),
 '{:.6f}'.format(aircraft.decel_descend_energy_kw_hr),
 '{:.6f}'.format(aircraft.arrive_proc_energy_kw_hr),
 '{:.6f}'.format(aircraft.trans_descend_energy_kw_hr),
 '{:.6f}'.format(aircraft.hover_descend_energy_kw_hr),
 '{:.6f}'.format(aircraft.arrive_taxi_energy_kw_hr),
 '{:.6f}'.format(aircraft.reserve_hover_climb_energy_kw_hr),
 '{:.6f}'.format(aircraft.reserve_trans_climb_energy_kw_hr),
 '{:.6f}'.format(aircraft.reserve_accel_climb_energy_kw_hr),
 '{:.6f}'.format(aircraft.reserve_cruise_energy_kw_hr),
 '{:.6f}'.format(aircraft.reserve_decel_descend_energy_kw_hr),
 '{:.6f}'.format(aircraft.reserve_trans_descend_energy_kw_hr),
 '{:.6f}'.format(aircraft.reserve_hover_descend_energy_kw_hr),
]

# write the mission segment energy values to a CSV file in the log directory
with open(log+'mission-segment-energy.csv', 'w', newline='') as csvfile:
  csvwriter = csv.writer(csvfile)
  csvwriter.writerows([mission_segment_labels,mission_segment_values])
