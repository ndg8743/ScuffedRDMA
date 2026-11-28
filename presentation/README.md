# Thesis defense presentation

Slides for the defense of the M.S. thesis "Adaptive RDMA Middleware for Disaggregated LLM Inference over
Commodity Ethernet" (Nathan Gopee, SUNY New Paltz, December 2026), with everything they are built from.

| File | What it is |
|---|---|
| `thesis-defense.pptx` | The deck: 166 slides (147 in the talk, 19 backup slides), 16:9, speaker notes on every slide, 18 looping animations |
| `thesis-defense-handout.pdf` | The same slides as a tagged PDF, with a still frame in place of every animation |

This is version 10 of the deck, built on November 27, 2026. It follows version 14 of the thesis draft, which is
the draft in `thesis/`. Slide 67 and the remarks on the verbs provider on slides 68 and 162 describe the blob
channel after the fix of November 26 (commits 9ae6c93, 0c4c93e and 5b0e9a7).

Version 10 adds two slides in part VII: TurboQuant as Google presents it (93), and our quantizer with what
differs (94). Slide 92 now says "the scheme of TurboQuant: rotate a vector, then round each coordinate" where
it said "the rotation and the scalar quantizer of TurboQuant", because our rotation is built differently. See
"TurboQuant and ours" below. Every slide after 92 has moved by two.

Version 9 adds ten slides. Four are pictures from everyday life that stand before a proof (see below), and
six are on NUMA (72 to 77), which follow section 5.6 of the thesis: where the registered memory of the pool
lies on a server with two processor sockets, what a NUMA-aware pool would do, and why this cannot be measured
on the four servers. Like the thesis, they describe a design that is not implemented.

## The talk

| Part | Slides |
|---|---|
| Opening | 1 to 5 |
| I. The moving bottleneck | 6 to 14 |
| II. A language model and its cache | 15 to 24 |
| III. The problem | 25 to 42 |
| IV. RDMA at a low level | 43 to 54 |
| V. The middleware | 55 to 77 |
| VI. Decisions per transfer | 78 to 90 |
| VII. Compression and storage | 91 to 104 |
| VIII. Testbed and method | 105 to 121 |
| IX. Results | 122 to 133 |
| X. Conclusions | 134 to 147 |
| Backup slides | 148 to 166 |

Every part is linked from the Outline (slide 5) and from the footer of each slide. The backup slides are reached
through the Proof and Detail buttons, and Back returns to the slide that was shown before.

Read in full, the speaker notes take about 59 minutes at 130 words a minute. Without parts I and IV, the five
completion signals (68), the NUMA details (73 to 76), the rule tree (86, 87), the storage tier (103, 104) and
the related work (135, 136), about 45 minutes remain. `node tools/deck/words.js` prints both figures and the
length of each part. A paragraph of the notes that starts with "For questions:" is kept for a question from
the audience and is not counted (slides 93 and 94 have one).

## Pictures from everyday life

Six slides explain a hard point with a picture before the slide that states it. Each is one animation with a
legend that says what stands for what, and each is marked as an illustration under the picture.

| Slide | Picture | It prepares |
|---|---|---|
| 10 | one hole, ten workers, one or ten shovels | Amdahl's law (9) |
| 21 | a bank statement: a new line changes no earlier balance | Proposition 2.1 (22) |
| 34 | a post office: one letter behind customers with forty parcels | the three waits of the queueing model (35) |
| 64 | eight parcel lockers, a courier with one token for each | Propositions 5.1 to 5.4 (65) |
| 72 | two sorting halls and one corridor | the NUMA slides (73 to 77) |
| 97 | a stick along a wall of a room, turned onto the diagonal | the rotation and Lemmas 6.7 and 6.8 (98, 99) |

## TurboQuant and ours (slides 93 and 94)

The two slides have the same three panels at the same places (rotate, round, signs of the error), so that going
from 93 to 94 shows what differs.

| Step | TurboQuant, as on slide 93 | Ours, as on slide 94 |
|---|---|---|
| Rotate | a random rotation matrix (64 by 64 numbers for a vector of 64 coordinates) | a diagonal of 64 random signs, then a Hadamard matrix |
| Round | in polar coordinates: two coordinates become a radius and an angle, the radii are paired again until one is left, and the angles are rounded on a fixed grid | each coordinate to one of eight fixed levels (3 bits), and the length of the vector stored once |
| Signs of the error | one sign per coordinate | 256 signs per vector |

What the slides rest on, each read at the source on November 27, 2026:

- The Google Research post "TurboQuant: Redefining AI efficiency with extreme compression" (March 24, 2026)
  presents TurboQuant in two stages: a random rotation followed by "the PolarQuant method", and one bit of QJL
  for the remaining error. It describes PolarQuant as the conversion to polar coordinates by pairs, repeated on
  the radii until one radius and a set of angles remain. Slide 93 follows this post.
- The TurboQuant paper (Zandieh, Daliri, Hadian and Mirrokni, arXiv 2504.19874, version 1): Algorithm 1 draws a
  rotation matrix from the QR decomposition of a matrix of normal entries and rounds each rotated coordinate to
  the nearest of 2^b levels of a codebook of the Lloyd and Max kind; Algorithm 2 runs it at b - 1 bits and adds
  the signs of a Gaussian projection of the residual, one per coordinate, and the length of the residual. Its
  algorithms use no polar coordinates and no Hadamard matrix, and PolarQuant appears in it as a method it is
  compared with. This is why the note on slide 93 says that in the paper the second step rounds each
  coordinate, and why slide 94 says "as here".
- The PolarQuant paper (Han, Kacham, Karbasi, Mirrokni and Zandieh, arXiv 2502.02617, version 1): the recursive
  polar transformation, d - 1 angles and one radius for d coordinates, a fixed codebook because the distribution
  of the angles is known after the random preconditioning, so that no scale and zero point are stored for a
  block; in practice four levels, with 4 bits for an angle of the first level and 2 bits above.
- Ours is the module `middleware/rdma_tensor_cache/scuffed_quant.py` with the settings of the tests (64
  coordinates, 3 bits, 256 signs, seed 42).

The pictures are computed, with one synthetic vector of 64 coordinates that has three large channels. For
slide 94 the vector goes through the module of this repository. For slide 93 `tools/quant_figures.py` contains
our reading of the published steps (the rotation matrix, the polar transformation with 16 sectors for an angle
of the first level and 2 bits above, and the signs); it was written for the picture and is not the authors'
code. Two seeds were chosen for the look of the pictures and for nothing else, and the script says how: the
first two rotated coordinates sit clear of a grid line, and the largest coordinate after the rotation is about
the same in both pictures (0.26 and 0.25), so that the pictures suggest no difference in quality. The slides
compare how the steps are built. They compare no quality, and the thesis ran no such comparison.

## Still open in the deck

A result that is not measured yet is an empty table cell with a note that starts with a star, for example
"* Waiting for results from E3 (run R2)". The star notes are on slides 1, 67, 77, 90, 106, 107, 113, 123, 125,
128, 130, 131, 132, 137, 138, 139, 154 and 157, and `python3 tools/check2.py thesis-defense.pptx` lists them.

The deck passes `tools/check2.py`, and its slides were looked at through LibreOffice in the variant with still
frames. LibreOffice ran out of memory on the deck itself (it needs more than 6 GB for the eighteen GIFs), so
the moving pictures were checked as rendered frames and not inside the deck. The file has 62 MB; GitHub takes
it and prints a warning for a file above 50 MB. It has not been opened in PowerPoint
yet. Before the defense, run the slide show there once and check that the animations move, that the Back
buttons return, and that the dashed and dotted lines of the chart on slide 9 show. An animated GIF moves in
PowerPoint's slide show; the editing view, previews and the handout show a still picture. Each animation is
also in `assets/clips` as an MP4 file, for a program that does not play GIFs.

## What is here

    thesis-defense.pptx           the deck
    thesis-defense-handout.pdf    the handout
    manim/                the eighteen animations (Manim Community edition 0.22.1)
      style.py            colors, type sizes, caption helper, and the pace of every animation
      grid.py             a matrix drawn as a grid of cells
      figures.py          pictograms and the legend of the pictures from everyday life
      x1_statement.py     slide 21      x2_post_office.py   slide 34      x3_lockers.py   slide 64
      x4_stick.py         slide 97      x5_numa_halls.py    slide 72
    tools/
      render.sh           one animation  -> assets/clips/<name>.gif, .mp4, first and last frame
      render_all.sh       all eighteen, then durations.py
      durations.py        length of one pass of each animation -> assets/clips/durations.json (for the notes)
      formulas.py         the formulas   -> assets/math/<name>.png and manifest.json (sizes, spoken alt text)
      quant_figures.py    the six pictures of slides 93 and 94 -> assets/diagrams/<name>.png and manifest.json
                          (sizes in inches, alt text, the numbers of the example)
      photos.py           the pictures of Updates/Update1-HardwareSetup -> assets/photos (cropped, one leveled,
                          reduced, without camera metadata)
      post.py             theme colors, fade transitions, Back buttons, header rows of tables, paragraph
                          clean-up, and dash styles for the series of a line chart
      check2.py           checks of the built file: titles, notes, alt text, links, wording, smallest type
      deck/               the slide generator (Node, pptxgenjs 4.0.1)
        lib.js            theme, layouts, parts, text and table helpers
        d1_front.js       opening, part I (history), part II (model and cache)
        d2_problem.js     part III (problem, research questions, contributions, scope)
        d3_rdma.js        part IV (RDMA at a low level)
        d4_middleware.js  part V (pool, blob channel, connector, NUMA)
        d5_decisions.js   part VI (classifier, rule tree, controller)
        d6_compression.js part VII (quantizer, storage tier)
        d7_method.js      part VIII (testbed, the firmware work on server 4, method)
        d8_results.js     part IX (results)
        d9_closing.js     part X (related work, answers, limitations, future work, closing)
        d10_backup.js     backup slides
        build.js          writes the deck
        words.js          spoken words in the notes, by part
        theme.json        colors and fonts (Cambria for titles, Calibri for text)
        metrics.json      character widths of the body font, used to check that text fits its box
    assets/img            logo
    assets/math           rendered formulas
    assets/diagrams       the pictures of slides 93 and 94, drawn at the size they have on the slide
    assets/photos         the prepared pictures and manifest.json (sizes, source file, crop box, rotation)
    assets/clips          rendered animations: <name>.gif is in the deck, a still frame (.png) in the handout

The folder is called `tools` because the repository ignores every folder named `build`.

## Rebuild

The deck needs Node and Python 3. Nothing has to be rendered again for it: the animations, formulas and
pictures are in `assets`.

    cd presentation/tools/deck
    npm install                                 # once: pptxgenjs 4.0.1, as named in package.json
    node build.js ../../out/deck_raw.pptx
    python3 ../post.py ../../out/deck_raw.pptx ../../out/deck.pptx theme.json
    python3 ../check2.py ../../out/deck.pptx
    node words.js                               # length of the talk from the notes

`out/deck.pptx` then differs from `thesis-defense.pptx` only in its time stamps and section identifiers. Copy
it over `thesis-defense.pptx` to publish a change. The folder `out` is not tracked.

Handout, with a still frame of every animation (the last frame; the first for the title strip):

    DECK_STATIC=1 node build.js ../../out/static_raw.pptx
    python3 ../post.py ../../out/static_raw.pptx ../../out/static.pptx theme.json
    # then export static.pptx to PDF from PowerPoint or LibreOffice (tagged PDF)

The handout in this folder was exported with LibreOffice, where Carlito and Caladea stand in for Calibri and
Cambria.

Only after a change to their sources, from the folder `presentation`:

    sh tools/render_all.sh                      # animations: needs manim, LaTeX, ffmpeg, ffprobe and the fonts
                                                # Carlito and DejaVu Sans Mono; several minutes; log in
                                                # tools/render_all.log
    python3 tools/formulas.py                   # formulas: needs pdflatex and pdftocairo
    python3 tools/quant_figures.py              # pictures of slides 93 and 94: needs numpy, matplotlib, the font
                                                # Carlito, and middleware/rdma_tensor_cache/scuffed_quant.py
    python3 tools/photos.py ../Updates/Update1-HardwareSetup    # pictures: needs Pillow

## Changing things

- A slide: every slide is one `def("id", () => { ... })` block in a `d*.js` file, in deck order. Its notes are
  the last argument of `newSlide`. Links use slide ids, so slides can be added or removed without renumbering.
- Bullets: `B(s, [...])` fills the body placeholder of the layout. A nested array is the second level,
  `**term**` is bold, `{ t, num: true }` is a numbered item. The build prints a warning when text does not fit
  its box.
- Tables: `tbl(...)` draws rules only (heavy above and below, a thin rule under the header).
- Pictures: `pic(s, name, altText, {x, y, w})` places a picture of `assets/photos`, `caption(...)` writes the
  line under it, and `code(s, lines, x, y, w)` sets source text in a fixed-width font on the gray panel.
- Diagrams: `dia(s, name, x, y)` places a picture of `assets/diagrams` at the size it was drawn for, so a label
  of 14 pt inside the picture is 14 pt on the slide. Change the picture in `tools/quant_figures.py`.
- Pace of the animations: `Clip.SPEED` (every movement), `Clip.PAUSE` (every pause) and `Clip.HOLD` (seconds
  the last frame stays) in `manim/style.py`, then render again. The GIFs are written at 10 frames per second
  with 64 colors; `COLORS=96 sh tools/render.sh ...` raises the number of colors.
- The example on slide 10: `T1`, `P` and `N` at the top of `manim/h1_amdahl_dig.py` set every number and bar.
- The other pictures from everyday life: the values at the top of each `manim/x*.py` set what is drawn (the
  amounts of the statement, the customers and parcels, the number of lockers, the length of the ruler), and
  the docstring of each file says what stands for what.

## Rules the deck follows

- The numbers come from the thesis. Results that are not measured yet are empty table cells with a star note.
  Six slides are labeled illustrations: the example of Amdahl's law on slide 10, which has an assumed value,
  and the pictures on slides 21, 34, 64, 72 and 97, whose amounts and counts are made up for the picture.
  Slides 93 and 94 are labeled illustrations as well: one synthetic vector, computed and not made up.
- Models and arithmetic are labeled as such on the slide. A test run on a development machine is named as a
  test, without numbers.
- Colors: navy for titles and emphasis, gray for secondary text and rules. Orange and blue appear only for the
  two traffic classes (orange: urgent, blue: bulk) and for the cache in diagrams. Star notes are dark orange
  italic.
- Type: titles 32 pt, bullets 22 to 24 pt (second level 19 to 21 pt), tables 17 to 20 pt, and 14 pt as the
  smallest size outside the footer and the link buttons.
- Animations are looping GIFs on a white background, 1280 x 720, one pass of 23 to 45 seconds (59 for the
  lockers, which show four propositions), the last frame held for five seconds. Each has a caption line inside the picture, and its first frame already shows its
  main picture.
- Photographs and screenshots come from the first update report (January 2026): the two towers, the V100
  cards, the vendor's firmware list, the firmware setup screen and a status report of server 4. A picture
  shows only the part that the slide talks about. The machines are server 1 to server 4.
- Every picture, chart and formula has alternative text. Every slide has a title and speaker notes.
- Wording: plain sentences. Statements with "never" or "always", and slogans of the form "X, not Y", are
  avoided; a proposition says "does not". `check2.py` rejects the phrases that were retired.
