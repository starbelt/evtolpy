"""Minimal example: size the Archer Midnight, then build its OpenVSP model.

This is the smallest end-to-end use of the eVTOLpy -> OpenVSP pipeline.

Run with the OpenVSP venv Python, e.g.:
    ~/opt/openvsp/.venv/bin/python openvsp/example_size_and_build.py
"""

import os
import sys

# Make the evtol package and this tool importable regardless of where it's run.
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
for p in (REPO, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import openvsp as vsp                         # OpenVSP Python API
from evtol.aircraft import Aircraft           # eVTOLpy design model
import evtolpy_openvsp as E                   # the OpenVSP integration

CONFIG = os.path.join(REPO, "Tutorial", "Archer_Midnight.json")
OUTDIR = os.path.join(HERE, "out_example")
os.makedirs(OUTDIR, exist_ok=True)

# 1. Load the eVTOLpy design.
ac = Aircraft(CONFIG)

# 2. Size it: eVTOLpy iterates empty + payload + battery -> MTOW until it
#    converges. This updates max_takeoff_mass_kg, which drives the wing area.
mtom_input = ac.max_takeoff_mass_kg
mtom_sized, _history = ac.iterate_mtow
print(f"MTOM: {mtom_input:.0f} kg (input) -> {mtom_sized:.0f} kg (sized)")
print(f"Wing area {ac.wing_area_m2:.2f} m^2, root chord {ac.wing_root_chord_m:.2f} m")

# 3. Build the layout (component positions) and the 3-D OpenVSP model.
arch = E.detect_arch(ac)
lay = E.build_layout(ac, arch, key="archer_midnight") 
ids = E.build_openvsp_model(vsp, ac, lay)

# 4. Save the OpenVSP model.
vsp3 = os.path.join(OUTDIR, "archer_midnight.vsp3")
vsp.WriteVSPFile(vsp3, vsp.SET_ALL)
print(f"Saved OpenVSP model: {vsp3}")

# 5. (Optional) run the geometry checks and print the headline result.
checks = E.run_geometry_analyses(vsp, ids, OUTDIR)
tp = checks["rotor_tip_path_vs_airframe"]
print(f"Rotor tip-path vs airframe: {tp['min_clearance_m']} m "
      f"[{'PASS' if tp['pass'] else 'FAIL'}]")
