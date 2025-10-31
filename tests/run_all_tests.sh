#!/bin/bash
#
# run_all_tests.sh
# A bash script to run all unit tests
#
# Usage: ./run_all_tests.sh
#  - Must execute from the evtolpy/tests directory
# Prerequisites:
#  - sudo apt install python3-pip
#  - sudo apt install python3-venv
# Arguments:
#  - None
# Outputs:
#  - Unit test results
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

python3 test_environ.py
python3 test_mission.py
python3 test_power.py
python3 test_propulsion.py
python3 test_aircraft.py
