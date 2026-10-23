#!/usr/bin/env bash
# Render README animations: manim (1280x720 @ 30 fps) -> mp4 -> GIF in docs/media/
# (1280 px, 20 fps, played SPEED x faster than authored, gifsicle-optimized).
#   bash docs/animations/render.sh                 # all scenes
#   bash docs/animations/render.sh S02HeadOfLine   # one scene
#   QUALITY=preview bash docs/animations/render.sh # fast low-res check, no GIF
# Needs: pip install manim (Community), ffmpeg, gifsicle, a LaTeX install with dvisvgm, Inter font (falls back if missing).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/../media"; BUILD="${BUILD:-$HERE/build}"
mkdir -p "$OUT" "$BUILD"
GIF_W="${GIF_W:-1280}"; GIF_FPS="${GIF_FPS:-20}"; SPEED="${SPEED:-1.35}"
declare -A FILE=(
  [S00Overview]=s01_problem.py [S01Traffic]=s01_problem.py [S02HeadOfLine]=s01_problem.py [S03Landscape]=s01_problem.py
  [S04DualPool]=s02_transport.py [S05BlobChannel]=s02_transport.py [S06Completion]=s02_transport.py [S07Connector]=s02_transport.py
  [S01KVCache]=s04_kv_and_compression.py [S11Compare]=s04_kv_and_compression.py
  [S08WFA]=s03_algorithms.py [S09Policy]=s03_algorithms.py [S10PMP]=s03_algorithms.py [S11ScuffedQuant]=s03_algorithms.py [S12Storage]=s03_algorithms.py
)
ORDER=(S00Overview S01KVCache S01Traffic S02HeadOfLine S03Landscape S04DualPool S05BlobChannel S06Completion S07Connector S08WFA S09Policy S10PMP S11ScuffedQuant S11Compare S12Storage)
[[ $# -gt 0 ]] && ORDER=("$@")
cd "$HERE"
for s in "${ORDER[@]}"; do
  f="${FILE[$s]}"
  if [[ "${QUALITY:-}" == preview ]]; then
    manim -q l --progress_bar none --media_dir "$BUILD" --disable_caching "$f" "$s" >/dev/null
    continue
  fi
  manim -r 1280,720 --fps 30 --progress_bar none --media_dir "$BUILD" --disable_caching -o "$s" "$f" "$s" >/dev/null
  mp4="$(find "$BUILD/videos" -path "*720p30*" -name "$s.mp4" | head -1)"
  name="$(echo "$s" | sed -E 's/^S([0-9]+)(.*)/\1_\2/' | tr 'A-Z' 'a-z')"
  ffmpeg -loglevel error -y -i "$mp4" -vf "setpts=PTS/$SPEED,fps=$GIF_FPS,scale=$GIF_W:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" "$BUILD/$name.raw.gif"
  if command -v gifsicle >/dev/null; then gifsicle -O3 --lossy=30 "$BUILD/$name.raw.gif" -o "$OUT/$name.gif"; else cp "$BUILD/$name.raw.gif" "$OUT/$name.gif"; fi
  printf '%-18s %s  %s\n' "$s" "$(du -h "$OUT/$name.gif" | cut -f1)" "$OUT/$name.gif"
done
