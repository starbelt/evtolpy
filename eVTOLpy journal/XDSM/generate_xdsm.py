from pyxdsm.XDSM import XDSM, OPT, SOLVER, FUNC, LEFT

x = XDSM(use_sfmath=True)

# Diagonal Systems
x.add_system('mass_sizing', SOLVER, (r'\text{Mass Sizing}', r'\text{Loop}'))
x.add_system('geom', FUNC, (r'\text{Aircraft}', r'\text{Geometry}'))
x.add_system('mass', FUNC, (r'\text{Aircraft}', r'\text{Mass}'))
x.add_system('env', FUNC, 'Env')
x.add_system('aero', FUNC, 'Aero')
x.add_system('prop', FUNC, 'Prop')
x.add_system('power', FUNC, 'Power')
x.add_system('bat_siz', FUNC, (r'\text{Battery}', r'\text{Size}'))
x.add_system('togw', FUNC, (r'\text{TOGW}', r'\text{Calc}'))

# Inputs
x.add_input('mass_sizing', r'W_{TO}^{(0)}')
x.add_input('geom', 'Geom')
x.add_input('env', 'Profile')

# Feedforward Connections
x.connect('mass_sizing', 'mass', 'W_{TO}')
x.connect('geom', 'mass', ' ')
x.connect('mass', 'env', ' ')
x.connect('mass', 'togw', 'm_{struct}')

x.connect('env', 'aero', ' ')
x.connect('env', 'prop', ' ')
x.connect('env', 'power', ' ')

x.connect('aero', 'prop', ' ')
x.connect('aero', 'power', ' ')

x.connect('prop', 'power', ' ')

x.connect('power', 'bat_siz', r'\text{Power \& Energy}')
x.connect('bat_siz', 'togw', 'm_{batt}')

# Feedback Connections
x.connect('togw', 'mass_sizing', ' ')

# PDF
x.write('eVTOLpy journal/XDSM/figures/evtolpy_architecture', build=False, cleanup=False)

# Override tikz styles AFTER the pyxdsm diagram_styles.tex is loaded so the
# native PDF is compact enough that, when included at width=7in in LaTeX,
# every glyph still renders at >= 8 pt.
_tikz = 'eVTOLpy journal/XDSM/figures/evtolpy_architecture.tikz'
with open(_tikz, 'r') as _f:
    _content = _f.read()
_inject = (
    r'\tikzstyle{MatrixSetup} = [row sep=0.5mm, column sep=0.7mm]' + '\n'
    + r'\tikzset{every node/.append style={font=\small}}' + '\n'
    + r'\usetikzlibrary{fit, backgrounds}' + '\n'
    + r'\pgfdeclarelayer{background}' + '\n'
    + r'\pgfsetlayers{background,data,process,main}' + '\n'
)
_content = _content.replace(
    r'\begin{tikzpicture}',
    r'\begin{tikzpicture}' + '\n' + _inject,
)

_content = _content.replace(
    r'\node [DataInter] (power-bat_siz) {$\text{Power \& Energy}$};',
    r'\hspace{120pt} \node [DataInter, xshift=30mm] (power-bat_siz) {$\text{Power \& Energy}$};'
)

_content = _content.replace(
    r'\node [Function] (bat_siz)',
    r'\node [Function, xshift=30mm] (bat_siz)'
)


_mission_box_tikz = r"""
\begin{pgfonlayer}{background}
\node[draw, dashed, fill=white, inner sep=15pt, fit=(env) (aero) (prop) (power), xshift=5pt, yshift=-5pt] (mission_box_2) {};
\node[draw, dashed, fill=white, inner sep=15pt, fit=(env) (aero) (prop) (power)] (mission_box_1) {};
\node[anchor=center, fill=white, inner sep=4pt, font=\small] at (mission_box_1.north) {Mission};
\node[anchor=west, inner sep=4pt, font=\small] at (mission_box_2.east) {\# segments};
\end{pgfonlayer}
"""
_content = _content.replace(
    '};\n\n% XDSM process chains',
    '};\n\n' + _mission_box_tikz + '\n\n% XDSM process chains'
)

_content = _content.replace(
    r'(power) edge [DataLine] (power-bat_siz)',
    r'(mission_box_2.east |- power-bat_siz) edge [DataLine] (power-bat_siz)'
)

_content = _content.replace(
    r'(env) edge [DataLine] (output_env)',
    r'(output_env |- mission_box_1.north) edge [DataLine] (output_env)'
)

_content = _content.replace(
    r'(mass-env) edge [DataLine] (env)',
    r'(mass-env) edge [DataLine] (mass-env |- mission_box_1.north)'
)

_content = _content.replace(
    '\\node [DataInter] (mass-togw) {$m_{struct}$};&\n\\\\',
    '\\node [DataInter] (mass-togw) {$m_{struct}$};&\n\\\\[10mm]'
)

_content = _content.replace(
    '%Row 1',
    '\\\\[3mm]\n%Row 1'
)
_content = _content.replace(
    '\\\\\n\\\\[3mm]',
    '\\\\[3mm]'
)

with open(_tikz, 'w') as _f:
    _f.write(_content)

_tex = 'eVTOLpy journal/XDSM/figures/evtolpy_architecture.tex'
with open(_tex, 'r') as _f:
    _tex_content = _f.read()
_tex_content = _tex_content.replace(
    r'\input{"eVTOLpy journal/XDSM/figures/evtolpy_architecture.tikz"}',
    r'\input{"evtolpy_architecture.tikz"}'
)
# We also want to replace the original 'paper/evtolpy_architecture.tikz' just in case
_tex_content = _tex_content.replace(
    r'\input{"paper/evtolpy_architecture.tikz"}',
    r'\input{"evtolpy_architecture.tikz"}'
)
with open(_tex, 'w') as _f:
    _f.write(_tex_content)

import subprocess
import os

_tectonic_path = None
if os.path.exists("./tectonic"):
    _tectonic_path = "./tectonic"
elif os.path.exists("../evtolpy_priv/tectonic"):
    _tectonic_path = "../evtolpy_priv/tectonic"
else:
    import shutil
    _tectonic_path = shutil.which("tectonic")

if _tectonic_path:
    try:
        print(f"Compiling PDF with {_tectonic_path}...")
        subprocess.run([_tectonic_path, "eVTOLpy journal/XDSM/figures/evtolpy_architecture.tex"], check=True)
        print("PDF generated successfully.")
        
        # Convert PDF to PNG using macOS sips tool
        subprocess.run(["sips", "-s", "format", "png", "eVTOLpy journal/XDSM/figures/evtolpy_architecture.pdf", "--out", "eVTOLpy journal/XDSM/figures/evtolpy_architecture.png"], check=True)
        
        # Convert PDF to EPS using cupsfilter and sed
        with open("eVTOLpy journal/XDSM/figures/evtolpy_architecture.ps", "w") as ps_file:
            subprocess.run(["cupsfilter", "-m", "application/postscript", "eVTOLpy journal/XDSM/figures/evtolpy_architecture.pdf"], stdout=ps_file, stderr=subprocess.DEVNULL, check=True)
        
        subprocess.run(["sed", "-i", "", "1s/.*/%!PS-Adobe-3.0 EPSF-3.0/", "eVTOLpy journal/XDSM/figures/evtolpy_architecture.ps"], check=True)
        subprocess.run(["mv", "eVTOLpy journal/XDSM/figures/evtolpy_architecture.ps", "eVTOLpy journal/XDSM/figures/evtolpy_architecture.eps"], check=True)        
    except Exception as e:
        print(f"Error during compilation or conversion: {e}")
else:
    print("Tectonic binary not found. Skipping PDF, PNG, and EPS generation.")
