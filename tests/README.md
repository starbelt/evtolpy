# eVTOLpy Unit Tests

This directory contains unit tests for the core `evtol` package.

The tests use Python's built-in `unittest` framework so the repository does not
need an additional test dependency.

## Directory Contents

- [`data/test-all.json`](data/test-all.json): frozen JSON fixture used by the unit tests
- [`helpers.py`](helpers.py): shared paths and constructors for test fixtures
- [`test_aircraft.py`](test_aircraft.py): aircraft JSON loading, subsystem construction, and setters
- [`test_aircraft_aero.py`](test_aircraft_aero.py): aerodynamic coefficient and drag buildup calculations
- [`test_aircraft_battery.py`](test_aircraft_battery.py): battery charge-time estimator behavior
- [`test_aircraft_geometry.py`](test_aircraft_geometry.py): wing, tail, fuselage, and derived geometry calculations
- [`test_aircraft_iteration.py`](test_aircraft_iteration.py): MTOW iteration convergence and invalid-input behavior
- [`test_aircraft_mass.py`](test_aircraft_mass.py): payload, battery, EPU, landing gear, and empty-mass calculations
- [`test_aircraft_performance.py`](test_aircraft_performance.py): power and energy calculations for mission segments
- [`test_aircraft_propulsion.py`](test_aircraft_propulsion.py): disk loading, over-torque, rotor solidity, and pusher rotor calculations
- [`test_environ.py`](test_environ.py): environment JSON loading and equality checks
- [`test_mission.py`](test_mission.py): mission JSON loading and equality checks
- [`test_power.py`](test_power.py): power JSON loading and battery-energy calculations
- [`test_propulsion.py`](test_propulsion.py): propulsion JSON loading and disk-area updates
- [`README.md`](README.md): This document

Many tests use expected numeric values computed from `data/test-all.json` and the
current equations in `evtol/`. These values act as regression checks: if a
formula or fixture input changes, the test failure shows which output changed.

## Run

From the repository root:

```
python -m unittest discover -s tests -p "test_*.py"
```
