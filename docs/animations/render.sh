#!/usr/bin/env bash
# Render README animations: manim -> mp4 -> palette GIF in docs/media/.
#   bash docs/animations/render.sh                 # all scenes
#   bash docs/animations/render.sh S02HeadOfLine   # one scene
#   QUALITY=preview bash docs/animations/render.sh # fast low-res check, no GIF
# Needs: pip install manim (Community), ffmpeg, a LaTeX install with dvisvgm, Inter font (falls back if missing).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/../media"; BUILD="${BUILD:-$HERE/build}"
mkdir -p "$OUT" "$BUILD"
GIF_W="${GIF_W:-800}"; GIF_FPS="${GIF_FPS:-12}"
declare -A FILE=(
  [S00Overview]=s01_problem.py [S01Traffic]=s01_problem.py [S02HeadOfLine]=s01_problem.py [S03Landscape]=s01_problem.py
  [S04DualPool]=s02_transport.py [S05BlobChannel]=s02_transport.py [S06Completion]=s02_transport.py [S07Connector]=s02_transport.py
  [S08WFA]=s03_algorithms.py [S09Policy]=s03_algorithms.py [S10PMP]=s03_algorithms.py [S11ScuffedQuant]=s03_algorithms.py [S12Storage]=s03_algorithms.py
)
ORDER=(S00Overview S01Traffic S02HeadOfLine S03Landscape S04DualPool S05BlobChannel S06Completion S07Connector S08WFA S09Policy S10PMP S11ScuffedQuant S12Storage)
[[ $# -gt 0 ]] && ORDER=("$@")
cd "$HERE"
for s in "${ORDER[@]}"; do
  f="${FILE[$s]}"
  if [[ "${QUALITY:-}" == preview ]]; then
    manim -q l --progress_bar none --media_dir "$BUILD" --disable_caching "$f" "$s" >/dev/null
    continue
  fi
  manim -r 960,540 --fps 15 --progress_bar none --media_dir "$BUILD" --disable_caching -o "$s" "$f" "$s" >/dev/null
  mp4="$(find "$BUILD/videos" -name "$s.mp4" | head -1)"
  name="$(echo "$s" | sed -E 's/^S([0-9]+)(.*)/\1_\2/' | tr 'A-Z' 'a-z')"
  ffmpeg -loglevel error -y -i "$mp4" -vf "fps=$GIF_FPS,scale=$GIF_W:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" "$OUT/$name.gif"
  printf '%-18s %s  %s\n' "$s" "$(du -h "$OUT/$name.gif" | cut -f1)" "$OUT/$name.gif"
done
