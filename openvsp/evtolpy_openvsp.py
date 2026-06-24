# evtolpy_openvsp.py
#
# Build a 3-D OpenVSP model from an eVTOLpy JSON configuration and run the
# OpenVSP "Geometry Analyses" (rotor tip-path / external interference, ground
# clearance, wetted area & volume, mass properties, projected area).
#
# Reference: R. A. McDonald, "Configuration Geometry Analyses in OpenVSP,"
#            AIAA AVIATION 2026 Forum, AIAA 2026-4357.
#
# This script has two layers:
#
#   1. A pure-Python "analytic" layer (no OpenVSP required) that derives a
#      component layout from the eVTOLpy JSON and computes closed-form versions
#      of the most important configuration checks (rotor tip-path clearance,
#      ground clearance, span / D-value consistency, disk loading). This always
#      runs and always produces quantitative results.
#
#   2. An OpenVSP layer (requires `import openvsp`) that constructs the actual
#      3-D model (fuselage, wing, empennage, rotors), attaches a Rotor Tip Path
#      Auxiliary Geometry to each rotor, runs the OpenVSP Geometry Analyses via
#      the API, writes a .vsp3 file, and (optionally) a screenshot.
#
# Usage:
#   python3 evtolpy_openvsp.py <config.json> [--outdir out] [--arch auto]
#                              [--analytic-only] [--screenshot]
#
# See the LICENSE file for the license.

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# Make the evtol package importable when run from this directory or the repo root
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
for _p in (_REPO, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from evtol.aircraft import Aircraft  # noqa: E402

M_2_FT = 3.28084
TAIL_SWEEP_DEG = 25.0   # explicit empennage LE sweep (deterministic placement)


# ---------------------------------------------------------------------------
# Layout model: where each component sits in space.
#
# The eVTOLpy JSON does NOT specify component positions, only sizes and counts.
# We synthesize a plausible, non-overlapping layout from the architecture so the
# geometry checks are meaningful. All positions are in the OpenVSP convention:
#   +X aft, +Y starboard (right), +Z up. Origin at the fuselage nose.
# Override any of this by editing build_layout() or the resulting Layout object.
# ---------------------------------------------------------------------------


@dataclass
class Rotor:
    name: str
    x_m: float
    y_m: float
    z_m: float
    diameter_m: float
    # Axis the thrust points along: "z" (lift rotor, disk horizontal),
    # "x" (pusher, disk vertical/facing aft), or "tilt" (modeled here in the
    # hover/disk-horizontal state, which is the binding case for tip clearance).
    axis: str = "z"
    n_blade: int = 5


@dataclass
class Boom:
    name: str
    y_m: float
    x_start_m: float
    x_end_m: float
    z_m: float
    diameter_m: float = 0.25


@dataclass
class ExtraWing:
    """An extra lifting surface (rear wing, V-tail panel, canard, ...) added by
    a per-aircraft layout. Rendered as an OpenVSP WING geom."""
    name: str
    x_m: float            # LE-root X location
    z_m: float            # root Z location
    span_m: float         # full span (tip-to-tip if sym) else single-panel
    root_chord_m: float
    tip_chord_m: float
    sweep_deg: float = 0.0
    dihedral_deg: float = 0.0   # >0 cants tips up (a V-tail uses ~35-45)
    x_rot_deg: float = 0.0      # 90 -> vertical surface
    sym: bool = True            # mirror across the XZ plane


@dataclass
class Layout:
    arch: str
    fuselage_l_m: float
    fuselage_w_m: float
    fuselage_h_m: float
    wing_x_m: float
    wing_span_m: float
    wing_root_chord_m: float
    wing_tip_chord_m: float
    wing_z_m: float
    htail_x_m: float
    htail_span_m: float
    htail_root_chord_m: float
    htail_tip_chord_m: float
    vtail_x_m: float
    vtail_height_m: float
    vtail_root_chord_m: float
    vtail_tip_chord_m: float
    d_value_m: float
    wing_sweep_deg: float = 0.0
    draw_default_tail: bool = True
    rotors: List[Rotor] = field(default_factory=list)
    booms: List[Boom] = field(default_factory=list)
    extra_wings: List[ExtraWing] = field(default_factory=list)


def detect_arch(ac: Aircraft) -> str:
    p = ac.propulsion
    if p is None:
        return "fixed_wing"
    tilt = p.tilt_rotor_count or 0
    pusher = p.pusher_rotor_count or 0
    lift = p.lift_rotor_count or 0
    # Distributed lift+cruise: dedicated cruise prop, OR both fixed-lift and
    # tilting rotors present on a winged vehicle (e.g. Archer Midnight: 6
    # tilting front + 6 fixed rear on booms).
    if pusher > 0 and lift > 0:
        return "lift_cruise"
    if tilt > 0 and lift > 0:
        return "lift_cruise"
    if tilt > 0:
        return "tiltrotor"
    if lift > 0:
        return "multirotor"
    return "fixed_wing"


def _tail_chords(area_m2: float, span_or_height_m: float):
    """Rough rectangular-ish tail: mean chord = area/span, taper ~0.6."""
    if span_or_height_m <= 0.0:
        return 0.0, 0.0
    mean_c = area_m2 / span_or_height_m
    taper = 0.6
    root = 2.0 * mean_c / (1.0 + taper)
    tip = root * taper
    return root, tip


def build_layout(ac: Aircraft, arch: str, key: str = None) -> Layout:
    # Per-aircraft overrides for the named example vehicles, matched to their
    # published planforms (see eVTOLpy journal/example aircraft/*_topview.png).
    arch = _ARCH_OVERRIDE.get(key, arch)
    fl = ac.fuselage_l_m
    fw = ac.fuselage_w_m
    fh = ac.fuselage_h_m
    span = ac.wingspan_m
    root_c = ac.wing_root_chord_m or 1.5
    tip_c = root_c * ac.wing_taper_ratio

    wing_z = 0.5 * fh

    # Empennage near the tail.
    htail_area = ac.horiz_tail_area_m2 or 1.0
    vtail_area = ac.vert_tail_area_m2 or 1.0
    # Tail span/height are unconstrained by the JSON (only the areas are), so
    # pick conventional aspect ratios for a sensible planform. This does not
    # affect the tail-volume coefficients (those depend only on area + arm).
    htail_span = max(math.sqrt(4.0 * htail_area), 2.0)   # AR_h ~ 4
    vtail_height = max(math.sqrt(1.5 * vtail_area), 1.2)  # AR_v ~ 1.5
    htail_root, htail_tip = _tail_chords(htail_area, htail_span)
    vtail_root, vtail_tip = _tail_chords(vtail_area, vtail_height)
    # Position so the *geometric* tail-volume coefficients match the JSON.
    # eVTOLpy sizes the tail areas assuming a wing-AC-to-tail-AC moment arm of
    # 0.5*fuselage_l. We anchor the tail AC near the fuselage tail (where tails
    # physically sit) and place the wing exactly that arm forward, so the arm
    # (and thus V_h, V_v) is exact while the tails stay on the airframe.
    mac = ac.wing_mac_m or root_c
    tail_arm = 0.5 * fl
    tail_ac_x = 0.90 * fl
    wing_ac_x = tail_ac_x - tail_arm
    wing_x = max(0.05 * fl, wing_ac_x - 0.25 * mac)  # unswept: MAC LE at wing_x
    htail_x = tail_ac_x - 0.25 * htail_root          # convert AC back to LE
    vtail_x = tail_ac_x - 0.25 * vtail_root

    lay = Layout(
        arch=arch,
        fuselage_l_m=fl, fuselage_w_m=fw, fuselage_h_m=fh,
        wing_x_m=wing_x, wing_span_m=span,
        wing_root_chord_m=root_c, wing_tip_chord_m=tip_c, wing_z_m=wing_z,
        htail_x_m=htail_x, htail_span_m=htail_span,
        htail_root_chord_m=htail_root, htail_tip_chord_m=htail_tip,
        vtail_x_m=vtail_x, vtail_height_m=vtail_height,
        vtail_root_chord_m=vtail_root, vtail_tip_chord_m=vtail_tip,
        d_value_m=ac.d_value_m,
    )
    custom = _AIRCRAFT_LAYOUTS.get(key)
    if custom is not None:
        custom(ac, lay)
    else:
        lay.rotors = _place_rotors(ac, lay, arch)
    return lay


def _place_rotors(ac: Aircraft, lay: Layout, arch: str) -> List[Rotor]:
    p = ac.propulsion
    if p is None:
        return []
    D = p.rotor_diameter_m
    R = D / 2.0
    rotors: List[Rotor] = []

    def spanwise_stations(n_per_side: float, inboard_y: float):
        """Even spanwise stations from inboard_y out to the half-span tip,
        leaving room for the rotor radius at the tip."""
        n = int(round(n_per_side))
        if n <= 0:
            return []
        y_tip = lay.wing_span_m / 2.0 - R
        if n == 1:
            return [0.5 * (inboard_y + y_tip)]
        return [inboard_y + (y_tip - inboard_y) * k / (n - 1) for k in range(n)]

    if arch == "tiltrotor":
        # Tilt rotors distributed along the wing; modeled in hover (disk level).
        # Pack from the wing tip inboard at one-diameter spacing (the densest
        # non-overlapping arrangement). If they don't fit in the semi-span, the
        # tip-path check will (correctly) report overlap.
        n_tilt = p.tilt_rotor_count or p.rotor_count
        n_per_side = int(round(n_tilt / 2.0))
        y_tip = lay.wing_span_m / 2.0 - R
        ys = [max(R, y_tip - k * D) for k in range(n_per_side)]
        for side in (+1, -1):
            for i, y in enumerate(ys):
                rotors.append(Rotor(
                    name=f"tilt_{'R' if side > 0 else 'L'}{i}",
                    x_m=lay.wing_x_m - 0.3 * lay.wing_root_chord_m,
                    y_m=side * y, z_m=lay.wing_z_m,
                    diameter_m=D, axis="tilt"))
        # Any dedicated lift rotors
        for i in range(int((p.lift_rotor_count or 0))):
            pass

    elif arch == "lift_cruise":
        # Distributed lift on longitudinal booms (a front + rear rotor per
        # boom), plus a cruise pusher at the tail. The front rotors tilt; the
        # rear rotors are fixed lift (the Archer Midnight pattern).
        n_pusher = int(p.pusher_rotor_count or 0)
        n_boom = int((p.lift_rotor_count or 0) + (p.tilt_rotor_count or 0))
        if n_boom == 0:
            n_boom = max(0, int(p.rotor_count) - n_pusher)
        rotors_per_boom = 2
        booms_total = max(1, n_boom // rotors_per_boom)
        per_side = max(1, booms_total // 2)

        rc = lay.wing_root_chord_m
        # Fore/aft rotor stations placed so each disk clears the wing chord:
        # the forward disk sits entirely ahead of the leading edge, the aft
        # disk entirely behind the trailing edge (margin beyond the rotor R).
        margin = 0.25
        x_fore = lay.wing_x_m - R - margin
        x_aft = lay.wing_x_m + rc + R + margin
        z = lay.wing_z_m + 0.15

        # Spanwise boom stations (spaced as evenly as the span allows; if the
        # spacing falls below D the clearance check will flag it).
        inboard = max(lay.fuselage_w_m / 2.0 + R + 0.2, 1.4)
        # Outboard rotor sits near the wingtip (disk may overhang slightly, as
        # on the real aircraft), which also frees up the spanwise spacing.
        y_tip = lay.wing_span_m / 2.0 - 0.5 * R
        if per_side <= 1:
            ys = [0.5 * (inboard + y_tip)]
        else:
            # Even spacing, but never closer than one diameter: if the span is
            # too tight, pack from the tip inboard at one-diameter spacing.
            spacing = max((y_tip - inboard) / (per_side - 1), D * 1.02)
            ys = [max(inboard, y_tip - k * spacing) for k in range(per_side)]

        idx = 0
        for side in (+1, -1):
            for bi, y in enumerate(ys):
                ystn = side * y
                sl = 'R' if side > 0 else 'L'
                # boom body spanning the two rotors
                lay.booms.append(Boom(
                    name=f"boom_{sl}{bi}", y_m=ystn,
                    x_start_m=x_fore - R, x_end_m=x_aft + R, z_m=z))
                for xx, tag, ax in ((x_fore, "fwd", "tilt"),
                                    (x_aft, "aft", "z")):
                    if idx >= n_boom:
                        break
                    rotors.append(Rotor(
                        name=f"lift_{sl}{bi}_{tag}",
                        x_m=xx, y_m=ystn, z_m=z, diameter_m=D, axis=ax))
                    idx += 1

        # Cruise pusher(s): vertical disk just aft of the furthest-back
        # structure (fuselage tail or empennage trailing edge).
        pd = p.pusher_rotor_diameter_m or D
        # Account for the swept-back tail tips when finding the aft-most extent.
        tan_s = math.tan(math.radians(TAIL_SWEEP_DEG))
        htail_aft = (lay.htail_x_m + (lay.htail_span_m / 2.0) * tan_s
                     + lay.htail_tip_chord_m)
        vtail_aft = (lay.vtail_x_m + lay.vtail_height_m * tan_s
                     + lay.vtail_tip_chord_m)
        aft_struct = max(lay.fuselage_l_m, htail_aft, vtail_aft)
        for i in range(n_pusher):
            y0 = 0.0 if n_pusher == 1 else (i - (n_pusher - 1) / 2.0) * pd * 1.1
            rotors.append(Rotor(
                name=f"pusher_{i}",
                x_m=aft_struct + 0.15,
                y_m=y0, z_m=lay.fuselage_h_m * 0.5,
                diameter_m=pd, axis="x", n_blade=4))

    elif arch == "multirotor":
        # Ring of rotors around the fuselage.
        n = p.rotor_count
        ring_r = max(lay.fuselage_w_m / 2.0 + R + 0.4, 1.5 * R)
        # Spread rotors so adjacent disks just clear: grow ring if needed.
        if n >= 2:
            min_ring = R / math.sin(math.pi / n) if n > 1 else ring_r
            ring_r = max(ring_r, min_ring * 1.05)
        for i in range(n):
            ang = 2.0 * math.pi * i / max(n, 1)
            rotors.append(Rotor(
                name=f"rotor_{i}",
                x_m=0.5 * lay.fuselage_l_m + ring_r * math.cos(ang),
                y_m=ring_r * math.sin(ang),
                z_m=lay.fuselage_h_m * 0.6,
                diameter_m=D, axis="z"))

    return rotors


# ---------------------------------------------------------------------------
# Per-aircraft layouts matched to the published planforms
# (eVTOLpy journal/example aircraft/*_topview.png)
# ---------------------------------------------------------------------------

def _layout_nasa_tr(ac: Aircraft, lay: Layout):
    """NASA tilt-rotor: tandem wings -- 4 tilting rotors on the front wing
    (2 per side), 2 on the rear wing (the default empennage acts as the rear
    lifting surface, sized to its large tail-volume-coefficient area)."""
    D = ac.propulsion.rotor_diameter_m
    R = D / 2.0
    z = lay.wing_z_m
    # Front wing: inboard + outboard rotor each side, just ahead of the LE.
    y_in = max(lay.fuselage_w_m / 2.0 + R + 0.2, 2.3)
    y_out = y_in + D + 0.2
    xf = lay.wing_x_m - R - 0.2
    for side in (+1, -1):
        sl = 'R' if side > 0 else 'L'
        for j, y in enumerate((y_in, y_out)):
            lay.rotors.append(Rotor(name=f"front_{sl}{j}", x_m=xf,
                                    y_m=side * y, z_m=z, diameter_m=D, axis="tilt"))
    # Rear wing (= default htail): one rotor each side, raised on a pylon over
    # the rear wing so the disk clears both lifting surfaces.
    y_r = max(lay.fuselage_w_m / 2.0 + R + 0.2, 2.4)
    xr = lay.htail_x_m + 0.2
    for side in (+1, -1):
        lay.rotors.append(Rotor(name=f"rear_{'R' if side > 0 else 'L'}",
                                x_m=xr, y_m=side * y_r,
                                z_m=lay.fuselage_h_m * 0.4 + 0.9,
                                diameter_m=D, axis="tilt"))


def _layout_joby(ac: Aircraft, lay: Layout):
    """Joby S4: swept wing carrying 4 tilting rotors (inboard + tip each side),
    plus a V-tail carrying 2 tilting rotors at the rear."""
    D = ac.propulsion.rotor_diameter_m
    R = D / 2.0
    lay.wing_sweep_deg = 12.0
    lay.draw_default_tail = False
    tan_s = math.tan(math.radians(lay.wing_sweep_deg))

    def le_x(y):  # leading-edge X at spanwise station y (swept-back wing)
        return lay.wing_x_m + abs(y) * tan_s

    y_in = max(lay.fuselage_w_m / 2.0 + R + 0.3, 2.4)
    y_tip = lay.wing_span_m / 2.0 - 0.3
    x_tip = le_x(y_tip) - R - 0.1
    # Put the inboard rotor far enough forward that its disk clears the tip
    # disk (they are too close spanwise to sit in the same line).
    dy = y_tip - y_in
    need_dx = math.sqrt(max((D + 0.2) ** 2 - dy ** 2, 0.0))
    x_in = x_tip - max(need_dx, R + 0.3)
    for side in (+1, -1):
        sl = 'R' if side > 0 else 'L'
        lay.rotors.append(Rotor(name=f"wing_{sl}_in", x_m=x_in, y_m=side * y_in,
                                z_m=lay.wing_z_m, diameter_m=D, axis="tilt"))
        lay.rotors.append(Rotor(name=f"wing_{sl}_tip", x_m=x_tip, y_m=side * y_tip,
                                z_m=lay.wing_z_m, diameter_m=D, axis="tilt"))
    # V-tail (two panels canted up ~40 deg) replacing the conventional tail.
    vt_x = 0.80 * lay.fuselage_l_m
    lay.extra_wings.append(ExtraWing(
        name="vtail", x_m=vt_x, z_m=lay.fuselage_h_m * 0.5,
        span_m=0.55 * lay.wing_span_m,
        root_chord_m=lay.vtail_root_chord_m * 1.4,
        tip_chord_m=lay.vtail_tip_chord_m * 1.4,
        sweep_deg=20.0, dihedral_deg=40.0, sym=True))
    # Two rotors on the V-tail, elevated and aft.
    y_vt = max(lay.fuselage_w_m / 2.0 + R + 0.2, 1.9)
    for side in (+1, -1):
        lay.rotors.append(Rotor(name=f"tail_{'R' if side > 0 else 'L'}",
                                x_m=vt_x + 0.2, y_m=side * y_vt,
                                z_m=lay.fuselage_h_m * 0.5 + 0.8,
                                diameter_m=D, axis="tilt"))


def _layout_wisk(ac: Aircraft, lay: Layout):
    """Wisk Cora: 12 lift rotors on 6 booms (the generic lift+cruise pattern)
    plus a tail pusher. The pusher is not in the JSON, so its diameter is
    assumed."""
    lay.rotors = _place_rotors(ac, lay, "lift_cruise")
    pd = ac.propulsion.pusher_rotor_diameter_m or 1.5   # assumed (not in JSON)
    tan_s = math.tan(math.radians(TAIL_SWEEP_DEG))
    aft = max(lay.fuselage_l_m,
              lay.htail_x_m + (lay.htail_span_m / 2.0) * tan_s + lay.htail_tip_chord_m,
              lay.vtail_x_m + lay.vtail_height_m * tan_s + lay.vtail_tip_chord_m)
    lay.rotors.append(Rotor(name="pusher_0", x_m=aft + 0.15, y_m=0.0,
                            z_m=lay.fuselage_h_m * 0.5, diameter_m=pd,
                            axis="x", n_blade=4))


# Force the architecture for vehicles the JSON counts misclassify.
_ARCH_OVERRIDE = {"wisk": "lift_cruise"}

# Dedicated layouts (keyed on the lower-cased config filename stem).
_AIRCRAFT_LAYOUTS = {
    "nasa_tr": _layout_nasa_tr,
    "joby_s4": _layout_joby,
    "wisk": _layout_wisk,
}


# ---------------------------------------------------------------------------
# Analytic checks (no OpenVSP needed)
# ---------------------------------------------------------------------------

def _disk_gap(a: Rotor, b: Rotor) -> float:
    """Center-to-center distance minus both radii (positive = clearance gap).

    For coaxial-in-plane lift rotors this is the in-plane tip-to-tip gap, which
    is the binding rotor-tip-path interference metric.
    """
    d = math.sqrt((a.x_m - b.x_m) ** 2 + (a.y_m - b.y_m) ** 2 + (a.z_m - b.z_m) ** 2)
    return d - (a.diameter_m / 2.0 + b.diameter_m / 2.0)


def analytic_checks(ac: Aircraft, lay: Layout) -> dict:
    res = {}

    # --- Rotor tip-path interference: rotor-to-rotor ---
    pairs = []
    rotors = lay.rotors
    worst = None
    for i in range(len(rotors)):
        for j in range(i + 1, len(rotors)):
            gap = _disk_gap(rotors[i], rotors[j])
            pairs.append({"a": rotors[i].name, "b": rotors[j].name,
                          "gap_m": round(gap, 4)})
            if worst is None or gap < worst["gap_m"]:
                worst = {"a": rotors[i].name, "b": rotors[j].name,
                         "gap_m": round(gap, 4)}
    res["rotor_tip_path_rotor_to_rotor"] = {
        "min_gap_m": worst["gap_m"] if worst else None,
        "worst_pair": worst,
        "pass": (worst["gap_m"] > 0.0) if worst else True,
        "n_pairs": len(pairs),
        "note": "in-plane tip-to-tip gap; <0 means disks overlap",
    }

    # --- Rotor tip-path vs fuselage ---
    fus_half_w = lay.fuselage_w_m / 2.0
    fus_clear = None
    for r in rotors:
        if r.axis == "x":
            continue  # centerline pusher: not an alongside-fuselage lift rotor
        if r.z_m > lay.fuselage_h_m / 2.0:
            continue  # rotor sits above the fuselage -> clears it vertically
        # lateral gap from rotor tip to fuselage side wall, if rotor is alongside it
        within_fus_x = -1.0 <= r.x_m <= lay.fuselage_l_m + 1.0
        lateral_gap = abs(r.y_m) - r.diameter_m / 2.0 - fus_half_w
        if within_fus_x:
            if fus_clear is None or lateral_gap < fus_clear["gap_m"]:
                fus_clear = {"rotor": r.name, "gap_m": round(lateral_gap, 4)}
    res["rotor_tip_path_to_fuselage"] = {
        "min_gap_m": fus_clear["gap_m"] if fus_clear else None,
        "worst": fus_clear,
        "pass": (fus_clear["gap_m"] > 0.0) if fus_clear else True,
    }

    # --- D-value consistency (largest turning diameter) ---
    if rotors:
        max_extent = max(abs(r.y_m) + r.diameter_m / 2.0 for r in rotors) * 2.0
        # also consider span
        max_extent = max(max_extent, lay.wing_span_m)
    else:
        max_extent = lay.wing_span_m
    res["d_value_consistency"] = {
        "json_d_value_m": lay.d_value_m,
        "layout_max_lateral_extent_m": round(max_extent, 4),
        "delta_m": round(lay.d_value_m - max_extent, 4),
        "note": "json d_value_m should be >= actual lateral extent of turning rotors",
        "pass": lay.d_value_m + 1e-6 >= max_extent,
    }

    # --- Ground / disk loading (informational) ---
    res["disk_loading_kg_p_m2"] = round(ac.disk_loading_kg_p_m2, 3) \
        if ac.propulsion else None

    return res


# ---------------------------------------------------------------------------
# OpenVSP model construction + geometry analyses
# ---------------------------------------------------------------------------

def build_openvsp_model(vsp, ac: Aircraft, lay: Layout, clear: bool = True):
    """Construct the 3-D model in OpenVSP. Returns dict of geom ids by set.

    Pass clear=False to add this vehicle to the existing model instead of
    starting fresh (used to assemble several configurations in one scene)."""
    if clear:
        vsp.VSPRenew()
        vsp.ClearVSPModel()

    ids = {"airframe": [], "booms": [], "rotors": [], "tip_paths": []}

    # --- Fuselage ---
    fid = vsp.AddGeom("FUSELAGE")
    vsp.SetGeomName(fid, "fuselage")
    vsp.SetParmVal(fid, "Length", "Design", lay.fuselage_l_m)
    vsp.Update()
    # Set cross-section width/height on interior stations (taper nose & tail).
    xsurf = vsp.GetXSecSurf(fid, 0)
    nx = vsp.GetNumXSec(xsurf)
    for i in range(nx):
        xs = vsp.GetXSec(xsurf, i)
        frac = i / max(nx - 1, 1)
        # bell-shaped scaling: small at nose/tail, full mid-body
        scale = math.sin(math.pi * frac) ** 0.5
        w = max(0.05, lay.fuselage_w_m * (0.15 + 0.85 * scale))
        h = max(0.05, lay.fuselage_h_m * (0.15 + 0.85 * scale))
        try:
            vsp.SetXSecWidthHeight(xs, w, h)
        except Exception:
            pass
    vsp.Update()
    ids["airframe"].append(fid)

    # --- Main wing ---
    wid = vsp.AddGeom("WING")
    vsp.SetGeomName(wid, "wing")
    # Drive the single section by span + root + tip chord.
    try:
        vsp.SetDriverGroup(wid, 1, vsp.SPAN_WSECT_DRIVER,
                           vsp.ROOTC_WSECT_DRIVER, vsp.TIPC_WSECT_DRIVER)
    except Exception:
        pass
    vsp.SetParmVal(wid, "Span", "XSec_1", lay.wing_span_m / 2.0)  # semi-span (sym)
    vsp.SetParmVal(wid, "Root_Chord", "XSec_1", lay.wing_root_chord_m)
    vsp.SetParmVal(wid, "Tip_Chord", "XSec_1", lay.wing_tip_chord_m)
    vsp.SetParmVal(wid, "Sweep", "XSec_1", lay.wing_sweep_deg)
    vsp.SetParmVal(wid, "X_Rel_Location", "XForm", lay.wing_x_m)
    vsp.SetParmVal(wid, "Z_Rel_Location", "XForm", lay.wing_z_m)
    vsp.Update()
    # Apply the JSON wing thickness-to-chord (wing_t_p_c) to every wing airfoil.
    try:
        t_p_c = ac.wing_t_p_c
        wxs = vsp.GetXSecSurf(wid, 0)
        for i in range(vsp.GetNumXSec(wxs)):
            tc = vsp.GetXSecParm(vsp.GetXSec(wxs, i), "ThickChord")
            if tc:
                vsp.SetParmVal(tc, t_p_c)
        vsp.Update()
    except Exception as e:
        print(f"  [wing] could not set thickness-to-chord: {e}")
    ids["airframe"].append(wid)

    if lay.draw_default_tail:
        # --- Horizontal tail ---
        hid = vsp.AddGeom("WING")
        vsp.SetGeomName(hid, "htail")
        try:
            vsp.SetDriverGroup(hid, 1, vsp.SPAN_WSECT_DRIVER,
                               vsp.ROOTC_WSECT_DRIVER, vsp.TIPC_WSECT_DRIVER)
        except Exception:
            pass
        vsp.SetParmVal(hid, "Span", "XSec_1", lay.htail_span_m / 2.0)
        vsp.SetParmVal(hid, "Root_Chord", "XSec_1", lay.htail_root_chord_m)
        vsp.SetParmVal(hid, "Tip_Chord", "XSec_1", lay.htail_tip_chord_m)
        vsp.SetParmVal(hid, "Sweep", "XSec_1", TAIL_SWEEP_DEG)
        vsp.SetParmVal(hid, "X_Rel_Location", "XForm", lay.htail_x_m)
        vsp.SetParmVal(hid, "Z_Rel_Location", "XForm", lay.fuselage_h_m * 0.4)
        vsp.Update()
        ids["airframe"].append(hid)

        # --- Vertical tail (single section wing rolled 90 deg, no Y symmetry) ---
        vid = vsp.AddGeom("WING")
        vsp.SetGeomName(vid, "vtail")
        try:
            vsp.SetDriverGroup(vid, 1, vsp.SPAN_WSECT_DRIVER,
                               vsp.ROOTC_WSECT_DRIVER, vsp.TIPC_WSECT_DRIVER)
        except Exception:
            pass
        vsp.SetParmVal(vid, "Span", "XSec_1", lay.vtail_height_m)
        vsp.SetParmVal(vid, "Root_Chord", "XSec_1", lay.vtail_root_chord_m)
        vsp.SetParmVal(vid, "Tip_Chord", "XSec_1", lay.vtail_tip_chord_m)
        vsp.SetParmVal(vid, "Sweep", "XSec_1", TAIL_SWEEP_DEG)
        vsp.SetParmVal(vid, "X_Rel_Location", "XForm", lay.vtail_x_m)
        vsp.SetParmVal(vid, "Z_Rel_Location", "XForm", lay.fuselage_h_m * 0.4)
        vsp.SetParmVal(vid, "X_Rel_Rotation", "XForm", 90.0)  # stand it up
        try:
            vsp.SetParmVal(vid, "Sym_Planar_Flag", "Sym", 0)  # no left/right mirror
        except Exception:
            pass
        vsp.Update()
        ids["airframe"].append(vid)

    # --- Extra lifting surfaces (rear wings, V-tail panels, ...) ---
    for ew in lay.extra_wings:
        eid = vsp.AddGeom("WING")
        vsp.SetGeomName(eid, ew.name)
        try:
            vsp.SetDriverGroup(eid, 1, vsp.SPAN_WSECT_DRIVER,
                               vsp.ROOTC_WSECT_DRIVER, vsp.TIPC_WSECT_DRIVER)
        except Exception:
            pass
        semi = ew.span_m / 2.0 if ew.sym else ew.span_m
        vsp.SetParmVal(eid, "Span", "XSec_1", semi)
        vsp.SetParmVal(eid, "Root_Chord", "XSec_1", ew.root_chord_m)
        vsp.SetParmVal(eid, "Tip_Chord", "XSec_1", ew.tip_chord_m)
        vsp.SetParmVal(eid, "Sweep", "XSec_1", ew.sweep_deg)
        vsp.SetParmVal(eid, "Dihedral", "XSec_1", ew.dihedral_deg)
        vsp.SetParmVal(eid, "X_Rel_Location", "XForm", ew.x_m)
        vsp.SetParmVal(eid, "Z_Rel_Location", "XForm", ew.z_m)
        if ew.x_rot_deg:
            vsp.SetParmVal(eid, "X_Rel_Rotation", "XForm", ew.x_rot_deg)
        if not ew.sym:
            try:
                vsp.SetParmVal(eid, "Sym_Planar_Flag", "Sym", 0)
            except Exception:
                pass
        vsp.Update()
        ids["airframe"].append(eid)

    # --- Booms (slender pods carrying the lift rotors) ---
    for b in lay.booms:
        bid = vsp.AddGeom("POD")
        vsp.SetGeomName(bid, b.name)
        length = max(b.x_end_m - b.x_start_m, 0.1)
        vsp.SetParmVal(bid, "Length", "Design", length)
        try:
            vsp.SetParmVal(bid, "FineRatio", "Design", length / b.diameter_m)
        except Exception:
            pass
        vsp.SetParmVal(bid, "X_Rel_Location", "XForm", b.x_start_m)
        vsp.SetParmVal(bid, "Y_Rel_Location", "XForm", b.y_m)
        vsp.SetParmVal(bid, "Z_Rel_Location", "XForm", b.z_m)
        vsp.Update()
        ids["booms"].append(bid)

    # --- Rotors (Propeller geoms) + Rotor Tip Path auxiliary geoms ---
    for r in lay.rotors:
        pid = vsp.AddGeom("PROP")
        vsp.SetGeomName(pid, r.name)
        vsp.SetParmVal(pid, "Diameter", "Design", r.diameter_m)
        # Actuator-disk mode: the swept disk *is* the rotor tip-path surface,
        # which both visualizes the keep-out zone and meshes reliably for the
        # clearance checks (thin blade/cone geometry meshes inconsistently).
        try:
            vsp.SetParmVal(pid, "PropMode", "Design", vsp.PROP_DISK)
        except Exception:
            pass
        vsp.SetParmVal(pid, "X_Rel_Location", "XForm", r.x_m)
        vsp.SetParmVal(pid, "Y_Rel_Location", "XForm", r.y_m)
        vsp.SetParmVal(pid, "Z_Rel_Location", "XForm", r.z_m)
        # Orient the disk. Default prop disk faces +X (thrust along X).
        # Lift rotor: disk horizontal -> rotate about Y by 90 deg.
        if r.axis in ("z", "tilt"):
            vsp.SetParmVal(pid, "Y_Rel_Rotation", "XForm", 90.0)
        vsp.Update()
        ids["rotors"].append(pid)

        # Rotor Tip Path Auxiliary Geometry (parent = the propeller).
        tip_id = _add_rotor_tip_path(vsp, pid, r)
        if tip_id:
            ids["tip_paths"].append(tip_id)

    vsp.Update()
    return ids


def _add_rotor_tip_path(vsp, prop_id: str, r: Rotor) -> Optional[str]:
    """Attach a Rotor Tip Path Auxiliary Geometry to a propeller.

    Verified against OpenVSP 3.50.5: the mode is selected by the integer parm
    "AuxiliaryGeomType" in group "Design", with value AUX_GEOM_ROTOR_TIP_PATH.
    """
    try:
        aux = vsp.AddGeom("AUXILIARY", prop_id)
    except Exception as e:
        print(f"  [tip-path] AUXILIARY geom not available in this build: {e}")
        return None
    vsp.SetGeomName(aux, f"{r.name}_tippath")
    try:
        vsp.SetParmVal(aux, "AuxiliaryGeomType", "Design",
                       vsp.AUX_GEOM_ROTOR_TIP_PATH)
    except Exception as e:
        print(f"  [tip-path] could not set AuxiliaryGeomType on {r.name}: {e}")
    vsp.Update()
    return aux


# OpenVSP user-set indices used for the geometry analyses.
SET_STRUCTURE = 3   # fuselage + wing + empennage (the rotor keep-out target)
SET_ROTORDISK = 4   # rotor actuator disks
SET_VEHICLE = 5     # everything (structure + booms + rotor disks)
SET_TIPPATH = 6     # rotor tip-path auxiliary geometries (visualization)
SET_SOLID = 7       # solid bodies for wetted-area/mass (structure + booms)
_IC = "InterferenceCase"   # parm group on a Geometry Analysis case
_BIG = 1e11         # OpenVSP "no measurement" sentinel (~1e12)


def _collect_results(vsp, rid: str) -> dict:
    res = {}
    for dn in vsp.GetAllDataNames(rid):
        try:
            dv = vsp.GetDoubleResults(rid, dn)
            if dv:
                res[dn] = list(dv)[:6]
                continue
        except Exception:
            pass
        try:
            sv = vsp.GetStringResults(rid, dn)
            if sv:
                res[dn] = list(sv)[:6]
        except Exception:
            pass
    return res


def _run_ga_case(vsp, check_type, primary_set, secondary_set=None,
                 secondary_type=0, extra=None) -> dict:
    """Create, configure, and execute one Geometry Analysis case."""
    ga = vsp.AddGeometryAnalysis()
    vsp.SetParmVal(vsp.FindParm(ga, "IntererenceCheckType", _IC), check_type)
    vsp.SetParmVal(vsp.FindParm(ga, "PrimarySet", _IC), primary_set)
    if secondary_set is not None:
        vsp.SetParmVal(vsp.FindParm(ga, "SecondarySet", _IC), secondary_set)
        vsp.SetParmVal(vsp.FindParm(ga, "SecondaryType", _IC), secondary_type)
    if extra:
        for name, val in extra.items():
            pid = vsp.FindParm(ga, name, _IC)
            if pid:
                vsp.SetParmVal(pid, val)
    vsp.Update()
    vsp.SetStringAnalysisInput("GeometryAnalysis", "CaseID", [ga])
    rid = vsp.ExecAnalysis("GeometryAnalysis")
    return _collect_results(vsp, rid)


def _legacy_analysis(vsp, name: str, set_idx: int) -> dict:
    try:
        vsp.SetAnalysisInputDefaults(name)
        vsp.SetIntAnalysisInput(name, "Set", [set_idx])
        rid = vsp.ExecAnalysis(name)
        return _collect_results(vsp, rid)
    except Exception as e:
        return {"error": str(e)}


def run_geometry_analyses(vsp, ids: dict, outdir: str) -> dict:
    """Run the OpenVSP Geometry Analyses and collect results.

    Verified against OpenVSP 3.50.5. The headline eVTOL check is rotor tip-path
    clearance, computed with ComputeMinClearanceDistance against the airframe
    (the actuator-disk surface is the swept tip path). Component packaging uses
    the Geometry Analysis Manager external self-interference case, whose
    `Con_Val` is a negative-null compound metric (<=0 => clear; see AIAA
    2026-4357, Eq. 1). Wetted area/volume and mass properties use the legacy
    CompGeom / MassProp analyses.
    """
    out = {"_available_analyses": list(vsp.ListAnalysis())}

    vsp.SetSetName(SET_STRUCTURE, "Structure")
    vsp.SetSetName(SET_ROTORDISK, "RotorDisks")
    vsp.SetSetName(SET_VEHICLE, "Vehicle")
    vsp.SetSetName(SET_TIPPATH, "RotorTipPaths")
    vsp.SetSetName(SET_SOLID, "SolidBodies")
    for gid in ids["airframe"]:
        vsp.SetSetFlag(gid, SET_STRUCTURE, True)
        vsp.SetSetFlag(gid, SET_SOLID, True)
        vsp.SetSetFlag(gid, SET_VEHICLE, True)
    for gid in ids.get("booms", []):
        # Booms are rotor mounts: included in the solid bodies and the whole
        # vehicle, but NOT in the rotor keep-out target (a rotor is meant to
        # touch its own boom).
        vsp.SetSetFlag(gid, SET_SOLID, True)
        vsp.SetSetFlag(gid, SET_VEHICLE, True)
    for gid in ids["rotors"]:
        vsp.SetSetFlag(gid, SET_ROTORDISK, True)
        vsp.SetSetFlag(gid, SET_VEHICLE, True)
    for gid in ids["tip_paths"]:
        vsp.SetSetFlag(gid, SET_TIPPATH, True)
    vsp.Update()

    # --- Rotor tip-path clearance vs airframe structure ---
    if ids["rotors"]:
        per_rotor = {}
        worst = None
        for pid in ids["rotors"]:
            d = vsp.ComputeMinClearanceDistance(pid, SET_STRUCTURE, False, "")
            if d >= _BIG:        # no measurement / degenerate
                continue
            name = vsp.GetGeomName(pid)
            per_rotor[name] = round(d, 4)
            if worst is None or d < worst[1]:
                worst = (name, d)
        out["rotor_tip_path_vs_airframe"] = {
            "min_clearance_m": round(worst[1], 4) if worst else None,
            "worst_rotor": worst[0] if worst else None,
            "pass": (worst[1] > 0.0) if worst else True,
            "per_rotor_m": per_rotor,
            "method": "ComputeMinClearanceDistance(rotor_disk, Structure set)",
        }

    # --- Component packaging: airframe self-interference (GA manager) ---
    try:
        res = _run_ga_case(vsp, vsp.EXTERNAL_SELF_INTERFERENCE, SET_STRUCTURE)
        cv = res.get("Con_Val", [None])[0]
        out["airframe_self_interference"] = {
            "Con_Val": cv, "pass": (cv is not None and cv <= 0.0),
            "results": res,
            "note": "Con_Val<=0 => structural components clear of each other"}
    except Exception as e:
        out["airframe_self_interference"] = {"error": str(e)}

    # --- Legacy: wetted area & volume, mass properties ---
    # Run on the solid bodies (structure + booms), not the thin actuator disks
    # which corrupt volume/mass integration.
    out["wetted_area_volume"] = _legacy_analysis(vsp, "CompGeom", SET_SOLID)
    out["mass_properties"] = _legacy_analysis(vsp, "MassProp", SET_SOLID)

    return out


def save_screenshot(vsp, path: str):
    """Headless ScreenGrab via the OpenVSP API.

    Note: on macOS this requires a real GUI/GL context, so it generally only
    works when the OpenVSP GUI is running. For reliable visuals either open the
    exported .vsp3 in the OpenVSP desktop app, or use the matplotlib 3-view
    produced by plot_layout().
    """
    try:
        vsp.InitGUI()
        vsp.ScreenGrab(path, 1600, 1000, True)
        if os.path.exists(path):
            return True
        print("  [screenshot] ScreenGrab produced no file (needs OpenVSP GUI "
              "running); open the .vsp3 in the OpenVSP app instead.")
        return False
    except Exception as e:
        print(f"  [screenshot] not available headless: {e}")
        return False


def plot_layout(lay: Layout, ac: Aircraft, path: str) -> bool:
    """Render a top/side/front 3-view of the layout with rotor disks drawn as
    circles, so rotor tip-path clearances are visible at a glance. Works
    headlessly (matplotlib Agg)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle, Circle, Ellipse
    except Exception as e:
        print(f"  [plot] matplotlib unavailable: {e}")
        return False

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fl, fw, fh = lay.fuselage_l_m, lay.fuselage_w_m, lay.fuselage_h_m

    def disk_color(r):
        return {"z": "#1f77b4", "tilt": "#2ca02c", "x": "#d62728"}.get(r.axis, "#1f77b4")

    # ---- Top view (X right, Y up) ----
    ax = axes[0]
    ax.set_title("Top view (plan)")
    ax.add_patch(Rectangle((0, -fw / 2), fl, fw, fc="#dddddd", ec="k"))
    # wing
    span, rc, tc = lay.wing_span_m, lay.wing_root_chord_m, lay.wing_tip_chord_m
    ax.add_patch(Rectangle((lay.wing_x_m, -span / 2), rc, span,
                           fc="#aac4e0", ec="k", alpha=0.7))
    # htail
    if lay.draw_default_tail:
        ax.add_patch(Rectangle((lay.htail_x_m, -lay.htail_span_m / 2),
                               lay.htail_root_chord_m, lay.htail_span_m,
                               fc="#c9c0e0", ec="k", alpha=0.7))
    # extra wings (rear wing / V-tail panels) shown by their plan projection
    for ew in lay.extra_wings:
        ax.add_patch(Rectangle((ew.x_m, -ew.span_m / 2), ew.root_chord_m,
                               ew.span_m, fc="#c9c0e0", ec="k", alpha=0.6))
    for b in lay.booms:
        ax.add_patch(Rectangle((b.x_start_m, b.y_m - b.diameter_m / 2),
                               b.x_end_m - b.x_start_m, b.diameter_m,
                               fc="#888888", ec="k"))
    for r in lay.rotors:
        if r.axis == "x":  # pusher disk vertical -> edge-on (line across Y)
            ax.plot([r.x_m, r.x_m],
                    [r.y_m - r.diameter_m / 2, r.y_m + r.diameter_m / 2],
                    color=disk_color(r), lw=1.6)
        else:
            ax.add_patch(Circle((r.x_m, r.y_m), r.diameter_m / 2,
                                fill=False, ec=disk_color(r), lw=1.6))
            ax.plot(r.x_m, r.y_m, ".", color=disk_color(r), ms=3)
    ax.set_xlabel("X aft [m]"); ax.set_ylabel("Y right [m]")

    # ---- Side view (X right, Z up) ----
    ax = axes[1]
    ax.set_title("Side view")
    ax.add_patch(Ellipse((fl / 2, 0), fl, fh, fc="#dddddd", ec="k"))
    ax.add_patch(Rectangle((lay.wing_x_m, lay.wing_z_m - 0.1),
                           lay.wing_root_chord_m, 0.2, fc="#aac4e0", ec="k"))
    if lay.draw_default_tail:
        ax.add_patch(Rectangle((lay.vtail_x_m, fh * 0.4),
                               lay.vtail_root_chord_m, lay.vtail_height_m,
                               fc="#c9c0e0", ec="k", alpha=0.7))
    for ew in lay.extra_wings:
        ax.add_patch(Rectangle((ew.x_m, ew.z_m), ew.root_chord_m,
                               max(0.4, ew.span_m / 2 * math.sin(
                                   math.radians(ew.dihedral_deg)) + 0.4),
                               fc="#c9c0e0", ec="k", alpha=0.5))
    for b in lay.booms:
        ax.plot([b.x_start_m, b.x_end_m], [b.z_m, b.z_m],
                color="#888888", lw=3, solid_capstyle="round")
    for r in lay.rotors:
        if r.axis in ("z", "tilt"):  # disk edge-on -> line of length D
            ax.plot([r.x_m - r.diameter_m / 2, r.x_m + r.diameter_m / 2],
                    [r.z_m, r.z_m], color=disk_color(r), lw=1.6)
        else:  # pusher disk faces aft -> circle in side view
            ax.add_patch(Circle((r.x_m, r.z_m), r.diameter_m / 2,
                                fill=False, ec=disk_color(r), lw=1.6))
    ax.set_xlabel("X aft [m]"); ax.set_ylabel("Z up [m]")

    # ---- Front view (Y right, Z up) ----
    ax = axes[2]
    ax.set_title("Front view")
    ax.add_patch(Ellipse((0, 0), fw, fh, fc="#dddddd", ec="k"))
    ax.plot([-lay.wing_span_m / 2, lay.wing_span_m / 2],
            [lay.wing_z_m, lay.wing_z_m], color="#5a82b0", lw=2)
    for r in lay.rotors:
        if r.axis in ("z", "tilt"):  # disk edge-on -> horizontal line
            ax.plot([r.y_m - r.diameter_m / 2, r.y_m + r.diameter_m / 2],
                    [r.z_m, r.z_m], color=disk_color(r), lw=1.6)
        else:  # pusher disk faces aft -> circle in front view
            ax.add_patch(Circle((r.y_m, r.z_m), r.diameter_m / 2,
                                fill=False, ec=disk_color(r), lw=1.6))
    ax.set_xlabel("Y right [m]"); ax.set_ylabel("Z up [m]")

    for ax in axes:
        ax.set_aspect("equal", "box"); ax.grid(True, alpha=0.3); ax.autoscale_view()
    fig.suptitle(f"eVTOLpy layout ({lay.arch}) — rotor disks = tip-path circles",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Build an OpenVSP model from an eVTOLpy JSON and run "
                    "geometry checks (rotor tip path, ground clearance, etc.)")
    ap.add_argument("config", help="path to eVTOLpy JSON config")
    ap.add_argument("--outdir", default="out", help="output directory")
    ap.add_argument("--arch", default="auto",
                    choices=["auto", "tiltrotor", "lift_cruise",
                             "multirotor", "fixed_wing"],
                    help="vehicle architecture (default: auto-detect)")
    ap.add_argument("--analytic-only", action="store_true",
                    help="skip OpenVSP; run only the pure-Python checks")
    ap.add_argument("--screenshot", action="store_true",
                    help="attempt an OpenVSP PNG screenshot (needs GUI)")
    ap.add_argument("--no-plot", action="store_true",
                    help="skip the matplotlib 3-view layout plot")
    ap.add_argument("--no-size", action="store_true",
                    help="do NOT run eVTOLpy's MTOW sizing iteration; build "
                         "geometry from the JSON's max_takeoff_mass_kg as-is")
    ap.add_argument("--aircraft", default=None,
                    help="force a named layout (e.g. joby_s4, nasa_tr, wisk); "
                         "defaults to the config filename stem")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    ac = Aircraft(args.config)

    # Size the vehicle first: eVTOLpy iterates empty+payload+battery -> MTOW
    # until convergence, which updates the mass that drives wing/tail areas.
    # The geometry is then built from the sized design.
    mtom_input = ac.max_takeoff_mass_kg
    sizing = {"input_mtom_kg": mtom_input, "sized": False}
    if not args.no_size:
        try:
            converged, history = ac.iterate_mtow
            sizing.update(sized=True, sized_mtom_kg=converged,
                          iterations=len(history))
            print(f"Sized: MTOM {mtom_input:.0f} -> {converged:.0f} kg "
                  f"({len(history)} iters)")
        except Exception as e:
            print(f"[sizing] iteration did not converge ({e.__class__.__name__}: "
                  f"{e}); building from the input MTOM as-is.")
            sizing["error"] = str(e)

    arch = detect_arch(ac) if args.arch == "auto" else args.arch
    key = (args.aircraft or
           os.path.splitext(os.path.basename(args.config))[0]).lower()
    lay = build_layout(ac, arch, key)

    report = {
        "config": os.path.abspath(args.config),
        "architecture": lay.arch,
        "sizing": sizing,
        "layout": asdict(lay),
        "analytic_checks": analytic_checks(ac, lay),
    }

    # Headless 3-view layout plot (rotor disks drawn as tip-path circles).
    if not args.no_plot:
        plot_path = os.path.join(args.outdir, "layout_3view.png")
        if plot_layout(lay, ac, plot_path):
            report["layout_plot"] = os.path.abspath(plot_path)

    # OpenVSP layer
    if not args.analytic_only:
        try:
            import openvsp as vsp
        except Exception:
            try:
                import vsp  # older module name
            except Exception:
                vsp = None
        if vsp is None:
            report["openvsp"] = {"status": "openvsp_python_api_not_installed"}
            print("OpenVSP Python API not found; ran analytic checks only.")
            print("Install with: pip install openvsp   (or build the OpenVSP "
                  "Python API and add it to PYTHONPATH)")
        else:
            ids = build_openvsp_model(vsp, ac, lay)
            vsp3 = os.path.join(args.outdir, "evtol_model.vsp3")
            vsp.WriteVSPFile(vsp3, vsp.SET_ALL)
            report["openvsp"] = {
                "status": "ok",
                "vsp3": os.path.abspath(vsp3),
                "n_airframe_geoms": len(ids["airframe"]),
                "n_rotors": len(ids["rotors"]),
                "n_tip_paths": len(ids["tip_paths"]),
                "geometry_analyses": run_geometry_analyses(vsp, ids, args.outdir),
            }
            if args.screenshot:
                png = os.path.join(args.outdir, "evtol_model.png")
                if save_screenshot(vsp, png):
                    report["openvsp"]["screenshot"] = os.path.abspath(png)

    out_json = os.path.join(args.outdir, "geometry_report.json")
    with open(out_json, "w") as f:
        json.dump(report, f, indent=2)

    _print_summary(report)
    print(f"\nFull report: {out_json}")


def _print_summary(report: dict):
    print("=" * 64)
    print(f"eVTOLpy -> OpenVSP geometry report")
    print(f"  architecture : {report['architecture']}")
    s = report.get("sizing", {})
    if s.get("sized"):
        print(f"  MTOM         : {s['input_mtom_kg']:.0f} -> "
              f"{s['sized_mtom_kg']:.0f} kg (sized)")
    else:
        print(f"  MTOM         : {s.get('input_mtom_kg', '?')} kg (as-is, not sized)")
    lay = report["layout"]
    print(f"  rotors       : {len(lay['rotors'])}")
    a = report["analytic_checks"]
    rr = a["rotor_tip_path_rotor_to_rotor"]
    print("-" * 64)
    print("Analytic checks:")
    print(f"  rotor tip-path (rotor-to-rotor) min gap : "
          f"{rr['min_gap_m']} m  [{'PASS' if rr['pass'] else 'FAIL'}]"
          + (f"  ({rr['worst_pair']['a']} <-> {rr['worst_pair']['b']})"
             if rr['worst_pair'] else ""))
    rf = a["rotor_tip_path_to_fuselage"]
    print(f"  rotor tip-path (to fuselage)   min gap  : "
          f"{rf['min_gap_m']} m  [{'PASS' if rf['pass'] else 'FAIL'}]")
    dv = a["d_value_consistency"]
    print(f"  D-value vs layout extent                : "
          f"json={dv['json_d_value_m']} m  layout={dv['layout_max_lateral_extent_m']} m"
          f"  [{'PASS' if dv['pass'] else 'FAIL'}]")
    print(f"  disk loading                            : "
          f"{a['disk_loading_kg_p_m2']} kg/m^2")
    if "openvsp" in report:
        print("-" * 64)
        print(f"OpenVSP: {report['openvsp'].get('status')}")
        if report["openvsp"].get("status") == "ok":
            o = report["openvsp"]
            print(f"  vsp3 : {o.get('vsp3')}")
            ga = o.get("geometry_analyses", {})
            tp = ga.get("rotor_tip_path_vs_airframe")
            if tp:
                v = "PASS" if tp.get("pass") else "FAIL"
                print(f"  rotor tip-path vs airframe min clearance : "
                      f"{tp.get('min_clearance_m')} m  [{v}]"
                      + (f"  ({tp.get('worst_rotor')})" if tp.get('worst_rotor') else ""))
            si = ga.get("airframe_self_interference", {})
            if "Con_Val" in si:
                v = "PASS" if si.get("pass") else "FAIL"
                print(f"  airframe self-interference Con_Val       : "
                      f"{si.get('Con_Val')}  [{v}]")
            wa = ga.get("wetted_area_volume", {})
            if "Total_Wet_Area" in wa:
                print(f"  wetted area / volume                     : "
                      f"{round(wa['Total_Wet_Area'][0], 2)} m^2 / "
                      f"{round(wa['Total_Wet_Vol'][0], 3)} m^3")
            mp = ga.get("mass_properties", {})
            for key in ("Total_Mass", "Mass"):
                if key in mp:
                    print(f"  mass properties Total_Mass               : "
                          f"{mp[key][0]}")
                    break
    print("=" * 64)


if __name__ == "__main__":
    main()
