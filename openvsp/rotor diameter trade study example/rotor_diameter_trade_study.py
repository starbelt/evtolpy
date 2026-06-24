# rotor_diameter_trade_study.py
#
# Rotor-diameter trade study for the Archer Midnight, built on the eVTOLpy ->
# OpenVSP pipeline. For each rotor diameter in the sweep it:
#   1. sizes the vehicle (eVTOLpy MTOW iteration),
#   2. builds the OpenVSP model and writes a .vsp3,
#   3. runs the geometry checks,
# and then produces trade-study figures (metric curves + a layout montage)
# showing how the vehicle changes across the sweep.
#
# Usage (with the OpenVSP venv Python):
#   python3 rotor_diameter_trade_study.py
#
# Output folder: "rotor diameter trade study/" at the repo root.

import copy
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
for _p in (_REPO, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from evtol.aircraft import Aircraft                       # noqa: E402
import evtolpy_openvsp as E                               # noqa: E402

BASE_CONFIG = os.path.join(_REPO, "Tutorial", "Archer_Midnight.json")
OUT_DIR = os.path.join(_REPO, "rotor diameter trade study")
SWEEP = [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]   # rotor diameter [m]
AIRCRAFT_KEY = "archer_midnight"


def _draw_topview(ax, lay, title):
    """Minimal plan-view of a layout: fuselage, wing, booms, rotor disks."""
    fl, fw = lay.fuselage_l_m, lay.fuselage_w_m
    color = {"z": "#1f77b4", "tilt": "#2ca02c", "x": "#d62728"}
    ax.add_patch(Rectangle((0, -fw / 2), fl, fw, fc="#dddddd", ec="k", lw=0.6))
    ax.add_patch(Rectangle((lay.wing_x_m, -lay.wing_span_m / 2),
                           lay.wing_root_chord_m, lay.wing_span_m,
                           fc="#aac4e0", ec="k", lw=0.6, alpha=0.7))
    for b in lay.booms:
        ax.add_patch(Rectangle((b.x_start_m, b.y_m - b.diameter_m / 2),
                               b.x_end_m - b.x_start_m, b.diameter_m,
                               fc="#888888", ec="k", lw=0.4))
    for r in lay.rotors:
        c = color.get(r.axis, "#1f77b4")
        if r.axis == "x":
            ax.plot([r.x_m, r.x_m], [r.y_m - r.diameter_m / 2,
                                     r.y_m + r.diameter_m / 2], color=c, lw=1.3)
        else:
            ax.add_patch(Circle((r.x_m, r.y_m), r.diameter_m / 2,
                                fill=False, ec=c, lw=1.2))
    # Patches do not auto-expand the view; set limits from the geometry extent.
    xs = [0.0, fl, lay.wing_x_m + lay.wing_root_chord_m]
    ys = [-fw / 2, fw / 2, -lay.wing_span_m / 2, lay.wing_span_m / 2]
    for r in lay.rotors:
        xs += [r.x_m - r.diameter_m / 2, r.x_m + r.diameter_m / 2]
        ys += [r.y_m - r.diameter_m / 2, r.y_m + r.diameter_m / 2]
    mx = 0.5
    ax.set_xlim(min(xs) - mx, max(xs) + mx)
    ax.set_ylim(min(ys) - mx, max(ys) + mx)
    ax.set_title(title, fontsize=10)
    ax.set_aspect("equal", "box")
    ax.grid(True, alpha=0.25)
    ax.set_xlabel("X [m]", fontsize=8)
    ax.set_ylabel("Y [m]", fontsize=8)
    ax.tick_params(labelsize=7)


def rotors_in_a_row(lay):
    """Number of lift rotors sharing a spanwise row (the fore or aft line) --
    i.e. how many rotors the wingspan must accommodate side-by-side."""
    from collections import Counter
    xs = Counter(round(r.x_m, 1) for r in lay.rotors if r.axis in ("z", "tilt"))
    return max(xs.values()) if xs else 1


def run_point(diameter_m, wingspan_m, vsp):
    """Size + build one sweep point. Returns (metrics dict, layout)."""
    name = f"archer_{diameter_m:g}m"          # e.g. archer_3m, archer_1.75m
    point_dir = os.path.join(OUT_DIR, name)
    os.makedirs(point_dir, exist_ok=True)

    # Write the modified config so each point records its own input.
    cfg = copy.deepcopy(json.load(open(BASE_CONFIG)))
    cfg["propulsion"]["rotor_diameter_m"] = diameter_m
    cfg["aircraft"]["wingspan_m"] = wingspan_m   # grow span with the rotors
    cfg["aircraft"]["d_value_m"] = wingspan_m
    cfg_path = os.path.join(point_dir, "config.json")
    json.dump(cfg, open(cfg_path, "w"), indent=2)

    ac = Aircraft(cfg_path)
    mtom_in = ac.max_takeoff_mass_kg
    try:
        mtom_sized, _ = ac.iterate_mtow
    except Exception as e:
        mtom_sized = ac.max_takeoff_mass_kg
        print(f"  D={diameter_m}: sizing did not converge ({e.__class__.__name__})")

    lay = E.build_layout(ac, E.detect_arch(ac), AIRCRAFT_KEY)
    an = E.analytic_checks(ac, lay)

    m = {
        "rotor_diameter_m": diameter_m,
        "wingspan_m": wingspan_m,
        "mtom_input_kg": mtom_in,
        "mtom_sized_kg": mtom_sized,
        "wing_area_m2": ac.wing_area_m2,
        "wing_root_chord_m": ac.wing_root_chord_m,
        "disk_loading_kg_p_m2": ac.disk_loading_kg_p_m2,
        "rotor_rotor_gap_m": an["rotor_tip_path_rotor_to_rotor"]["min_gap_m"],
        "rotor_rotor_pass": an["rotor_tip_path_rotor_to_rotor"]["pass"],
    }

    # OpenVSP model + geometry checks
    ids = E.build_openvsp_model(vsp, ac, lay)
    vsp3 = os.path.join(point_dir, f"{name}.vsp3")
    vsp.WriteVSPFile(vsp3, vsp.SET_ALL)
    ga = E.run_geometry_analyses(vsp, ids, point_dir)
    tp = ga.get("rotor_tip_path_vs_airframe", {})
    wa = ga.get("wetted_area_volume", {})
    m["tippath_vs_airframe_m"] = tp.get("min_clearance_m")
    m["wetted_area_m2"] = (wa.get("Total_Wet_Area") or [None])[0]
    m["wetted_vol_m3"] = (wa.get("Total_Wet_Vol") or [None])[0]

    # Per-point 3-view
    E.plot_layout(lay, ac, os.path.join(point_dir, "layout_3view.png"))

    json.dump({"metrics": m}, open(os.path.join(point_dir, "report.json"), "w"),
              indent=2)
    return m, lay


def make_trade_curves(rows, path):
    D = [r["rotor_diameter_m"] for r in rows]
    panels = [
        ("wingspan_m", "Wingspan [m]", None),
        ("mtom_sized_kg", "Sized MTOM [kg]", None),
        ("wing_area_m2", "Wing area [m$^2$]", None),
        ("disk_loading_kg_p_m2", "Disk loading [kg/m$^2$]", None),
        ("rotor_rotor_gap_m", "Rotor-rotor tip gap [m]", 0.0),
        ("tippath_vs_airframe_m", "Tip-path vs airframe [m]", 0.0),
        ("wetted_area_m2", "Wetted area [m$^2$]", None),
        ("wing_root_chord_m", "Wing root chord [m]", None),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(19, 8))
    for ax, (key, ylabel, zero) in zip(axes.ravel(), panels):
        y = [r.get(key) for r in rows]
        ax.plot(D, y, "o-", color="#1f55a0")
        if zero is not None:
            ax.axhline(zero, color="r", ls="--", lw=1, alpha=0.7)
            for xi, yi in zip(D, y):
                if yi is not None:
                    ax.plot(xi, yi, "o",
                            color="#2ca02c" if yi > zero else "#d62728")
        ax.set_xlabel("Rotor diameter [m]")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
    fig.suptitle("Archer Midnight — rotor diameter trade study", fontsize=14)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def make_montage(layouts, path):
    n = len(layouts)
    fig, axes = plt.subplots(1, n, figsize=(3.0 * n, 3.6))
    if n == 1:
        axes = [axes]
    for ax, (D, lay) in zip(axes, layouts):
        _draw_topview(ax, lay, f"D = {D:.2f} m")
    fig.suptitle("Archer Midnight planform vs rotor diameter "
                 "(disks = rotor tip paths)", fontsize=13)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    import openvsp as vsp

    # Baseline: rotors-in-a-row (n) and the reference diameter / span. The span
    # then grows as wingspan = base_span + n*(D - D_base) to hold the rotor
    # spacing roughly constant as the rotors grow.
    base = json.load(open(BASE_CONFIG))
    d_base = base["propulsion"]["rotor_diameter_m"]
    span_base = base["aircraft"]["wingspan_m"]
    base_ac = Aircraft(BASE_CONFIG)
    n_row = rotors_in_a_row(E.build_layout(base_ac, E.detect_arch(base_ac),
                                           AIRCRAFT_KEY))
    print(f"Coupling: n (rotors in a row) = {n_row};  "
          f"wingspan = {span_base:.2f} + {n_row}*(D - {d_base:.2f})\n")

    rows, layouts = [], []
    for D in SWEEP:
        span = span_base + n_row * (D - d_base)
        print(f"Rotor diameter {D:.2f} m  ->  wingspan {span:.2f} m ...")
        m, lay = run_point(D, span, vsp)
        rows.append(m)
        layouts.append((D, lay))
        print(f"  MTOM={m['mtom_sized_kg']:.0f} kg  wing_area={m['wing_area_m2']:.2f}  "
              f"rotor-rotor={m['rotor_rotor_gap_m']:+.2f} m  "
              f"disk_loading={m['disk_loading_kg_p_m2']:.1f}")

    # Figures
    make_trade_curves(rows, os.path.join(OUT_DIR, "trade_curves.png"))
    make_montage(layouts, os.path.join(OUT_DIR, "layout_montage.png"))

    # Summary CSV
    with open(os.path.join(OUT_DIR, "summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nTrade study written to: {OUT_DIR}")
    print("  trade_curves.png, layout_montage.png, summary.csv")
    print("  per point: archer_<D>m/archer_<D>m.vsp3 (+ config.json, "
          "layout_3view.png, report.json)")


if __name__ == "__main__":
    main()
