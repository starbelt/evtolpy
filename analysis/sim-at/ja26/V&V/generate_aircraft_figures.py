#!/usr/bin/env python3
"""
Generate per-aircraft summary figures for the V&V eVTOL set.

Per-aircraft composite figures (as seen in Journal paper):
  - VV_<aircraft>_summary.eps         : a single full-width figure combining
                                          (a) a to-scale top-view planform drawn
                                              from wing/rotor geometry,
                                          (b) a mass pie (payload/battery/empty)
                                              with wing/disk loadings and the
                                              thrust-to-weight ratio,
                                          (c) power profile across mission phases,
                                          (d) energy profile across mission phases,
                                          (e) cruise drag buildup (drag counts).

"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.image as mpimg
import numpy as np

from evtol.aircraft import Aircraft

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, 'figures'))

# Aircraft set: each entry is (display name, JSON file, color).
AIRCRAFT = [
    ('Joby S4',           'Joby_s4.json',         '#1f77b4'),
    ('Wisk Cora',         'Wisk.json',            '#ff7f0e'),
    ('NASA Lift+cruise',  'NASA_LC.json',         '#2ca02c'),
    ('NASA Tiltrotor',    'NASA_TR.json',         '#d62728'),
    ('Archer Midnight',   'Archer_Midnight.json', '#9467bd'),
]


COL_WIDTH_IN = 3.25
FIG_WIDTH_IN = 3.25       
PT = 8    

# Uniform typography for all figures: one font family, one size, regular
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': PT,
    'axes.titlesize': PT,
    'axes.labelsize': PT,
    'xtick.labelsize': PT,
    'ytick.labelsize': PT,
    'legend.fontsize': PT,
    'font.weight': 'normal',
    'axes.titleweight': 'bold',
    'axes.labelweight': 'normal',
    'axes.titlepad': 2.0,
    'axes.labelpad': 1.5,
    'xtick.major.pad': 1.5,
    'ytick.major.pad': 1.5,
    'xtick.major.size': 2.5,
    'ytick.major.size': 2.5,
    'axes.linewidth': 0.5,
    'lines.linewidth': 0.6,
    'patch.linewidth': 0.4,
    'grid.linewidth': 0.4,
    'legend.borderpad': 0.2,
    'legend.labelspacing': 0.25,
    'legend.handlelength': 1.0,
    'legend.handletextpad': 0.4,
    'legend.columnspacing': 0.8,
    'legend.frameon': False,
})

SAVE_KW = dict(dpi=400, bbox_inches='tight', pad_inches=0.02)


def _save(fig, name):
    base, _ = os.path.splitext(name)
    for ext in ('.eps', '.png'):
        out = os.path.join(PAPER_DIR, base + ext)
        fig.savefig(out, **SAVE_KW)
        print(f'  Saved {out}')
    plt.close(fig)

def _accel_climb_power_kw(ac):
    if ac.mission.accel_climb_s is None or ac.mission.accel_climb_s < 1.0:
        return None
    return ac.accel_climb_avg_electric_power_kw

def size_aircraft(name, json_filename):
    """Size an aircraft and gather every quantity the figures need."""
    ac = Aircraft(os.path.join(SCRIPT_DIR, '../example aircraft', json_filename))
    final_mtow, _ = ac._iterate_mtow()

    hover_kw = ac.hover_electric_power_kw
    climb_kw = _accel_climb_power_kw(ac)
    trans_climb_kw = ac.trans_climb_avg_electric_power_kw
    cruise_kw = ac.cruise_avg_electric_power_kw

    wing_loading = (final_mtow / ac.wing_area_m2) if ac.wing_area_m2 > 0.0 else 0.0
    disk_loading = ac.disk_loading_kg_p_m2
    aspect_ratio = ac.wing_aspect_ratio
    ld_cruise = ac.cruise_l_p_d

    oew_components = {
        'Wing':           ac.wing_mass_kg,
        'Horiz. Tail':    ac.horiz_tail_mass_kg,
        'Vert. Tail':     ac.vert_tail_mass_kg,
        'Fuselage':       ac.fuselage_mass_kg,
        'Boom':           ac.boom_mass_kg,
        'Landing Gear':   ac.landing_gear_mass_kg,
        'Lift Rotor+Hub': ac.lift_rotor_hub_mass_kg,
        'Tilt Rotor':     ac.tilt_rotor_mass_kg,
        'Pusher Motor':   ac.pusher_motor_mass_kg,
        'EPU':            ac.epu_mass_kg,
        'Actuators':      ac.actuator_mass_kg,
        'Furnishings':    ac.furnishings_mass_kg,
        'ECS':            ac.environmental_control_system_mass_kg,
        'Avionics':       ac.avionics_mass_kg,
        'Hi-Volt Power':  ac.hivolt_power_dist_mass_kg,
        'Lo-Volt Power':  ac.lovolt_power_coms_mass_kg,
    }
    margin_mass = sum(oew_components.values()) * ac.mass_margin_factor
    oew_components['Mass Margin'] = margin_mass

    primary = {
        'depart_taxi':   ac.depart_taxi_energy_kw_hr,
        'hover_climb':   ac.hover_climb_energy_kw_hr,
        'trans_climb':   ac.trans_climb_energy_kw_hr,
        'depart_proc':   ac.depart_proc_energy_kw_hr,
        'accel_climb':   ac.accel_climb_energy_kw_hr,
        'cruise':        ac.cruise_energy_kw_hr,
        'decel_descend': ac.decel_descend_energy_kw_hr,
        'arrive_proc':   ac.arrive_proc_energy_kw_hr,
        'trans_descend': ac.trans_descend_energy_kw_hr,
        'hover_descend': ac.hover_descend_energy_kw_hr,
        'arrive_taxi':   ac.arrive_taxi_energy_kw_hr,
    }
    hover_energy = (primary['depart_taxi'] + primary['hover_climb']
                    + primary['hover_descend'] + primary['arrive_taxi'])
    climb_energy = (primary['trans_climb'] + primary['depart_proc']
                    + primary['accel_climb'])
    cruise_energy = (primary['cruise'] + primary['decel_descend']
                     + primary['arrive_proc'] + primary['trans_descend'])
    reserve_energy = ac.total_reserve_mission_energy_kw_hr or 0.0
    trip_energy = ac.total_mission_energy_kw_hr or 0.0
    nameplate_kwh = ac.battery_mass_kg * ac.power.batt_spec_energy_w_h_p_kg / 1000.0
    unusable_energy = max(nameplate_kwh - trip_energy, 0.0)

    empty_mass = ac.empty_mass_kg

    # Cruise drag buildup (parasite + induced) expressed as drag coefficients.
    drag_components = [
        ('Wing profile',  ac.wing_airfoil_cd_at_cruise_cl),
        ('Induced',       ac.induced_drag_cdi),
        ('Fuselage',      ac.fuselage_cd0),
        ('Horiz. tail',   ac.horiz_tail_cd0),
        ('Vert. tail',    ac.vert_tail_cd0),
        ('Landing gear',  ac.landing_gear_cd0),
        ('Stopped rotor', ac.stopped_rotor_cd0),
    ]
    drag_components = [(lbl, (cd or 0.0)) for lbl, cd in drag_components]

    # Mission-phase power and energy, in flight order. Phases with zero duration are dropped.
    phase_defs = [
        ('Taxi-out',     'depart_taxi'),
        ('Hover climb',  'hover_climb'),
        ('Trans. climb', 'trans_climb'),
        ('Depart proc.', 'depart_proc'),
        ('Accel climb',  'accel_climb'),
        ('Cruise',       'cruise'),
        ('Decel desc.',  'decel_descend'),
        ('Arrive proc.', 'arrive_proc'),
        ('Trans. desc.', 'trans_descend'),
        ('Hover desc.',  'hover_descend'),
        ('Taxi-in',      'arrive_taxi'),
    ]
    phases = []
    for label, key in phase_defs:
        dur = getattr(ac.mission, f'{key}_s')
        if dur is None or dur <= 0.0:
            continue
        phases.append({
            'label':  label,
            'dur_s':  dur,
            'power_kw': getattr(ac, f'{key}_avg_electric_power_kw') or 0.0,
            'energy_kwh': getattr(ac, f'{key}_energy_kw_hr') or 0.0,
        })

    return {
        'name': name,
        'mtom': final_mtow,
        'payload': ac.payload_kg,
        'battery': ac.battery_mass_kg,
        'empty': empty_mass,
        'power_hover_kw': hover_kw,
        'power_climb_kw': climb_kw,
        'power_trans_climb_kw': trans_climb_kw,
        'power_cruise_kw': cruise_kw,
        'aspect_ratio': aspect_ratio,
        'disk_loading': disk_loading,
        'wing_loading': wing_loading,
        'ld_cruise': ld_cruise,
        'oew_components': oew_components,
        'trip_energy_kwh': trip_energy,
        'nameplate_kwh': nameplate_kwh,
        'energy_hover': hover_energy,
        'energy_climb': climb_energy,
        'energy_cruise': cruise_energy,
        'energy_reserve': reserve_energy,
        'energy_unusable': unusable_energy,
        'over_torque_factor': ac.over_torque_factor,
        'wingspan_m':       ac.wingspan_m,
        'wing_root_chord_m': ac.wing_root_chord_m,
        'wing_taper_ratio': ac.wing_taper_ratio,
        'fuselage_l_m':     ac.fuselage_l_m,
        'fuselage_w_m':     ac.fuselage_w_m,
        'horiz_tail_area_m2': ac.horiz_tail_area_m2,
        'vert_tail_area_m2':  ac.vert_tail_area_m2,
        'rotor_count':      ac.propulsion.rotor_count,
        'lift_rotor_count': ac.propulsion.lift_rotor_count,
        'tilt_rotor_count': ac.propulsion.tilt_rotor_count,
        'rotor_diameter_m': ac.propulsion.rotor_diameter_m,
        'pusher_rotor_count': ac.propulsion.pusher_rotor_count,
        'pusher_rotor_diameter_m': ac.propulsion.pusher_rotor_diameter_m,
        'drag_components': drag_components,
        'phases': phases,
    }


def _short_name(name):
    """Uniform compact aircraft labels used on every x-axis."""
    return {
        'Joby S4':           'Joby',
        'Wisk Cora':         'Wisk',
        'NASA Lift+cruise':  'NASA LC',
        'NASA Tiltrotor':    'NASA TR',
        'Archer Midnight':   'Archer',
    }.get(name, name)


def _style_axes(ax):
    """Common axis styling: thin spines, light y-grid, no extra ornament."""
    ax.grid(False)
    ax.tick_params(width=0.5)
    for s in ax.spines.values():
        s.set_linewidth(0.5)



# ---------------------------------------------------------------------------
# Per-aircraft composite summary figure as seen in Journal Paper
# ---------------------------------------------------------------------------

FIG_WIDTH_FULL_IN = 7.0
FIG_HEIGHT_FULL_IN = 6.2


def _safe_slug(name):
    """Filesystem-safe token for a per-aircraft output filename."""
    return ''.join(c if c.isalnum() else '_' for c in name).strip('_')

_PLANFORM_IMAGES_SPAN = {}


def _draw_planform_image(ax, r, img_path):
    """Render a supplied top-view PNG with the loadings caption beneath it."""
    img = mpimg.imread(img_path)

    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha = img[..., 3:4]
        img = img[..., :3] * alpha + (1.0 - alpha) * 1.0

    h, w = img.shape[0], img.shape[1]

    aspect = h / float(w)
    ax.imshow(img, extent=(-1.0, 1.0, 0.0, 2.0 * aspect), zorder=2)

    # Wingspan dimension line just below the image (spans the full image width;
    span_frac = _PLANFORM_IMAGES_SPAN.get(str(r.get('name', '')), 1.0)
    y_dim = -0.08 * aspect
    ax.annotate('', xy=(span_frac, y_dim), xytext=(-span_frac, y_dim),
                arrowprops=dict(arrowstyle='<->', linewidth=0.6, color='#444444'))
    ax.text(0.0, y_dim - 0.035 * aspect, f'b = {r["wingspan_m"]:.1f} m',
            ha='center', va='top', fontsize=PT)

    info = (
        f'Wing loading: {r["wing_loading"]:.0f} kg/m$^2$\n'
        f'Disk loading: {r["disk_loading"]:.0f} kg/m$^2$\n'
        f'Thrust-to-weight ($T/W$): {r["over_torque_factor"]:.2f}\n'
        f'Rotor diameter: {r["rotor_diameter_m"]:.1f} m'
    )
    has_pusher = r.get("pusher_rotor_count", 0) > 0 and r.get("pusher_rotor_diameter_m") is not None
    if has_pusher:
        info += f'\nPusher diameter: {r["pusher_rotor_diameter_m"]:.1f} m'

    info_y = y_dim - 0.19 * aspect
    ax.text(0.0, info_y, info, ha='center', va='top', fontsize=PT)

    ax.set_aspect('equal')
    ax.set_xlim(-1.05, 1.05)
    y_pad = 0.26 * aspect if has_pusher else 0.21 * aspect
    ax.set_ylim(info_y - y_pad, 2.0 * aspect + 0.02 * aspect)
    ax.axis('off')
    ax.set_title('Top View')
def _draw_planform(ax, r):
    """Schematic to-scale top-view: wing planform, fuselage, rotor disks.

    Spanwise is horizontal (x), longitudinal is vertical (y, nose up). All
    dimensions are in metres so the panel is drawn to scale (equal aspect).
    """
    img_path = os.path.join(SCRIPT_DIR, '../example aircraft', f'{_safe_slug(r.get("name", ""))}_topview.png')
    _draw_planform_image(ax, r, img_path)



def _draw_mass_pie(ax, r):
    """Payload / battery / empty mass pie (fractions of MTOW)."""
    labels = ['Payload', 'Battery', 'Empty']
    vals = [r['payload'], r['battery'], r['empty']]
    colors = ['#6aa3c8', '#c9a96e', '#9aa0a6']
    ax.pie(vals, labels=labels, colors=colors, startangle=140,
           radius=1.2, labeldistance=1.1, pctdistance=0.62,
           autopct=lambda p: f'{p:.0f}%',
           wedgeprops=dict(edgecolor='white', linewidth=0.6),
           textprops=dict(fontsize=PT))
    ax.set_aspect('equal')
    ax.set_title(f'Mass Breakdown (MTOW {r["mtom"]:.0f} kg)', pad=-4)


def _phase_axes(ax, phases, key, ylabel, title, fmt, color):
    """
    Categorical mission-phase bar chart (mission power profile).
    """
    labels = [p['label'] for p in phases]
    vals = [p[key] for p in phases]
    x = np.arange(len(phases))
    vmax = max(vals) if vals else 1.0
    bars = ax.bar(x, vals, 0.74, color=color, linewidth=0)
    for bar, v in zip(bars, vals):
        if v <= 0:
            continue
        ax.text(bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + vmax * 0.02, fmt.format(v),
                ha='center', va='bottom', rotation=90, fontsize=PT)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, ha='center', fontsize=PT)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, vmax * 1.45)
    _style_axes(ax)
    ax.set_title(title)


def _waterfall(ax, labels, increments, ylabel, title, color, fmt):
    """Cumulative waterfall: each increment stacks on the running total, with
    a final 'Total' bar."""
    increments = list(increments)
    n = len(increments)
    bottoms, tops, cum = [], [], 0.0
    for v in increments:
        bottoms.append(cum)
        cum += v
        tops.append(cum)
    total = cum if cum > 0 else 1.0

    colors = color if isinstance(color, (list, tuple)) else [color] * n
    for i, v in enumerate(increments):
        ax.bar(i, v, 0.68, bottom=bottoms[i], color=colors[i], linewidth=0)
    ax.bar(n, total, 0.68, bottom=0.0, color='#555555', linewidth=0)

    # Dashed step connectors from each bar top to the next bar's base.
    for i in range(n):
        ax.plot([i + 0.34, (i + 1) - 0.34], [tops[i], tops[i]],
                color='#999999', linewidth=0.5, linestyle='--', zorder=1)

    off = total * 0.02
    for i, v in enumerate(increments):
        if v <= total * 0.004:   # hide negligible segments to avoid clutter
            continue
        ax.text(i, tops[i] + off, fmt.format(v), ha='center', va='bottom',
                rotation=90, fontsize=PT)
    ax.text(n, total + off, fmt.format(total), ha='center', va='bottom',
            rotation=90, fontsize=PT)

    all_labels = list(labels) + ['Total']
    ax.set_xticks(range(len(all_labels)))
    ax.set_xticklabels(all_labels, rotation=90, ha='center', fontsize=PT)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, total * 1.45)
    _style_axes(ax)
    ax.set_title(title)


def _draw_energy_waterfall(ax, r):
    """Mission energy as a cumulative waterfall across flight phases, with a
    trailing reserve column (total reserve-segment energy) before the total."""
    phases = r['phases']
    labels = [p['label'] for p in phases] + ['Reserve']
    increments = [p['energy_kwh'] for p in phases] + [r['energy_reserve'] or 0.0]
    colors = ['#2ca02c'] * len(phases) + ['#c9a96e']
    _waterfall(ax, labels, increments, 'Energy [kWh]', 'Energy Profile',
               colors, '{:.1f}')


def _draw_drag_waterfall(ax, r):
    """Cruise drag buildup (drag counts) as a cumulative waterfall."""
    comps = [(lbl, cd) for lbl, cd in r['drag_components']
             if cd and cd > 0.0]
    _waterfall(ax, [c[0] for c in comps], [c[1] for c in comps],
               'Coefficient of Drag', 'Cruise Drag Buildup',
               '#a35d6a', '{:.4f}')


def plot_aircraft_summary(r):
    """One composite full-width figure for a single aircraft.

    Top row: to-scale top view (with loadings beneath it) and an enlarged mass
    pie. Bottom row: mission power profile, energy waterfall, and cruise drag
    waterfall.
    """
    fig = plt.figure(figsize=(FIG_WIDTH_FULL_IN, FIG_HEIGHT_FULL_IN))
    gs = fig.add_gridspec(2, 6, height_ratios=[1.1, 1.0],
                          hspace=0.32, wspace=1.0)

    ax_plan = fig.add_subplot(gs[0, 0:3])
    ax_pie = fig.add_subplot(gs[0, 3:6])
    ax_power = fig.add_subplot(gs[1, 0:2])
    ax_energy = fig.add_subplot(gs[1, 2:4])
    ax_drag = fig.add_subplot(gs[1, 4:6])

    _draw_planform(ax_plan, r)
    _draw_mass_pie(ax_pie, r)
    _phase_axes(ax_power, r['phases'], 'power_kw', 'Electric power [kW]',
                'Power Profile', '{:.0f}', '#1f77b4')
    _draw_energy_waterfall(ax_energy, r)
    _draw_drag_waterfall(ax_drag, r)

    fig.suptitle(f"{r['name']} High Level Overview", fontsize=PT + 1, fontweight='bold', y=0.950)
    fig.tight_layout(rect=(0, 0, 1, 0.925))
    _save(fig, f'VV_{_safe_slug(r["name"])}_summary.eps')


if __name__ == '__main__':
    os.makedirs(PAPER_DIR, exist_ok=True)

    results = []
    for name, json_filename, color in AIRCRAFT:
        print(f'Sizing {name}...')
        r = size_aircraft(name, json_filename)
        r['color'] = color
        results.append(r)

    print('\nGenerating per-aircraft summary figures...')
    for r in results:
        print(f'  {r["name"]}...')
        plot_aircraft_summary(r)
    print('\nDone.')
