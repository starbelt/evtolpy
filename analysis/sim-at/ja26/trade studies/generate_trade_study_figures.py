#!/usr/bin/env python3
"""
Runs parametric sweeps across three eVTOL configurations (NASA tiltrotor, Archer
Midnight, NASA lift+cruise) varying battery specific energy, mission range, rotor
diameter, payload, and cruise speed. Saves all figures as EPS and PNG into the
paper directory.

"""

import sys
import os
import json
import tempfile
import concurrent.futures

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from evtol.aircraft import Aircraft


COL_WIDTH_IN = 3.25
FIG_WIDTH_IN = COL_WIDTH_IN
FIGSIZE = (FIG_WIDTH_IN, 2.7)
FIGSIZE_WIDE = (3.25, 3.05)
PT = 8

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
    'lines.linewidth': 0.9,
    'lines.markersize': 3.5,
    'patch.linewidth': 0.4,
    'grid.linewidth': 0.4,
    'legend.borderpad': 0.2,
    'legend.labelspacing': 0.25,
    'legend.handlelength': 1.6,
    'legend.handletextpad': 0.4,
    'legend.columnspacing': 0.8,
    'legend.frameon': False,
    'ps.useafm': True,
})

SAVE_KW = dict(dpi=400, bbox_inches='tight', pad_inches=0.02)


def _save_fig(fig, base_name, tight=True):
    """Write both .eps and .png to the paper directory.
    """
    base, _ = os.path.splitext(base_name)
    eps_out = os.path.join(PAPER_DIR, base + '.eps')
    png_out = os.path.join(PAPER_DIR, base + '.png')
    kw = dict(SAVE_KW)
    if not tight:
        kw['bbox_inches'] = None
    fig.savefig(eps_out, format='eps', **kw)
    fig.savefig(png_out, format='png', **kw)
    plt.close(fig)
    print(f'  Saved {eps_out} and {png_out}')


def _style_axes(ax):
    """Common axis styling: thin spines, light grid, no extra ornament."""
    ax.grid(True, alpha=0.3, linewidth=0.4)
    ax.tick_params(width=0.5)
    for s in ax.spines.values():
        s.set_linewidth(0.5)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, 'figures'))


# Configuration registry
CONFIGS = {
    'tiltrotor': {
        'json': os.path.join(SCRIPT_DIR, '../example aircraft/NASA_TR.json'),
        'color': 'tab:blue',
        'marker': 'o',
        'linestyle': '-',
        'arch': 'Tilt-Rotor',
    },
    'lift+tilt': {
        'json': os.path.join(SCRIPT_DIR, '../example aircraft/Archer_Midnight.json'),
        'color': 'tab:orange',
        'marker': 's',
        'linestyle': '--',
        'arch': 'Lift+Cruise (Tilt)',
    },
    'lift+cruise': {
        'json': os.path.join(SCRIPT_DIR, '../example aircraft/NASA_LC.json'),
        'color': 'tab:green',
        'marker': '^',
        'linestyle': '-.',
        'arch': 'Lift+Cruise (Pusher)',
    },
}

# Sweep parameter ranges
BATTERY_SWEEP = [200, 225, 250, 275, 300, 325, 350, 375, 400, 450, 500]
RANGE_SWEEP_NM = [10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80]
ROTOR_SWEEP_M = [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0]
PAYLOAD_SWEEP_KG = [200, 250, 300, 350, 400, 450, 500, 550, 600, 700, 800]
CRUISE_SPEED_SWEEP_MPS = [40, 50, 60, 65, 70, 75, 80, 85, 90, 100, 110]

BATTERY_OVERLAY_RANGES_NM = [20, 40, 60]
RANGE_LINESTYLE = {20: ':', 40: '-', 60: '--'}

M_PER_NM = 1852.0

# Standardized mission/payload/battery applied to every sweep case so the
# trade study is a pure architecture comparison. 
COMMON_RANGE_NM = 40.0
COMMON_CRUISE_SPEED_M_P_S = 60.0

COMMON_BASELINE = {
    # Payload
    'aircraft.payload_kg': 454.0,

    # Battery 
    'power.batt_spec_energy_w_h_p_kg': 400.0,
    'power.batt_int_factor': 1.0,
    'power.batt_inaccessible_energy_frac': 0.0,
    'power.batt_eol_capacity': 1.0,
    'power.epu_effic': 0.92,

    # Primary mission segments
    'mission.depart_taxi_avg_h_m_p_s': 1.34,
    'mission.depart_taxi_s': 30.0,
    'mission.hover_climb_avg_v_m_p_s': 0.508,
    'mission.hover_climb_s': 60.0,
    'mission.trans_climb_avg_h_m_p_s': 28.8,
    'mission.trans_climb_v_m_p_s': 1.0,
    'mission.trans_climb_s': 20.0,
    'mission.depart_proc_s': 1.0,
    'mission.accel_climb_v_m_p_s': 4.572,
    'mission.accel_climb_s': 263.3,
    'mission.decel_descend_v_m_p_s': 4.572,
    'mission.decel_descend_s': 1.0,
    'mission.arrive_proc_s': 1.0,
    'mission.trans_descend_avg_h_m_p_s': 28.8,
    'mission.trans_descend_v_m_p_s': 2.0,
    'mission.trans_descend_s': 20.0,
    'mission.hover_descend_avg_v_m_p_s': 0.508,
    'mission.hover_descend_s': 60.0,
    'mission.arrive_taxi_avg_h_m_p_s': 1.34,
    'mission.arrive_taxi_s': 30.0,
    # Reserve: 20 min loiter at architecture's cruise speed
    'mission.reserve_hover_climb_avg_v_m_p_s': 0.508,
    'mission.reserve_hover_climb_s': 1.0,
    'mission.reserve_trans_climb_avg_h_m_p_s': 28.8,
    'mission.reserve_trans_climb_v_m_p_s': 2.0,
    'mission.reserve_trans_climb_s': 1.0,
    'mission.reserve_accel_climb_v_m_p_s': 4.572,
    'mission.reserve_accel_climb_s': 1.0,
    'mission.reserve_cruise_s': 1200.0,
    'mission.reserve_decel_descend_v_m_p_s': 4.572,
    'mission.reserve_decel_descend_s': 1.0,
    'mission.reserve_trans_descend_avg_h_m_p_s': 28.8,
    'mission.reserve_trans_descend_v_m_p_s': 2.0,
    'mission.reserve_trans_descend_s': 1.0,
    'mission.reserve_hover_descend_avg_v_m_p_s': 0.508,
    'mission.reserve_hover_descend_s': 1.0,
}


def _climb_horizontal_distance_m(cruise_speed):
    """Horizontal ground distance covered during the climb-to-cruise phase.
    Hover and taxi segments carry no forward ground distance and are excluded.
    """
    return (
        cruise_speed * (COMMON_BASELINE['mission.depart_proc_s']
                        + COMMON_BASELINE['mission.accel_climb_s'])
        + COMMON_BASELINE['mission.trans_climb_avg_h_m_p_s']
        * COMMON_BASELINE['mission.trans_climb_s']
    )


def cruise_s_for_trip(trip_nm, cruise_speed):
    """Cruise duration so that climb + cruise horizontal distance == trip_nm.

    The reference trip distance is defined over the climb and cruise phases
    (descent distance is not counted); the cruise leg makes up whatever
    horizontal distance the climb phase does not already cover.
    """
    cruise_dist_m = trip_nm * M_PER_NM - _climb_horizontal_distance_m(cruise_speed)
    return cruise_dist_m / cruise_speed


def build_common_mods(baseline_json_path):
    """
    Return COMMON_BASELINE augmented with derived per-architecture fields.
    """
    with open(baseline_json_path, 'r') as f:
        cfg = json.load(f)  # noqa: F841 — kept for parity with prior signature
    cruise_speed = COMMON_CRUISE_SPEED_M_P_S

    mods = dict(COMMON_BASELINE)
    mods['mission.cruise_h_m_p_s'] = cruise_speed
    mods['mission.cruise_s'] = cruise_s_for_trip(COMMON_RANGE_NM, cruise_speed)
    mods['mission.depart_proc_h_m_p_s'] = cruise_speed
    mods['mission.accel_climb_avg_h_m_p_s'] = cruise_speed
    mods['mission.decel_descend_avg_h_m_p_s'] = cruise_speed
    mods['mission.arrive_proc_h_m_p_s'] = cruise_speed
    mods['mission.reserve_accel_climb_avg_h_m_p_s'] = cruise_speed
    mods['mission.reserve_cruise_h_m_p_s'] = cruise_speed
    mods['mission.reserve_decel_descend_avg_h_m_p_s'] = cruise_speed
    return mods


def run_sweep_case(baseline_json_path, modifications, apply_common=True):
    """
    Load baseline JSON, apply modifications, run sizing.
    """
    with open(baseline_json_path, 'r') as f:
        cfg = json.load(f)

    if apply_common:
        merged = build_common_mods(baseline_json_path)
        merged.update(modifications)
    else:
        merged = modifications

    for key_path, value in merged.items():
        parts = key_path.split('.')
        section = cfg
        for part in parts[:-1]:
            section = section[part]
        section[parts[-1]] = value

    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(cfg, tmp)
    tmp.close()

    try:
        ac = Aircraft(tmp.name)
        final_mtow, _ = ac._iterate_mtow()
        return final_mtow, ac
    except Exception:
        return None, None
    finally:
        os.unlink(tmp.name)


def collect_metrics(ac, mtow):
    """Collect key sizing metrics from a converged aircraft."""
    if ac is None or mtow is None:
        return None

    primary_segments = [
        ac.depart_taxi_energy_kw_hr, ac.hover_climb_energy_kw_hr,
        ac.trans_climb_energy_kw_hr, ac.depart_proc_energy_kw_hr,
        ac.accel_climb_energy_kw_hr, ac.cruise_energy_kw_hr,
        ac.decel_descend_energy_kw_hr, ac.arrive_proc_energy_kw_hr,
        ac.trans_descend_energy_kw_hr, ac.hover_descend_energy_kw_hr,
        ac.arrive_taxi_energy_kw_hr,
    ]
    reserve_segments = [
        ac.reserve_hover_climb_energy_kw_hr, ac.reserve_trans_climb_energy_kw_hr,
        ac.reserve_accel_climb_energy_kw_hr, ac.reserve_cruise_energy_kw_hr,
        ac.reserve_decel_descend_energy_kw_hr, ac.reserve_trans_descend_energy_kw_hr,
        ac.reserve_hover_descend_energy_kw_hr,
    ]
    total_energy = sum(primary_segments) + sum(reserve_segments)

    return {
        'mtow': mtow,
        'battery_mass_kg': ac.battery_mass_kg,
        'empty_mass_kg': ac.empty_mass_kg,
        'total_energy_kw_hr': total_energy,
        'cruise_energy_kw_hr': ac.cruise_energy_kw_hr,
        'cruise_l_p_d': ac.cruise_l_p_d,
        'hover_shaft_power_kw': ac.hover_shaft_power_kw,
        'cruise_avg_shaft_power_kw': ac.cruise_avg_shaft_power_kw,
        'payload_kg': ac.payload_kg,
        'payload_mass_frac': ac.payload_kg / mtow,
        'battery_mass_frac': ac.battery_mass_kg / mtow,
        'range_nm': (
            ac.mission.depart_proc_h_m_p_s * ac.mission.depart_proc_s
            + ac.mission.accel_climb_avg_h_m_p_s * ac.mission.accel_climb_s
            + ac.mission.trans_climb_avg_h_m_p_s * ac.mission.trans_climb_s
            + ac.mission.cruise_h_m_p_s * ac.mission.cruise_s
        ) / M_PER_NM,
    }


# ---------------------------------------------------------------------------
# Sweep runners
# ---------------------------------------------------------------------------

def _evaluate_case(case_tuple):
    """Worker function for multiprocessing."""
    baseline_json_path, mods = case_tuple
    mtow, ac = run_sweep_case(baseline_json_path, mods)
    return collect_metrics(ac, mtow)


def run_battery_sweep():
    """
    Sweep battery specific energy for all configs at multiple ranges.

    Returns {config_name: {range_nm: {batt_e: metrics}}}. The reference
    range (COMMON_RANGE_NM) is included so downstream plots that want a
    single-range view can index that slice.
    """
    results = {name: {} for name in CONFIGS}
    cases = []
    keys = []
    
    cruise_speed = COMMON_CRUISE_SPEED_M_P_S
    for name, cfg in CONFIGS.items():
        for range_nm in BATTERY_OVERLAY_RANGES_NM:
            results[name][range_nm] = {}
            cruise_s = cruise_s_for_trip(range_nm, cruise_speed)
            for batt_e in BATTERY_SWEEP:
                mods = {
                    'power.batt_spec_energy_w_h_p_kg': batt_e,
                    'mission.cruise_s': cruise_s,
                }
                cases.append((cfg['json'], mods))
                keys.append((name, range_nm, batt_e))
                
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for key, res in zip(keys, executor.map(_evaluate_case, cases)):
            name, range_nm, batt_e = key
            results[name][range_nm][batt_e] = res

    for name in CONFIGS:
        print(f'  Battery sweep complete: {name}')
    return results


def run_range_sweep():
    """Sweep mission range for all configs."""
    results = {name: {} for name in CONFIGS}
    cases = []
    keys = []
    
    cruise_speed = COMMON_CRUISE_SPEED_M_P_S
    for name, cfg in CONFIGS.items():
        for range_nm in RANGE_SWEEP_NM:
            cruise_s = cruise_s_for_trip(range_nm, cruise_speed)
            mods = {'mission.cruise_s': cruise_s}
            cases.append((cfg['json'], mods))
            keys.append((name, range_nm))
            
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for key, res in zip(keys, executor.map(_evaluate_case, cases)):
            name, range_nm = key
            results[name][range_nm] = res

    for name in CONFIGS:
        print(f'  Range sweep complete: {name}')
    return results


def run_rotor_sweep():
    """Sweep rotor diameter for all configs."""
    results = {name: {} for name in CONFIGS}
    cases = []
    keys = []

    for name, cfg in CONFIGS.items():
        for rotor_d in ROTOR_SWEEP_M:
            mods = {'propulsion.rotor_diameter_m': rotor_d}
            cases.append((cfg['json'], mods))
            keys.append((name, rotor_d))
            
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for key, res in zip(keys, executor.map(_evaluate_case, cases)):
            name, rotor_d = key
            results[name][rotor_d] = res

    for name in CONFIGS:
        print(f'  Rotor sweep complete: {name}')
    return results


def run_payload_sweep():
    """Sweep payload mass for all configs."""
    results = {name: {} for name in CONFIGS}
    cases = []
    keys = []
    
    for name, cfg in CONFIGS.items():
        for payload in PAYLOAD_SWEEP_KG:
            mods = {'aircraft.payload_kg': payload}
            cases.append((cfg['json'], mods))
            keys.append((name, payload))
            
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for key, res in zip(keys, executor.map(_evaluate_case, cases)):
            name, payload = key
            results[name][payload] = res

    for name in CONFIGS:
        print(f'  Payload sweep complete: {name}')
    return results


def run_cruise_speed_sweep():
    """Sweep cruise speed for all configs.

    Cruise distance is kept at the standardized COMMON_RANGE_NM, so
    cruise_s scales inversely with cruise_h_m_p_s. The architecture's other
    speed-dependent mission averages (accel/decel/proc) are also pinned to
    the swept cruise speed for self-consistency.
    """
    results = {name: {} for name in CONFIGS}
    cases = []
    keys = []
    
    for name, cfg in CONFIGS.items():
        for cruise_mps in CRUISE_SPEED_SWEEP_MPS:
            cruise_s = cruise_s_for_trip(COMMON_RANGE_NM, cruise_mps)
            mods = {
                'mission.cruise_h_m_p_s': cruise_mps,
                'mission.cruise_s': cruise_s,
                'mission.depart_proc_h_m_p_s': cruise_mps,
                'mission.accel_climb_avg_h_m_p_s': cruise_mps,
                'mission.decel_descend_avg_h_m_p_s': cruise_mps,
                'mission.arrive_proc_h_m_p_s': cruise_mps,
                'mission.reserve_accel_climb_avg_h_m_p_s': cruise_mps,
                'mission.reserve_cruise_h_m_p_s': cruise_mps,
                'mission.reserve_decel_descend_avg_h_m_p_s': cruise_mps,
            }
            cases.append((cfg['json'], mods))
            keys.append((name, cruise_mps))
            
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for key, res in zip(keys, executor.map(_evaluate_case, cases)):
            name, cruise_mps = key
            results[name][cruise_mps] = res

    for name in CONFIGS:
        print(f'  Cruise speed sweep complete: {name}')
    return results


# ---------------------------------------------------------------------------
# Helpers for extracting sweep data with None handling
# ---------------------------------------------------------------------------

def extract_sweep_values(data, config_name, sweep_keys, metric):
    """Extract x values and metric values, skipping None results."""
    xs, ys = [], []
    for k in sweep_keys:
        r = data[config_name].get(k)
        if r is not None and r.get(metric) is not None:
            xs.append(k)
            ys.append(r[metric])
    return xs, ys


# ---------------------------------------------------------------------------
# Plotting functions
# ---------------------------------------------------------------------------

def _plot_simple_sweep(data, sweep_keys, metric, xlabel, ylabel, title,
                       out_name, y_scale=1.0):
    """Single-line-per-config sweep: one line per configuration."""
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for name, cfg in CONFIGS.items():
        xs, ys = extract_sweep_values(data, name, sweep_keys, metric)
        ax.plot(xs, [y * y_scale for y in ys], marker=cfg['marker'],
                linestyle=cfg['linestyle'], color=cfg['color'], label=name)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    _style_axes(ax)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.20), ncol=3)
    fig.tight_layout(pad=0.2, rect=(0, 0.12, 1, 1))
    _save_fig(fig, out_name)


def _plot_overlay_sweep(data, x_sweep, range_overlays, metric,
                        xlabel, ylabel, title, out_name, y_scale=1.0,
                        figsize=FIGSIZE_WIDE):
    """Multi-range overlay sweep: 3 configs x N ranges = many lines."""
    fig, ax = plt.subplots(figsize=figsize)
    for name, cfg in CONFIGS.items():
        for range_nm in range_overlays:
            xs, ys = [], []
            for x in x_sweep:
                r = data[name][range_nm].get(x)
                if r is not None and r.get(metric) is not None:
                    xs.append(x)
                    ys.append(r[metric] * y_scale)
            ax.plot(xs, ys, marker=cfg['marker'],
                    linestyle=RANGE_LINESTYLE[range_nm], color=cfg['color'],
                    label=f'{name}, {range_nm} nm')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    _style_axes(ax)
    fig.tight_layout(pad=0.2, rect=(0, 0.30, 1, 1))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 0.29),
              bbox_transform=fig.transFigure, ncol=2)
    _save_fig(fig, out_name, tight=False)


def plot_battery_sweep_mtow(data):
    _plot_overlay_sweep(
        data, BATTERY_SWEEP, BATTERY_OVERLAY_RANGES_NM, 'mtow',
        'Battery Specific Energy [Wh/kg]', 'Converged MTOW [kg]',
        'MTOW Sensitivity to Battery Specific Energy',
        'TS_battery_sweep_mtow.eps')


def plot_battery_sweep_mass(data):
    _plot_overlay_sweep(
        data, BATTERY_SWEEP, BATTERY_OVERLAY_RANGES_NM, 'battery_mass_frac',
        'Battery Specific Energy [Wh/kg]', 'Battery Mass Fraction [%]',
        'Battery Mass Fraction vs. Specific Energy',
        'TS_battery_sweep_mass.eps', y_scale=100.0)


def plot_range_sweep_mtow(data):
    _plot_simple_sweep(
        data, RANGE_SWEEP_NM, 'mtow',
        'Mission Range [nm]', 'Converged MTOW [kg]',
        'MTOW Sensitivity to Mission Range',
        'TS_range_sweep_mtow.eps')


def plot_range_sweep_energy(data):
    _plot_simple_sweep(
        data, RANGE_SWEEP_NM, 'total_energy_kw_hr',
        'Mission Range [nm]', 'Total Mission Energy [kWh]',
        'Total Energy vs. Mission Range',
        'TS_range_sweep_energy.eps')


def plot_range_sweep_payload_frac(data):
    _plot_simple_sweep(
        data, RANGE_SWEEP_NM, 'payload_mass_frac',
        'Mission Range [nm]', 'Payload Mass Fraction [%]',
        'Payload Mass Fraction vs. Mission Range',
        'TS_range_sweep_payload_frac.eps', y_scale=100.0)


def plot_rotor_sweep_mtow(data):
    _plot_simple_sweep(
        data, ROTOR_SWEEP_M, 'mtow',
        'Rotor Diameter [m]', 'Converged MTOW [kg]',
        'MTOW Sensitivity to Rotor Diameter',
        'TS_rotor_sweep_mtow.eps')


def plot_rotor_sweep_hover_power(data):
    _plot_simple_sweep(
        data, ROTOR_SWEEP_M, 'hover_shaft_power_kw',
        'Rotor Diameter [m]', 'Hover Shaft Power [kW]',
        'Hover Power vs. Rotor Diameter',
        'TS_rotor_sweep_hover_power.eps')


def plot_payload_sweep_mtow(data):
    _plot_simple_sweep(
        data, PAYLOAD_SWEEP_KG, 'mtow',
        'Payload [kg]', 'Converged MTOW [kg]',
        'MTOW Sensitivity to Payload',
        'TS_payload_sweep_mtow.eps')


def plot_payload_sweep_battery(data):
    _plot_simple_sweep(
        data, PAYLOAD_SWEEP_KG, 'battery_mass_kg',
        'Payload [kg]', 'Battery Mass [kg]',
        'Battery Mass vs. Payload',
        'TS_payload_sweep_battery.eps')


def plot_cruise_speed_sweep_mtow(data):
    _plot_simple_sweep(
        data, CRUISE_SPEED_SWEEP_MPS, 'mtow',
        'Cruise Speed [m/s]', 'Converged MTOW [kg]',
        'MTOW Sensitivity to Cruise Speed',
        'TS_cruise_speed_sweep_mtow.eps')


def plot_config_comparison(battery_data, range_data):
    """Write a LaTeX table comparing configs at common design points."""
    # Common design point: 40 nm range, 300 Wh/kg battery
    target_range = 40
    target_batt = 300

    metrics = [
        ('mtow', 'MTOW (kg)'),
        ('battery_mass_kg', 'Battery Mass (kg)'),
        ('hover_shaft_power_kw', 'Hover Power (kW)'),
        ('cruise_avg_shaft_power_kw', 'Cruise Power (kW)'),
        ('cruise_l_p_d', 'Cruise L/D'),
        ('payload_mass_frac', 'Payload Fraction (\\%)'),
    ]

    names = list(CONFIGS.keys())
    short_names = ['tiltrotor', 'lift+tilt', 'lift+cruise']

    out_tex = os.path.join(PAPER_DIR, 'TS_config_comparison.tex')
    with open(out_tex, 'w') as f:
        f.write('\\begin{table*}[t]\n')
        f.write('\\centering\n')
        f.write('\\caption{Architecture comparison across six sizing metrics at two common design points: 40~nm range and 300~Wh/kg battery specific energy. All other mission, payload, and battery inputs are identical across the three vehicles.}\n')
        f.write('\\label{tab:ts_comparison}\n')
        f.write('\\small\n')
        f.write('\\begin{tabular}{l c c c | c c c}\n')
        f.write('\\hline\n')
        f.write(' & \\multicolumn{3}{c|}{\\textbf{40 nm range (400 Wh/kg)}} & \\multicolumn{3}{c}{\\textbf{300 Wh/kg battery (40 nm)}} \\\\\n')
        f.write('\\textbf{Metric} & ' + ' & '.join(short_names) + ' & ' + ' & '.join(short_names) + ' \\\\\n')
        f.write('\\hline\n')
        
        for metric_key, metric_label in metrics:
            row_str = metric_label
            
            # 40 nm range (with 400 Wh/kg baseline)
            for name in names:
                r_data = range_data[name].get(target_range)
                val = r_data[metric_key] if r_data else 0
                if metric_key == 'payload_mass_frac':
                    val *= 100
                if metric_key == 'cruise_l_p_d':
                    row_str += f' & {val:.1f}'
                else:
                    row_str += f' & {val:.0f}'
                    
            # 300 Wh/kg battery (at 40 nm range)
            for name in names:
                b_data = battery_data[name].get(target_range, {}).get(target_batt)
                val = b_data[metric_key] if b_data else 0
                if metric_key == 'payload_mass_frac':
                    val *= 100
                if metric_key == 'cruise_l_p_d':
                    row_str += f' & {val:.1f}'
                else:
                    row_str += f' & {val:.0f}'
            
            row_str += ' \\\\\n'
            f.write(row_str)
            
        f.write('\\hline\n')
        f.write('\\end{tabular}\n')
        f.write('\\end{table*}\n')
        
    print(f'  Saved {out_tex}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    os.makedirs(PAPER_DIR, exist_ok=True)

    print('Running sweeps...')
    battery_data = run_battery_sweep()
    range_data = run_range_sweep()
    rotor_data = run_rotor_sweep()
    payload_data = run_payload_sweep()
    cruise_speed_data = run_cruise_speed_sweep()

    print('\nGenerating figures...')
    plot_battery_sweep_mtow(battery_data)
    plot_battery_sweep_mass(battery_data)
    plot_range_sweep_mtow(range_data)
    plot_range_sweep_energy(range_data)
    plot_range_sweep_payload_frac(range_data)
    plot_rotor_sweep_mtow(rotor_data)
    plot_rotor_sweep_hover_power(rotor_data)
    plot_payload_sweep_mtow(payload_data)
    plot_payload_sweep_battery(payload_data)
    plot_cruise_speed_sweep_mtow(cruise_speed_data)
    plot_config_comparison(battery_data, range_data)

    print('\nUpdating architecture diagram...')
    import subprocess
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    subprocess.run([sys.executable, 'eVTOLpy journal/XDSM/generate_xdsm.py'], cwd=repo_root, check=True)

    print('\nDone. All trade study figures saved to:', PAPER_DIR)
