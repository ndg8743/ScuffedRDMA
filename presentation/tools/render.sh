#!/bin/sh
# render.sh file.py Scene name [w,h]
#   -> assets/clips/name.mp4 (20 fps), name.gif (10 fps, loops forever, lossless palette), name.first.png, name.last.png
# Needs: manim (Community edition), a LaTeX installation, ffmpeg.
set -e
here=$(cd "$(dirname "$0")" && pwd)
root=$(dirname "$here")
cd "$root/manim"
f="$1"; scene="$2"; name="$3"; res="${4:-1280,720}"
manim -r "$res" --fps 20 --format mp4 --media_dir media "$f" "$scene" 2>&1 | grep -E "Error|Traceback|line [0-9]+, in" || true
src=$(ls -t media/videos/$(basename "$f" .py)/*/"$scene".mp4 | head -1)
out="$root/assets/clips"
mkdir -p "$out"
cp "$src" "$out/$name.mp4"
ffmpeg -loglevel error -y -i "$out/$name.mp4" -vf "fps=10,split[a][b];[a]palettegen=max_colors=${COLORS:-64}:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" -loop 0 "$out/$name.gif"
ffmpeg -loglevel error -y -i "$out/$name.mp4" -frames:v 1 "$out/$name.first.png"
ffmpeg -loglevel error -y -sseof -0.3 -i "$out/$name.mp4" -frames:v 1 "$out/$name.last.png"
ls -la "$out/$name.mp4" "$out/$name.gif" | awk '{print $5, $9}'
