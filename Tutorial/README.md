# evtolpy Tutorials

These tutorials walk through the `evtolpy` framework for eVTOL aircraft conceptual design, sizing, and performance analysis. All tutorials use the **Archer Midnight** as the reference vehicle.
## How to Use

Work through the folders and notebooks in ascending order. Each folder focuses on a specific topic and contains Jupyter notebooks that build on previous concepts. Read any `README.md` files within each folder before proceeding.

Each notebook is designed to be self-contained.

## Prerequisites

- Python 3.8+
- Jupyter Notebook or JupyterLab
- `matplotlib` (for plotting tutorials)

## Tutorial Outline

| Folder | Topic | Description |
|--------|-------|-------------|
| `01 - Getting Started` | Basics | Loading a configuration, creating an Aircraft object, and inspecting properties |
| `02 - Aircraft Configuration` | Configuration | Understanding JSON input files and aircraft parameters |
| `03 - Mission Profiles` | Mission | Defining and exploring mission segments |
| `04 - Mass and Weight Analysis` | Weight | MTOW iteration, mass breakdown, and component mass estimation |
| `05 - Power and Energy Analysis` | Energy | Mission segment power and energy calculations |
| `06 - Aerodynamics` | Aero | Drag buildup, lift-to-drag ratio, and Reynolds number |
| `07 - Propulsion and Battery` | Propulsion | Rotor sizing, battery modeling, and EPU estimation |
| `08 - Archer Midnight Sizing` | Case Study | Sizing the Archer Midnight across mission ranges and altitudes |
| `09 - Miscellaneous` | Advanced | Comparative studies, sensitivity analysis, and custom configurations |
