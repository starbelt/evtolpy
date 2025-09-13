# log_mass_breakdown.py

import csv
import sys

# path to directory containing evtolpy package
sys.path.append('../../../evtol')
from aircraft import Aircraft

# parse script arguments
if len(sys.argv) == 3:
    cfg = sys.argv[1]
    log = sys.argv[2]
    if log[-1] != '/':
        log += '/'
else:
    print(
        'Usage: '
        'python3 log_mass_breakdown.py '
        '/path/to/cfg.json /path/to/log/'
    )
    exit()

# create aircraft object
aircraft = Aircraft(cfg)

# collect mass components
mass_data = {
    "Wing": aircraft.wing_mass_kg,
    "Horizontal Tail": aircraft.horiz_tail_mass_kg,
    "Vertical Tail": aircraft.vert_tail_mass_kg,
    "Fuselage": aircraft.fuselage_mass_kg,
    "Boom": aircraft.boom_mass_kg,
    "Landing Gear": aircraft.landing_gear_mass_kg,
    "EPU": aircraft.epu_mass_kg,
    "Lift Rotor + Hub": aircraft.lift_rotor_hub_mass_kg,
    "Tilt Rotor": aircraft.tilt_rotor_mass_kg,
    "Actuators": aircraft.actuator_mass_kg,
    "Furnishings": aircraft.furnishings_mass_kg,
    "ECS": aircraft.environmental_control_system_mass_kg,
    "Avionics": aircraft.avionics_mass_kg,
    "High-Volt Power Dist.": aircraft.hivolt_power_dist_mass_kg,
    "Low-Volt Power & Comms": aircraft.lovolt_power_coms_mass_kg,
}

# calculate total empty mass
total_empty_mass = aircraft.empty_mass_kg

# write to CSV
with open(log + 'mass-breakdown.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['Component', 'Mass_kg'])
    for name, mass in mass_data.items():
        csvwriter.writerow([name, f'{mass:.3f}'])
    csvwriter.writerow(['Total Empty Mass', f'{total_empty_mass:.3f}'])
