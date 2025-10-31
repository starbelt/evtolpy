#!/bin/bash
#
# run_mission_segment_energy.sh
# A bash script to log and plot mission segment energy
#
# Usage: ./run_mission_segment_energy.sh
#  - Must execute from the evtolpy/analysis/mission-segment-energy directory
# Prerequisites:
#  - Run setup_dependencies.sh
# Arguments:
#  - None
# Outputs:
#  - mission segment energy logs and plot
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

if [ ! -d "../../p3-env/" ]
then
  echo "It appears that the Python venv module is not set up"
  echo "  Run setup_dependencies.sh first"
  echo "  Exiting"
  exit 1
else
  source ../../p3-env/bin/activate
  python3 log_mission_segment_energy.py ../cfg/test-all.json ../log/
  python3 plt_mission_segment_energy.py ../log/mission-segment-energy.csv ../plt/

  
  deactivate
fi
