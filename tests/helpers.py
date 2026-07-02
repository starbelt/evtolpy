# helpers.py
#
# Shared helpers for eVTOLpy unit tests
#
# Written by First Last
#
# See the LICENSE file for the license

# import Python modules
from pathlib import Path # paths

# import eVTOLpy modules
from evtol.aircraft import Aircraft # aircraft model

# paths
ROOT_DIR = Path(__file__).resolve().parents[1]
TEST_DATA_DIR = ROOT_DIR / 'tests' / 'data'
TEST_ALL_JSON = TEST_DATA_DIR / 'test-all.json'


def make_aircraft():
  return Aircraft(str(TEST_ALL_JSON))
