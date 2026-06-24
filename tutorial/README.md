# Tutorial

This directory contains Jupyter tutorial notebooks aligned with the case-study subsections. All notebooks use the Archer Midnight as the reference vehicle.

## Directory Contents

* [README.md](README.md): This document
* [Archer_Midnight.json](Archer_Midnight.json): Reference Archer Midnight aircraft configuration file used by the tutorial notebooks
* [01_Getting-started](01_Getting-started/README.md): Introductory notebooks for inspecting the `eVTOLpy` aircraft object and loading aircraft configurations from JSON files
* [02_Aircraft-Config](02_Aircraft-Config/README.md): Notebooks for aircraft geometry parameters, derived quantities, fixed mass inputs, and custom configuration settings
* [03_Mission-Profiles](03_Mission-Profiles/README.md): Notebooks for defining primary and reserve mission segments and modifying mission timeline parameters
* [04_Mass-and-Weight-Analysis](04_Mass-and-Weight-Analysis/README.md): Notebooks for component-level mass breakdown and iterative MTOW convergence analysis
* [05_Power-and-Energy-Analysis](05_Power-and-Energy-Analysis/README.md): Notebooks for segment power, electric power, power-chain losses, and mission energy consumption
* [06_Aerodynamics](06_Aerodynamics/README.md): Notebooks for component drag buildup and aerodynamic contribution analysis
* [07_Propulsion](07_Propulsion/README.md): Notebooks for rotor disk loading, solidity, EPU mass, battery energy density, and usable battery energy
* [08_Archer-Midnight-Sizing](08_Archer-Midnight-Sizing/README.md): Notebooks for the final Archer Midnight sizing case, convergence dashboard, and range/altitude design-space study
* [09_Miscellaneous](09_Miscellaneous/README.md): Additional scripted examples and utility demonstrations

## Tutorial Notebook Map

| Sec. | Notebook | Topic | Key Visualization |
|---|---|---|---|
| 01 | eVTOLpy | Inspect properties and class structure | 3-panel summary: geometry, aero, power |
| 01 | JSON Configuration | Load aircraft config from JSON | Parameter-count bar chart |
| 02 | Geometry | Geometry parameters and derived quantities | Planform schematic + component areas |
| 02 | Fixed Mass | Mass component inputs and custom configs | Pie chart + fixed/calculated bar chart |
| 03 | Mission Segments | Primary and reserve mission segments | Velocity/altitude profile |
| 03 | Mission Timeline | Modify mission parameters | Duration / power / energy bubble chart |
| 04 | Mass Breakdown | Component-level mass breakdown | Stacked bar by category |
| 04 | MTOW Iteration | Iterative MTOW convergence | Convergence history |
| 05 | Segment Power | Shaft power, electric power, power chain | Shaft/electric bars + EPU losses |
| 05 | Power and Energy | Power profiles and energy consumption | Step profile + reserve stacked bar |
| 06 | Drag Buildup | Component drag buildup method | Horizontal bar of drag contributions |
| 07 | Rotor and EPU | Rotor disk loading, solidity, EPU mass | Propulsion mass bar |
| 07 | Battery Sizing | Battery energy density and usable energy | Derating waterfall |
| 08 | Vehicle Overview | Final sized Archer Midnight | 4-panel dashboard |
| 08 | Sizing Convergence | Full MTOW convergence run | Convergence + mass + energy |
| 08 | Range/Altitude Study | Six-case mission design space | MTOW, energy, battery vs. range |
| 09 | Miscellaneous | Additional scripted examples | No interactive plots |