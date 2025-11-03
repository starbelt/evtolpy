import subprocess

# Run a shell command and print status.
def run_command(cmd):
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
    # else:
    #     print(f"✅ Finished: {cmd}")

def run_case(base_dir, config):
    commands = [
        # # Energy
        # f"python log_mission_segment_energy.py {config} {base_dir}",
        # f"python plt_mission_segment_energy.py {base_dir}mission-segment-energy.csv {base_dir}",

        # # Power
        # f"python log_power_profile_all.py {config} {base_dir}",
        # f"python plt_power_profile_all.py {base_dir}power-profile-all.csv {base_dir}",

        # f"python log_power_all.py {config} {base_dir}",
        # f"python plt_power_all.py {base_dir}power-all.csv {base_dir}",

        # # Weight
        # f"python log_mass_breakdown.py {config} {base_dir}",
        # f"python plt_mass_breakdown.py {base_dir}mass-breakdown.csv {base_dir}",

        # f"python log_mtow_iteration.py {config} {base_dir}",
        # f"python plt_mtow_iteration.py {base_dir}mtow-iteration.csv {base_dir}",

        # # ABU (1): Assisted Takeoff
        # f"python log_mission_segment_abu_analysis_energy.py {config} {base_dir}",
        # f"python plt_mission_segment_abu_analysis_energy.py {base_dir}mission-segment-abu-analysis-energy.csv {base_dir}",

        # # ABU (2.1): Extended Flight (Attached full-segment)
        # f"python log_mission_segment_abu_analysis_flight_extension.py {config} {base_dir}",
        # f"python plt_mission_segment_abu_analysis_flight_extension.py {base_dir}mission-segment-abu-analysis-flight-extension.csv {base_dir}",

        # # ABU (2.2): Extended Flight (Detach-on-Depletion or End-of-Cruise)
        # f"python log_mission_segment_abu_analysis_flight_extension_detach_on_depletion_or_end.py {config} {base_dir}",
        # f"python plt_mission_segment_abu_analysis_flight_extension_detach_on_depletion_or_end.py {base_dir}mission-segment-abu-analysis-flight-extension-detach-on-depletion-or-end.csv {base_dir}",

        # # ABU (3): Safety Landing
        # f"python log_mission_segment_abu_analysis_landing_safety_loiter.py {config} {base_dir}",
        # f"python plt_mission_segment_abu_analysis_landing_safety_loiter.py {base_dir}mission-segment-abu-analysis-landing-safety-loiter.csv {base_dir}",

        # # ABU (4.1): Common Case Economics (Baseline, non-ABU)
        # f"python log_mission_segment_abu_analysis_common_case_economics_baseline.py {config} {base_dir}",

        # # ABU (4.2): Common Case Economics (ABU, Assisted Takeoff)
        # f"python log_mission_segment_abu_analysis_common_case_economics_assisted_takeoff.py {config} {base_dir}",

        # # ABU (4.3): Common Case Economics (ABU, Extended Flight Powered by ABU)
        # f"python log_mission_segment_abu_analysis_common_case_economics_extended_flight.py {config} {base_dir}",

        # ABU (4.4): Common Case Economics (ABU, Combined - Assisted Takeoff & Extended Flight Powered by ABU)
        f"python log_mission_segment_abu_analysis_common_case_economics_combined.py {config} {base_dir}",
    ]

    for cmd in commands:
        run_command(cmd)


def main():
    # Case study
    cases = [
        ## High Altitude - 3000 ft
        # Archer Midnight
        ("../../cfg-case-study/high-altitude-3000-ft/archer-midnight/30-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/archer-midnight/30-miles/Archer-Midnight-3000-30.json"),
        ("../../cfg-case-study/high-altitude-3000-ft/archer-midnight/45-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/archer-midnight/45-miles/Archer-Midnight-3000-45.json"),
        ("../../cfg-case-study/high-altitude-3000-ft/archer-midnight/60-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/archer-midnight/60-miles/Archer-Midnight-3000-60.json"),

        # Joby S4
        ("../../cfg-case-study/high-altitude-3000-ft/joby-s4/30-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/joby-s4/30-miles/Joby-S4-3000-30.json"),
        ("../../cfg-case-study/high-altitude-3000-ft/joby-s4/45-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/joby-s4/45-miles/Joby-S4-3000-45.json"),
        ("../../cfg-case-study/high-altitude-3000-ft/joby-s4/60-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/joby-s4/60-miles/Joby-S4-3000-60.json"),

        # Supernal S-A2
        ("../../cfg-case-study/high-altitude-3000-ft/supernal/30-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/supernal/30-miles/Supernal-S-A2-3000-30.json"),
        ("../../cfg-case-study/high-altitude-3000-ft/supernal/45-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/supernal/45-miles/Supernal-S-A2-3000-45.json"),
        ("../../cfg-case-study/high-altitude-3000-ft/supernal/60-miles/",
         "../../cfg-case-study/high-altitude-3000-ft/supernal/60-miles/Supernal-S-A2-3000-60.json"),
        
        ## Low Altitude - 1500 ft
        # Archer Midnight
        ("../../cfg-case-study/low-altitude-1500-ft/archer-midnight/30-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/archer-midnight/30-miles/Archer-Midnight-1500-30.json"),
        ("../../cfg-case-study/low-altitude-1500-ft/archer-midnight/45-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/archer-midnight/45-miles/Archer-Midnight-1500-45.json"),
        ("../../cfg-case-study/low-altitude-1500-ft/archer-midnight/60-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/archer-midnight/60-miles/Archer-Midnight-1500-60.json"),

        # Joby S4
        ("../../cfg-case-study/low-altitude-1500-ft/joby-s4/30-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/joby-s4/30-miles/Joby-S4-1500-30.json"),
        ("../../cfg-case-study/low-altitude-1500-ft/joby-s4/45-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/joby-s4/45-miles/Joby-S4-1500-45.json"),
        ("../../cfg-case-study/low-altitude-1500-ft/joby-s4/60-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/joby-s4/60-miles/Joby-S4-1500-60.json"),

        # Supernal S-A2
        ("../../cfg-case-study/low-altitude-1500-ft/supernal/30-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/supernal/30-miles/Supernal-S-A2-1500-30.json"),
        ("../../cfg-case-study/low-altitude-1500-ft/supernal/45-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/supernal/45-miles/Supernal-S-A2-1500-45.json"),
        ("../../cfg-case-study/low-altitude-1500-ft/supernal/60-miles/",
         "../../cfg-case-study/low-altitude-1500-ft/supernal/60-miles/Supernal-S-A2-1500-60.json"),
    ]

    # Run all active cases
    for base_dir, config in cases:
        run_case(base_dir, config)


if __name__ == "__main__":
    main()
