# evtolpy: A Design and Simulation Framework for eVTOL Aircraft

`evtolpy` is a Python-based modeling framework for sizing, performance analysis,
and mission-level simulation of electric vertical takeoff and landing (eVTOL)
aircraft. The software evaluates vehicle aerodynamics, rotorcraft performance,
subsystem masses, battery requirements, and mission energy consumption using an
extensible set of physics-based methods combined with empirical mass
regressions.  

License: MIT License

## Overview

The framework is mission-driven: given a vehicle configuration and a sequence of
flight segments, `evtolpy` computes shaft power, electric power, and energy for
each segment; iteratively updates vehicle mass properties; and converges on a
consistent maximum takeoff weight (MTOW). The tool supports comparative studies
across aircraft architectures, propulsion layouts, battery technologies, and
mission definitions.

The `evtolpy` simulator accepts JSON-based inputs describing aircraft geometry
(e.g., wingspan, fuselage dimensions, rotor diameter), aerodynamic and drag-related
properties, propulsion system characteristics (e.g., rotor count, thrust and
power coefficients, efficiency parameters), mission definitions (e.g., segment
speeds, durations, and vertical profiles), battery cell and pack properties
(e.g., specific energy, accessible energy fraction, pack integration factor),
and relevant environmental conditions such as air density and atmospheric
viscosity. A complete list of input parameters is provided in the
[`sample-inputs`](sample-inputs/README.md) directory.

This repository also includes source code implementing the Autonomous Battery
Units (ABU) concept introduced in the AIAA SciTech Forum 2026 paper  
**“Autonomous Battery Units as an Enabling Technology for Urban Air Mobility.”**

## Key Features

- Mission-based energy and power simulation
- Iterative aircraft sizing loop for MTOW, battery mass, and structural and
  subsystem mass estimation
- Aerodynamic and rotor performance models based on NASA’s NDARC rotorcraft
  design database
- Configurable inputs for geometry, aerodynamics, propulsion, environment, and
  battery characteristics
- Modular Python package suitable for research, teaching, and early-stage
  conceptual design of eVTOL aircraft

## Requirements
- Python 3.x
- matplotlib  

## Directory Contents

* [analysis](analysis/README.md): Analysis scripts and study workflows
* [docs](docs/README.md): Framework documentation and methodology notes
* [evtol](evtol/README.md): Core Python package
* [references](references/README.md): Supporting reference materials and
  technical sources
* [sample-inputs](sample-inputs/README.md): Example configuration files for
  testing and demonstrations
* [tests](tests/README.md): Package unit tests
* [README.md](README.md): This document

## Quick Start Guide

Analysis scripts are organized by study type within the `analysis/` directory.
Each analysis follows a similar workflow consisting of a logging step followed
by a plotting step.

The simulator is driven by a JSON input file that defines both the aircraft
configuration and mission parameters. In the examples below, `test-all.json`
specifies vehicle geometry, aerodynamic and propulsion properties, battery
characteristics, and the sequence of mission segments. Users may modify this
file to define custom aircraft configurations and mission profiles. This JSON
file serves as the primary input to the `evtolpy` simulator.

### 1. Mission Energy Analysis
```
cd analysis/mission-segment-energy/src
python log_mission_segment_energy.py ../cfg/test-all.json ../log/
python plt_mission_segment_energy.py ../log/mission-segment-energy.csv ../plt/
```

### 2. Mission Power Analysis
```
cd analysis/mission-segment-power/src
# Follow similar logging and plotting steps as above
```

### 3. Aircraft Weight Analysis
```
cd analysis/mission-segment-weight/src
# Follow similar logging and plotting steps as above
```

### 4. Autonomous Battery Unit (ABU) Analysis
```
cd analysis/mission-segment-abu-analysis/src
# Follow similar logging and plotting steps as above
```

## Citing evtolpy
This repository may be cited using the following BibTeX entry:
```
@software{evtolpy2026,
  author = {Nguyen, Khoa D. and Hogge, Dylan and Riris, John and Sarojini, Darshan and Denby, Bradley},
  title  = {evtolpy: A Design and Simulation Framework for eVTOL Aircraft},
  url    = {https://github.com/starbelt/evtolpy},
  year   = {2026}
}
```

The most recent publication introducing evtolpy and the ABU framework was
presented at the AIAA SciTech Forum 2026 and may be cited as:
```
@inproceedings{nguyen2026autonomous,
  title     = {Autonomous Battery Units as an Enabling Technology for Urban Air Mobility},
  author    = {Nguyen, Khoa D. and Hogge, Dylan and Riris, John and Sarojini, Darshan and Denby, Bradley},
  booktitle = {AIAA SciTech 2026 Forum},
  year      = {2026},
  doi       = {},
  url       = {}
}
```