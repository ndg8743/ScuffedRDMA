# Thesis defense presentation

Slides for the defense of the M.S. thesis "Adaptive RDMA Middleware for Disaggregated LLM Inference over
Commodity Ethernet" (Nathan Gopee, SUNY New Paltz, December 2026), with everything they are built from.

| File | What it is |
|---|---|
| `thesis-defense.pptx` | The deck: 154 slides (135 in the talk, 19 backup slides), 16:9, speaker notes on every slide, 13 looping animations |
| `thesis-defense-handout.pdf` | The same slides as a tagged PDF, with a still frame in place of every animation |

This is version 8 of the deck, built on November 26, 2026. It follows version 12 of the thesis draft, which is
newer than the draft in `thesis/`. Slide 64 and the remarks on the verbs provider on slides 65 and 150 describe
the code of the branch `fix/blob-channel-progress`.

## The talk

| Part | Slides |
|---|---|
| Opening | 1 to 5 |
| I. The moving bottleneck | 6 to 14 |
| II. A language model and its cache | 15 to 23 |
| III. The problem | 24 to 40 |
| IV. RDMA at a low level | 41 to 52 |
| V. The middleware | 53 to 68 |
| VI. Decisions per transfer | 69 to 81 |
| VII. Compression and storage | 82 to 92 |
| VIII. Testbed and method | 93 to 109 |
| IX. Results | 110 to 121 |
| X. Conclusions | 122 to 135 |
| Backup slides | 136 to 154 |

Every part is linked from the Outline (slide 5) and from the footer of each slide. The backup slides are reached
through the Proof and Detail buttons, and Back returns to the slide that was shown before.

Read in full, the speaker notes take about 50 minutes at 130 words a minute. Without parts I and IV, the five
completion signals (65), the rule tree (77, 78), the storage tier (91, 92) and the related work (123, 124),
about 38 minutes remain. `node tools/deck/words.js` prints both figures and the length of each part.

## Still open in the deck

A result that is not measured yet is an empty table cell with a note that starts with a star, for example
"* Waiting for results from E3 (run R2)". The star notes are on slides 1, 64, 81, 94, 95, 101, 111, 113, 116,
118, 119, 120, 125, 126, 127, 142 and 145, and `python3 tools/check2.py thesis-defense.pptx` lists them.

The deck was rendered through LibreOffice and passes `tools/check2.py`. It has not been opened in PowerPoint
yet. Before the defense, run the slide show there once and check that the animations move, that the Back
buttons return, and that the dashed and dotted lines of the chart on slide 9 show. An animated GIF moves in
PowerPoint's slide show; the editing view, previews and the handout show a still picture. Each animation is
also in `assets/clips` as an MP4 file, for a program that does not play GIFs.

## What is here

    thesis-defense.pptx           the deck
    thesis-defense-handout.pdf    the handout
    manim/                the thirteen animations (Manim Community edition 0.22.1)
      style.py            colors, type sizes, caption helper, and the pace of every animation
      grid.py             a matrix drawn as a grid of cells
    tools/
      render.sh           one animation  -> assets/clips/<name>.gif, .mp4, first and last frame
      render_all.sh       all thirteen, then durations.py
      durations.py        length of one pass of each animation -> assets/clips/durations.json (for the notes)
      formulas.py         the formulas   -> assets/math/<name>.png and manifest.json (sizes, spoken alt text)
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
        d4_middleware.js  part V (pool, blob channel, connector)
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
- Pace of the animations: `Clip.SPEED` (every movement), `Clip.PAUSE` (every pause) and `Clip.HOLD` (seconds
  the last frame stays) in `manim/style.py`, then render again. The GIFs are written at 10 frames per second
  with 64 colors; `COLORS=96 sh tools/render.sh ...` raises the number of colors.
- The example on slide 10: `T1`, `P` and `N` at the top of `manim/h1_amdahl_dig.py` set every number and bar.

## Rules the deck follows

- The numbers come from the thesis. Results that are not measured yet are empty table cells with a star note.
  One slide is a labeled illustration with an assumed value: the example of Amdahl's law on slide 10.
- Models and arithmetic are labeled as such on the slide. A test run on a development machine is named as a
  test, without numbers.
- Colors: navy for titles and emphasis, gray for secondary text and rules. Orange and blue appear only for the
  two traffic classes (orange: urgent, blue: bulk) and for the cache in diagrams. Star notes are dark orange
  italic.
- Type: titles 32 pt, bullets 22 to 24 pt (second level 19 to 21 pt), tables 17 to 20 pt, and 14 pt as the
  smallest size outside the footer and the link buttons.
- Animations are looping GIFs on a white background, 1280 x 720, one pass of 23 to 45 seconds, the last frame
  held for five seconds. Each has a caption line inside the picture, and its first frame already shows its
  main picture.
- Photographs and screenshots come from the first update report (January 2026): the two towers, the V100
  cards, the vendor's firmware list, the firmware setup screen and a status report of server 4. A picture
  shows only the part that the slide talks about. The machines are server 1 to server 4.
- Every picture, chart and formula has alternative text. Every slide has a title and speaker notes.
- Wording: plain sentences. Statements with "never" or "always", and slogans of the form "X, not Y", are
  avoided; a proposition says "does not". `check2.py` rejects the phrases that were retired.
