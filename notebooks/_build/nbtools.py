"""
Helpers to generate the research notebooks from plain Python, so they stay
diffable. Each make_*.py builds one notebook with nbformat.

Conventions every notebook follows:
  - First code cell is the parameter cell (tagged "parameters" for papermill):
      MODE = "local"   # "local": smoke sizes on any Linux box, results to /tmp
                       # "cluster": real runs on server 1 / server 2, results to benchmarks/results/
  - A setup cell finds the repo root and puts it on sys.path, sets the figure
    style, and defines fig(name) which saves every figure for the paper:
      docs/figures/<name>.png|.pdf          model figures: arithmetic, proofs, repo results
      docs/figures/<MODE>/<name>.png|.pdf   measured figures: depend on the machine the notebook ran on
  - Cluster-mode results are JSON tagged with hostname and UTC timestamp.
  - Local-mode numbers are smoke tests, never thesis results.
  - Each notebook opens with a "Math" cell: the formulas it checks, mirroring
    the matching page in docs/explained/.
"""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SETUP = '''import os, sys, json, socket, subprocess, time
from pathlib import Path
ROOT = Path.cwd()
while not (ROOT / "middleware").is_dir() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
HOST = socket.gethostname()
STAMP = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
RESULTS = (ROOT / "benchmarks" / "results" / RESULTS_SUBDIR) if MODE == "cluster" else Path("/tmp/scuffed-local") / RESULTS_SUBDIR
RESULTS.mkdir(parents=True, exist_ok=True)
FIGDIR = ROOT / "docs" / "figures"
(FIGDIR / MODE).mkdir(parents=True, exist_ok=True)

import matplotlib
import matplotlib.pyplot as plt
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 170, "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 7.5, "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "lines.linewidth": 1.4,
    "lines.markersize": 4, "figure.constrained_layout.use": False})
C = {"hot": "#f97316", "cold": "#38bdf8", "spill": "#a78bfa", "ok": "#34d399", "bad": "#f43f5e",
     "gold": "#facc15", "ink": "#1f2937", "muted": "#94a3b8"}

def fig(name, model=False, caption=None, f=None):
    """Save the current figure as PNG + PDF and show it.
    model=True: arithmetic or repo results, same on every machine -> docs/figures/<name>
    model=False: measured on this machine -> docs/figures/<MODE>/<name>"""
    f = f or plt.gcf()
    d = FIGDIR if model else FIGDIR / MODE
    f.tight_layout()
    for ext in ("png", "pdf"):
        f.savefig(d / f"{name}.{ext}", bbox_inches="tight")
    print(f"figure -> {d.relative_to(ROOT)}/{name}.png" + (f"  |  {caption}" if caption else ""))
    plt.show()

def save(name, obj):
    p = RESULTS / f"{HOST}_{name}.json"
    obj = {"host": HOST, "utc": STAMP, "mode": MODE, **obj}
    p.write_text(json.dumps(obj, indent=2, default=str))
    print("wrote", p)
    return p

def sh(cmd, check=True):
    print("$", cmd)
    r = subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=ROOT)
    print(r.stdout[-4000:], r.stderr[-2000:])
    if check and r.returncode:
        raise RuntimeError(f"{cmd} -> {r.returncode}")
    return r
print("repo:", ROOT, "| host:", HOST, "| mode:", MODE, "| results ->", RESULTS, "| figures ->", FIGDIR)'''


def build(path, title, intro, params, cells, sections=None):
    """cells: list of ("md", text) or ("code", text).
    sections: list of (number, title, explained-page) this notebook covers; rendered under the title."""
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    head = f"# {title}\n\n{intro}"
    if sections:
        head += "\n\n**README sections covered:** " + ", ".join(
            f"[{n}. {t}](../docs/explained/{p})" for n, t, p in sections)
        head += "\n\nFigures are written to `docs/figures/` (model figures: arithmetic, proofs and repo results) and `docs/figures/<MODE>/` (measured on the machine that ran the notebook)."
    nb.cells.append(nbf.v4.new_markdown_cell(head))
    pc = nbf.v4.new_code_cell(params)
    pc.metadata["tags"] = ["parameters"]
    nb.cells.append(pc)
    nb.cells.append(nbf.v4.new_code_cell(SETUP))
    for kind, src in cells:
        nb.cells.append(nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src))
    out = ROOT / "notebooks" / path
    nbf.write(nb, out)
    return out
