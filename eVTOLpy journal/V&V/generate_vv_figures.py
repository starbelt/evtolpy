#!/usr/bin/env python3
"""
Generate V&V figures for the eVTOLpy paper.

Sizes four reference vehicles (Joby S4, Wisk Cora, NASA LC, NASA TR),
produces MTOW convergence plots and sizing comparison bar charts,
and saves all figures as PNGs to the paper directory.

Usage:
    python3 evtol/V&V/generate_vv_figures.py
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from evtol.aircraft import Aircraft

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAPER_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, 'figures'))

VEHICLES = {
    'Joby S4': {
        'json': os.path.join(SCRIPT_DIR, '../example aircraft/Joby_s4.json'),
        'tag': 'joby',
        'arch': 'Tilt-Rotor',
        'ref': {
            'MTOW (kg)': 1961.0,
            'Hover Power (kW)': 413.0,
            'Cruise Power (kW)': 151.5,
            'Battery (kg)': 374.6,
            'Cruise L/D': 4.1,
            'Empty Weight (kg)': 1226.40,
        },
    },
    'Wisk Cora': {
        'json': os.path.join(SCRIPT_DIR, '../example aircraft/Wisk.json'),
        'tag': 'wisk',
        'arch': 'Lift+Cruise',
        'ref': {
            'MTOW (kg)': 1269.0,
            'Hover Power (kW)': 326.1,
            'Cruise Power (kW)': 64.3,
            'Battery (kg)': 293.1,
            'Cruise L/D': 10.8,
            'Empty Weight (kg)': 815.90,
        },
    },
    'NASA LC': {
        'json': os.path.join(SCRIPT_DIR, '../example aircraft/NASA_LC.json'),
        'tag': 'nasa_lc',
        'arch': 'Lift+Cruise',
        'ref': {
            'MTOW (kg)': 3724.0,
            'Hover Power (kW)': 829.2,
            'Cruise Power (kW)': 279.2,
            'Battery (kg)': 767.9,
            'Cruise L/D': 8.5,
            'Empty Weight (kg)': 2411.79,
        },
    },
    'NASA TR': {
        'json': os.path.join(SCRIPT_DIR, '../example aircraft/NASA_TR.json'),
        'tag': 'nasa_tr',
        'arch': 'Tilt-Rotor',
        'ref': {
            'MTOW (kg)': 3010.04,
            'Hover Power (kW)': None,
            'Cruise Power (kW)': None,
            'Battery (kg)': 729.38,
            'Cruise L/D': None,
            'Empty Weight (kg)': 1842.45,
        },
    },
    'Archer Midnight': {
        'json': os.path.join(SCRIPT_DIR, '../example aircraft/Archer_Midnight.json'),
        'tag': 'archer',
        'arch': 'Lift+Cruise',
        'ref': {
            'MTOW (kg)': 3175.0,
            'Hover Power (kW)': None,
            'Cruise Power (kW)': None,
            'Battery (kg)': None,
            'Cruise L/D': None,
            'Empty Weight (kg)': 1968.50,
        },
    },
}

LBS_TO_KG = 0.453592




def size_vehicle(name, cfg):
    """Size a vehicle and return results dict."""
    ac = Aircraft(cfg['json'])
    final_mtow, history = ac._iterate_mtow()
    hover_kw = ac._calc_hover_electric_power_kw()
    cruise_kw = ac._calc_cruise_avg_electric_power_kw()

    structural = (ac.wing_mass_kg + ac.horiz_tail_mass_kg + ac.vert_tail_mass_kg +
                  ac.fuselage_mass_kg + ac.boom_mass_kg + ac.landing_gear_mass_kg)
    propulsion = ac.epu_mass_kg + ac.lift_rotor_hub_mass_kg + ac.tilt_rotor_mass_kg
    subsystems = (ac.actuator_mass_kg + ac.furnishings_mass_kg +
                  ac.environmental_control_system_mass_kg + ac.avionics_mass_kg +
                  ac.hivolt_power_dist_mass_kg + ac.lovolt_power_coms_mass_kg)

    return {
        'ac': ac,
        'history': history,
        'mtow': final_mtow,
        'empty': ac.empty_mass_kg,
        'battery': ac.battery_mass_kg,
        'payload': ac.payload_kg,
        'hover_power': hover_kw,
        'cruise_power': cruise_kw,
        'cruise_ld': ac.cruise_l_p_d,
        'structural': structural,
        'propulsion': propulsion,
        'subsystems': subsystems,
    }


def plot_mtow_convergence(name, tag, history):
    """Plot MTOW convergence for a single vehicle."""
    iters = [r['iteration'] for r in history]
    guess = [r['mtow_guess_kg'] for r in history]
    new = [r['new_mtow_kg'] for r in history]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    ax1.plot(iters, guess, 'o-', markersize=3, label='MTOW Guess')
    ax1.plot(iters, new, 's-', markersize=3, label='New MTOW')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('MTOW (kg)')
    ax1.set_title(f'{name} — MTOW Convergence')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    delta = [r['delta_kg'] for r in history]
    ax2.plot(iters, delta, 'x-', markersize=4, color='tab:red')
    ax2.axhline(0, color='black', linestyle='--', linewidth=0.5)
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('MTOW Delta (kg)')
    ax2.set_title(f'{name} — Convergence Error')
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    out = os.path.join(PAPER_DIR, f'VV_{tag}_mtow.png')
    fig.savefig(out, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved {out}')


def plot_sizing_comparison(all_results):
    """Grouped bar chart: sized vs reference for MTOW, hover power, cruise power, battery."""
    metrics = ['MTOW (kg)', 'Hover Power (kW)', 'Cruise Power (kW)', 'Battery (kg)']
    vehicles_with_all = ['Joby S4', 'Wisk Cora', 'NASA LC']

    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    x = np.arange(len(vehicles_with_all))
    width = 0.35

    key_map = {
        'MTOW (kg)': 'mtow',
        'Hover Power (kW)': 'hover_power',
        'Cruise Power (kW)': 'cruise_power',
        'Battery (kg)': 'battery',
    }

    for i, metric in enumerate(metrics):
        ax = axes[i]
        sized_vals = [all_results[v][key_map[metric]] for v in vehicles_with_all]
        ref_vals = [VEHICLES[v]['ref'][metric] for v in vehicles_with_all]

        bars1 = ax.bar(x - width/2, sized_vals, width, label='eVTOLpy', color='tab:blue', alpha=0.8)
        bars2 = ax.bar(x + width/2, ref_vals, width, label='Reference', color='tab:orange', alpha=0.8)

        ax.set_ylabel(metric)
        ax.set_title(metric)
        ax.set_xticks(x)
        ax.set_xticklabels(['Joby S4', 'Wisk\nCora', 'NASA\nLC'], fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
        if i == 0:
            ax.legend(fontsize=8)

    fig.suptitle('Sizing Comparison: eVTOLpy vs. Reference Data', fontsize=13, fontweight='bold')
    fig.tight_layout()
    out = os.path.join(PAPER_DIR, 'VV_sizing_comparison.png')
    fig.savefig(out, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved {out}')


def plot_mass_breakdown(all_results):
    """Stacked bar chart showing mass fractions for all 4 vehicles."""
    names = list(all_results.keys())
    structural = [all_results[v]['structural'] for v in names]
    propulsion = [all_results[v]['propulsion'] for v in names]
    subsystems = [all_results[v]['subsystems'] for v in names]
    battery = [all_results[v]['battery'] for v in names]
    payload = [all_results[v]['payload'] for v in names]
    mtow = [all_results[v]['mtow'] for v in names]

    # Convert to fractions
    struct_frac = [s/m for s, m in zip(structural, mtow)]
    prop_frac = [p/m for p, m in zip(propulsion, mtow)]
    sub_frac = [s/m for s, m in zip(subsystems, mtow)]
    batt_frac = [b/m for b, m in zip(battery, mtow)]
    pay_frac = [p/m for p, m in zip(payload, mtow)]

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(names))
    width = 0.5

    bottom = np.zeros(len(names))
    colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f']
    labels = ['Structural', 'Propulsion', 'Subsystems', 'Battery', 'Payload']
    fracs = [struct_frac, prop_frac, sub_frac, batt_frac, pay_frac]

    for frac, color, label in zip(fracs, colors, labels):
        ax.bar(x, frac, width, bottom=bottom, label=label, color=color, alpha=0.9)
        bottom += np.array(frac)

    ax.set_ylabel('Mass Fraction')
    ax.set_title('Mass Breakdown Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9)
    ax.legend(loc='upper right', fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3, axis='y')

    # Add MTOW labels on top
    for i, m in enumerate(mtow):
        ax.text(i, bottom[i] + 0.01, f'{m:.0f} kg', ha='center', va='bottom', fontsize=8, fontweight='bold')

    fig.tight_layout()
    out = os.path.join(PAPER_DIR, 'VV_mass_breakdown.png')
    fig.savefig(out, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved {out}')


def plot_metric_bar(all_results, ref_key, calc_key, metric_display_name, filename_suffix, err_p=0.1):
    """Grouped bar chart of Calculated vs Published metric. Every vehicle
    in ``all_results`` is shown; for vehicles with no reference value the
    reference bar is omitted (calculated bar still rendered)."""
    short = {
        'Joby S4': 'Joby S4',
        'Wisk Cora': 'Wisk\nCora',
        'NASA LC': 'NASA\nLC',
        'NASA TR': 'NASA\nTR',
        'Archer Midnight': 'Archer\nMidnight',
    }
    names = list(all_results.keys())
    calculated, published, labels = [], [], []
    for n in names:
        calc_val = all_results[n].get(calc_key)
        ref_val = VEHICLES[n]['ref'].get(ref_key)
        if calc_val is None:
            continue
        calculated.append(calc_val)
        published.append(ref_val)  # may be None
        labels.append(short.get(n, n))

    if not calculated:
        return

    # Journal-column sizing: 3.25 in wide, uniform 8 pt sans-serif.
    PT = 8
    with plt.rc_context({
        'font.family': 'sans-serif',
        'font.size': PT,
        'axes.titlesize': PT,
        'axes.labelsize': PT,
        'xtick.labelsize': PT,
        'ytick.labelsize': PT,
        'legend.fontsize': PT,
        'axes.titleweight': 'bold',
        'axes.titlepad': 2.0,
        'axes.labelpad': 1.5,
        'xtick.major.pad': 1.5,
        'ytick.major.pad': 1.5,
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
    }):
        fig, ax = plt.subplots(figsize=(3.25, 2.6))
        x = np.arange(len(labels))
        width = 0.36

        ax.bar(x - width / 2, calculated, width, label='eVTOLpy',
               color='tab:blue', alpha=0.85)
        # Reference bars: skip vehicles with no ref value.
        ref_x, ref_y = [], []
        for xi, p in zip(x, published):
            if p is not None:
                ref_x.append(xi + width / 2)
                ref_y.append(p)
        ax.bar(ref_x, ref_y, width, label='Reference',
               color='tab:orange', alpha=0.85)

        ax.set_ylabel(metric_display_name)
        ax.set_title(f'Calculated vs Published {metric_display_name}')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend(loc='upper left', ncol=2)
        ax.grid(True, alpha=0.3, axis='y')

        ymax = max([*calculated, *(p for p in published if p is not None)])
        for i, p in enumerate(published):
            if p is None:
                ax.text(x[i], calculated[i] + ymax * 0.02, 'N/A',
                        ha='center', va='bottom', fontsize=PT,
                        color='black', style='italic')
                continue
            diff = (calculated[i] - p) / p * 100
            h = max(calculated[i], p)
            ax.text(x[i], h + ymax * 0.02, f'{diff:+.1f}%',
                    ha='center', va='bottom', fontsize=PT, color='black')

        ax.set_ylim(0, ymax * 1.22)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)

        fig.tight_layout(pad=0.2)
        for ext in ('png', 'eps'):
            out = os.path.join(PAPER_DIR, f'VV_{filename_suffix}_bar.{ext}')
            fig.savefig(out, dpi=400, bbox_inches='tight', pad_inches=0.02)
            print(f'  Saved {out}')
        plt.close(fig)


if __name__ == '__main__':
    os.makedirs(PAPER_DIR, exist_ok=True)

    all_results = {}
    for name, cfg in VEHICLES.items():
        print(f'Sizing {name}...')
        all_results[name] = size_vehicle(name, cfg)
        plot_mtow_convergence(name, cfg['tag'], all_results[name]['history'])

    print('\nGenerating comparison figures...')
    plot_sizing_comparison(all_results)
    plot_mass_breakdown(all_results)
    plot_metric_bar(all_results, 'MTOW (kg)', 'mtow', 'Takeoff Weight (kg)', 'mtow')
    plot_metric_bar(all_results, 'Empty Weight (kg)', 'empty', 'Empty Weight (kg)', 'empty_weight')
    plot_metric_bar(all_results, 'Battery (kg)', 'battery', 'Battery Weight (kg)', 'battery', err_p=0.15)
    plot_metric_bar(all_results, 'Hover Power (kW)', 'hover_power', 'Hover Power (kW)', 'hover_power')
    plot_metric_bar(all_results, 'Cruise Power (kW)', 'cruise_power', 'Cruise Power (kW)', 'cruise_power', err_p=0.15)
    print('\nDone.')
