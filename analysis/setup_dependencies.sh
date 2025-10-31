#!/bin/bash
#
# setup_dependencies.sh
# A bash script to set up the Python 3 virtual environment
#
# Usage: ./setup_dependencies.sh
#  - Must execute from the evtolpy/analysis/ directory
# Prerequisites:
#  - sudo apt install python3-pip
#  - sudo apt install python3-venv
# Arguments:
#  - None
# Outputs:
#  - Python 3 virtual environment
#
# Written by First Last
# Other contributors: Bradley Denby, Darshan Sarojini, Dylan Hogge, John Riris, Khoa Nguyen
#
# See the LICENSE file for the license

if [ ! -d "./p3-env/" ]
then
  python3 -c "import venv" 1> /dev/null 2> /dev/null
  if [ $? -ne 0 ]
  then
    echo "It appears that the Python venv module is not installed"
    echo "  Try sudo apt install python3-venv"
    echo "  Exiting"
    exit 1
  else
    python3 -m venv p3-env
    source p3-env/bin/activate
    # use pip to list available versions:
    #   python3 -m pip index versions matplotlib
    python3 -m pip install matplotlib==3.10.5
    deactivate
  fi
fi
