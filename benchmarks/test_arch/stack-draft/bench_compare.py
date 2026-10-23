#!/usr/bin/env python3
"""Compare ScuffedRDMA vs UCCL results from test_arch JSON files."""
import json, glob, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import results_dir

def main():
    rd = results_dir()
    files = sorted(rd.glob("*.json"))
    if not files:
        print(f"No results in {rd}")
        return

    print(f"\n{'File':<50} {'Model/Type':<25}")
    print("-" * 75)
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        tag = data.get("model", data.get("type", "unknown"))
        print(f"{f.name:<50} {tag:<25}")

    print(f"\n{len(files)} result files in {rd}")

if __name__ == "__main__":
    main()
