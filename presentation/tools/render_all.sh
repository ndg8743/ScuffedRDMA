#!/bin/sh
# Renders every animation of the deck, then records their lengths. Log: render_all.log beside this script.
here=$(cd "$(dirname "$0")" && pwd)
R="$here/render.sh"
L="$here/render_all.log"
: > "$L"
run() { echo "== $3" >> "$L"; "$R" "$1" "$2" "$3" "$4" >> "$L" 2>&1; }
run m1_attention.py M1Attention m1_attention
run m2_cache.py M2aCacheRows m2a_cache_rows
run m2_cache.py M2bCacheSize m2b_cache_size
run m3_hol.py M3HeadOfLine m3_head_of_line
run m4_hadamard.py M4Hadamard m4_hadamard
run m5_rotation.py M5Rotation m5_rotation
run m6_quant.py M6Quantize m6_quantize
run m7_classifier.py M7Classifier m7_classifier
run m8_phase.py M8PhaseDetector m8_phase_detector
run m9_credits.py M9Credits m9_credits
run m10_controller.py M10Controller m10_controller
run h1_amdahl_dig.py H1AmdahlDig h1_amdahl_dig
run t0_title.py T0Title t0_title 1600,200
python3 "$here/durations.py" >> "$L" 2>&1
echo ALLDONE >> "$L"
