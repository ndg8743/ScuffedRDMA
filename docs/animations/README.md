# README animations

Manim Community scenes behind the GIFs in the top-level README. One scene per thesis section.

| Scene | File | GIF |
|---|---|---|
| `S00Overview` | `s01_problem.py` | `docs/media/00_overview.gif` |
| `S01Traffic` | `s01_problem.py` | `docs/media/01_traffic.gif` |
| `S02HeadOfLine` | `s01_problem.py` | `docs/media/02_headofline.gif` |
| `S03Landscape` | `s01_problem.py` | `docs/media/03_landscape.gif` |
| `S04DualPool` | `s02_transport.py` | `docs/media/04_dualpool.gif` |
| `S05BlobChannel` | `s02_transport.py` | `docs/media/05_blobchannel.gif` |
| `S06Completion` | `s02_transport.py` | `docs/media/06_completion.gif` |
| `S07Connector` | `s02_transport.py` | `docs/media/07_connector.gif` |
| `S08WFA` | `s03_algorithms.py` | `docs/media/08_wfa.gif` |
| `S09Policy` | `s03_algorithms.py` | `docs/media/09_policy.gif` |
| `S10PMP` | `s03_algorithms.py` | `docs/media/10_pmp.gif` |
| `S11ScuffedQuant` | `s03_algorithms.py` | `docs/media/11_scuffedquant.gif` |
| `S12Storage` | `s03_algorithms.py` | `docs/media/12_storage.gif` |

`style.py` holds the palette (orange hot, blue cold, violet spill, green ok, red stall), captions and box helpers.

## Render

```bash
pip install manim            # Manim Community; needs cairo, pango, ffmpeg, LaTeX with dvisvgm
bash docs/animations/render.sh                    # all scenes: 960x540 @ 15 fps -> 800 px, 12 fps GIF
bash docs/animations/render.sh S10PMP             # one scene
QUALITY=preview bash docs/animations/render.sh    # fast low-res check, no GIFs
```

Text uses the Inter font when installed. Build output goes to `docs/animations/build/` (ignored by git).

## What the numbers are

Sizes and wire times are arithmetic (Granite 3.3-2B KV shape, 10 Gb/s line rate). The scuffedQuant overlap and the NVMe coalescing sweep come from `benchmarks/results/`. The PMP queue values are illustrative and say so on screen. Nothing in these scenes is a transport measurement; those come from notebooks 01 to 03 and 06.
