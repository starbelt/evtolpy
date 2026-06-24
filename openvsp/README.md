# eVTOLpy → OpenVSP geometry integration

This tool reads an `evtolpy` JSON configuration, builds a 3-D
[OpenVSP](https://openvsp.org) model of the aircraft, and runs OpenVSP's
**Geometry Analyses** — the configuration-level geometric compatibility checks
described in R. A. McDonald, *"Configuration Geometry Analyses in OpenVSP,"*
AIAA AVIATION 2026 Forum, AIAA 2026-4357.

The headline check for eVTOL aircraft is the **rotor tip path** clearance: the
disk swept by each rotor is a keep-out zone that must clear the airframe and the
other rotors.

## What it produces

For a given config the tool writes (into `--outdir`, default `out/`):

| File | Contents |
|------|----------|
| `evtol_model.vsp3` | The 3-D OpenVSP model — **open this in the OpenVSP GUI for visualization** |
| `layout_3view.png` | Headless top/side/front 3-view; rotor disks drawn as tip-path circles |
| `geometry_report.json` | All check results (analytic + OpenVSP) |
| `evtol_model_CompGeom.*` | OpenVSP wetted-area/volume output |
| `evtol_model_MassProps.txt` | OpenVSP mass-properties output |

## Checks performed

**Analytic layer** (pure Python, always runs, no OpenVSP needed):
- Rotor tip-path clearance, rotor-to-rotor (exact disk-to-disk gap)
- Rotor tip-path clearance to fuselage
- `d_value_m` consistency vs the actual lateral extent of the turning rotors
- Disk loading

**OpenVSP layer** (requires the OpenVSP Python API, see Setup):
- **Rotor tip path vs airframe** — `ComputeMinClearanceDistance` of each rotor
  actuator disk against the airframe structure set (the validated, reliable path)
- **Airframe self-interference** — Geometry Analysis Manager external
  self-interference case; reports `Con_Val`, a negative-null compound metric
  (`<= 0` ⇒ clear). *Note: intentional wing/empennage-to-fuselage junctions
  register as interference; this metric is most meaningful for booms, gear, and
  rotor packaging.*
- **Wetted area & volume** (`CompGeom`) and **Mass properties** (`MassProp`)

The model also includes the formal **Rotor Tip Path Auxiliary Geometry**
(`AUX_GEOM_ROTOR_TIP_PATH`) on each rotor so the keep-out cones are visible in
the OpenVSP GUI.

## Usage

```bash
# analytic checks + plot only (no OpenVSP needed)
python3 evtolpy_openvsp.py ../Tutorial/Archer_Midnight.json --analytic-only

# full run: build model + OpenVSP geometry analyses (needs the OpenVSP venv)
~/opt/openvsp/.venv/bin/python evtolpy_openvsp.py \
    ../Tutorial/Archer_Midnight.json --outdir out_archer
```

Options: `--arch {auto,tiltrotor,lift_cruise,multirotor,fixed_wing}` (default
auto-detected from rotor counts), `--aircraft <key>` (force a named layout
regardless of filename — useful for parameter sweeps that write temp files),
`--analytic-only`, `--no-plot`, `--screenshot` (OpenVSP PNG; needs the GUI),
`--no-size` (see below).

### Sizing first

By default the tool runs eVTOLpy's MTOW sizing iteration
(`Aircraft.iterate_mtow`) before building geometry. The loop converges
`empty + payload + battery -> MTOW`, and since MTOW drives the wing area (stall
equation) it changes the built geometry. Both the input and sized MTOM are
printed and recorded in the report, e.g. `MTOM 1850 -> 2108 kg (sized)`. This
matters for sweeps: change a driver (rotor diameter, mission, battery, ...) and
the vehicle re-sizes before it is drawn.

Pass `--no-size` to skip the iteration and build from the JSON's
`max_takeoff_mass_kg` as-is — use this for partial JSONs (the iteration needs
the propulsion/power/mission/environ sections) or when you specifically want the
unsized design point. If the iteration diverges (it raises for physically
self-inconsistent configs) the tool warns and falls back to the input MTOM.

### Geometric fidelity

What the model reproduces **exactly** from the JSON / eVTOLpy-derived values:

- **Wingspan**, **wing planform area** (the root chord is back-computed from
  area+span+taper, so the trapezoid area equals `wing_area_m2`), and **taper**.
- **Wing thickness-to-chord** — the airfoil `ThickChord` is set to `wing_t_p_c`.
- **Horizontal & vertical tail areas**, and — because the tails are placed at a
  wing-AC-to-tail-AC arm of exactly `0.5*fuselage_l` — the **geometric tail
  volume coefficients match `horiz_tail_vol_coeff` / `vert_tail_vol_coeff`**.
- **Fuselage length/width/height**, **rotor diameter**, and **rotor counts**.

What is **assumed** (the JSON does not constrain it):

- All component **positions**. The tail is anchored near the fuselage tail and
  the wing placed the exact arm forward of it; rotors/booms are synthesized per
  architecture (lift+cruise: fore/aft rotors on booms; tiltrotor: packed from
  the tip; multirotor: a ring). The JSON has no coordinates.
- **Tail span/aspect ratio and taper** (only the areas are constrained), wing
  **dihedral/twist** (0) and **sweep** (wing 0; tails OpenVSP default), the
  **airfoil family**, and the **fuselage cross-section shape**.

Edit `build_layout()` / `_place_rotors()` to match a specific aircraft. A
`[FAIL]` on rotor-to-rotor clearance means the rotors don't fit at that
span/diameter in this layout — itself a useful configuration signal.

### Generic builders vs. per-aircraft layouts (and what the keys are)

There are two ways a layout gets built:

1. **Generic per-class builders** (the default). Each architecture —
   `lift_cruise`, `tiltrotor`, `multirotor`, `fixed_wing` — has a parametric
   builder that reads the JSON (wingspan, rotor diameter, chord, **rotor
   counts**, ...) and adapts the wing, booms, and rotors accordingly. Change the
   *dimensions* and the model follows: a bigger span spreads the booms, a bigger
   rotor grows the disks, more lift rotors add more booms. This is what
   `Archer_Midnight` and `NASA_LC` use — they have **no** special-case code.

2. **Per-aircraft layouts** (`_AIRCRAFT_LAYOUTS` / `_ARCH_OVERRIDE`, keyed on the
   config filename stem). These exist **only** for aircraft whose rotor
   *arrangement* the generic builder cannot reproduce:

   | Key | Why it needs custom code |
   |---|---|
   | `joby_s4` | rotors on a **V-tail** + swept wing inboard/tip rotors |
   | `nasa_tr` | **tandem wings** (4 front-wing + 2 rear-wing rotors) |
   | `wisk` | JSON counts misclassify it (reclassified to `lift_cruise`) and it needs a tail **pusher** not in the JSON |

**The keys are per-aircraft, not per-architecture.** So to build, say, a
lift+tilt distributed design *like* Archer but with very different wings or
rotor sizes, you do **not** use a key — the generic `lift_cruise` builder
already adapts to your numbers (auto-detected from the rotor counts, or force it
with `--arch lift_cruise`). You only write a new `_layout_*()` function and
register a key when your **geometry/arrangement** departs from the class pattern
(rotors on a V-tail, a canard, an unusual spanwise distribution, ...). Different
*dimensions* alone never need one.

A `[FAIL]` on rotor-to-rotor clearance from the generic builder means the rotors
don't fit at that span/diameter — grow the span (or shrink the rotors), exactly
as `rotor_diameter_trade_study.py` does.

## Setup: installing the OpenVSP Python API

There is **no `pip install openvsp`** package. The API ships as Python wheels
bundled inside each OpenVSP release, built for specific Python versions. This
machine was set up as follows (macOS arm64; the OpenVSP arm64 build requires
Python 3.11 or 3.13, not the system 3.9):

```bash
# 1. Get a matching Python (uv is self-contained, no sudo)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.11
uv venv --python 3.11 ~/opt/openvsp/.venv

# 2. Download the matching OpenVSP build (arm64 + Python 3.11)
#    from https://openvsp.org/download.php  (3.50.5 used here)
#    e.g. OpenVSP-3.50.5-macos-14-ARM64-Python3.11.zip  (~137 MB)
cd ~/opt/openvsp && unzip OpenVSP-3.50.5-macos-14-ARM64-Python3.11.zip -d extracted

# 3. Install the bundled Python packages into the venv
cd extracted/OpenVSP-3.50.5-MacOS/python
uv pip install --python ~/opt/openvsp/.venv/bin/python -r requirements.txt

# 4. Verify (run from outside the package dir to avoid name shadowing)
cd /tmp && ~/opt/openvsp/.venv/bin/python -c \
  "import openvsp as vsp; print(vsp.GetVSPVersion())"
```

The Geometry Analysis Manager API (`AddGeometryAnalysis`,
`EXTERNAL_INTERFERENCE`, `AUX_GEOM_ROTOR_TIP_PATH`, `ComputeMinClearanceDistance`)
is confirmed present in **OpenVSP 3.50.5**.

> Implementation note: in 3.50.5 the thin auxiliary tip-path cones mesh
> inconsistently, so rotor tip-path clearance is computed from the rotor
> **actuator disks** (`PROP_DISK` mode), which represent the same swept surface
> and mesh reliably. Rotor-to-rotor clearance uses the exact analytic disk math
> because coplanar-disk clearance in OpenVSP is degenerate. The OpenVSP and
> analytic tip-path-vs-airframe numbers agree (e.g. 0.83 m vs 0.82 m on Archer
> Midnight), cross-validating both.
