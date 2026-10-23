"""
Helpers to generate the research notebooks from plain Python, so they stay
diffable. Each make_*.py builds one notebook with nbformat.

Conventions every notebook follows:
  - First code cell is the parameter cell (tagged "parameters" for papermill):
      MODE = "local"   # "local": smoke sizes on any Linux box, results to /tmp
                       # "cluster": real runs on Chimera/Cerberus, results to benchmarks/results/
  - A setup cell finds the repo root and puts it on sys.path.
  - Cluster-mode results are JSON tagged with hostname and UTC timestamp.
  - Local-mode numbers are smoke tests, never thesis results.
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
print("repo:", ROOT, "| host:", HOST, "| mode:", MODE, "| results ->", RESULTS)'''


def build(path, title, intro, params, cells):
    """cells: list of ("md", text) or ("code", text)."""
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.cells.append(nbf.v4.new_markdown_cell(f"# {title}\n\n{intro}"))
    pc = nbf.v4.new_code_cell(params)
    pc.metadata["tags"] = ["parameters"]
    nb.cells.append(pc)
    nb.cells.append(nbf.v4.new_code_cell(SETUP))
    for kind, src in cells:
        nb.cells.append(nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src))
    out = ROOT / "notebooks" / path
    nbf.write(nb, out)
    return out
