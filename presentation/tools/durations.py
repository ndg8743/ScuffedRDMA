#!/usr/bin/env python3
"""Writes assets/clips/durations.json: the length of one pass of each animation in seconds (read by the deck generator
for the presenter notes). Needs ffprobe."""
import glob, json, os, subprocess
here = os.path.dirname(os.path.abspath(__file__))
clips = os.path.join(os.path.dirname(here), "assets", "clips")
out = {}
for f in sorted(glob.glob(os.path.join(clips, "*.mp4"))):
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
    out[os.path.basename(f)[:-4]] = round(float(d), 1)
json.dump(out, open(os.path.join(clips, "durations.json"), "w"), indent=1)
print(out)
