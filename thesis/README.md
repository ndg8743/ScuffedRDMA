# Thesis source

Adaptive RDMA Middleware for Disaggregated LLM Inference over Commodity Ethernet.
Nathan Gopee, M.S. Computer Science, SUNY New Paltz. Draft of November 24, 2026 (version 10).

## Build

LuaLaTeX with TeX Live 2025 or later.

    latexmk -lualatex thesis.tex

By hand: `lualatex thesis`, `bibtex thesis`, then `lualatex thesis` until the
"Rerun" warning is gone (three more runs on TeX Live 2026, four on TeX Live 2025).

On Overleaf: set the compiler to LuaLaTeX and the TeX Live version to 2025 or
later, with `thesis.tex` as the main document.

The PDF is tagged for accessibility (PDF/UA-2), and tagging makes every run
slow. A build from nothing takes several minutes. While editing, change
`tagging = on` to `tagging = off` near the top of `thesis.tex`, and switch it
back on for any PDF you check or hand in.

This draft has 166 pages, of which 17 are the bibliography, so 149 pages
count against the limit of 150. The list of symbols takes two of them and
the Dedication page one, and both can be dropped (see Switches). It builds with no LaTeX or BibTeX warnings and
no overfull lines, every figure and formula has alt text, and no heading level
is skipped.

## Structure

Ten chapters and three appendices, no parts. The contents list shows chapters
and sections only (`\setcounter{tocdepth}{1}` in `thesis.tex`).

| File | Chapter |
|---|---|
| `chapters/c01-introduction.tex` | 1 Introduction: History (ENIAC, IBM, Sun, InfiniBand, Cray and Slingshot under HPE, NVIDIA and Mellanox, the move to Ethernet, the industry today), Motivation and Contributions |
| `chapters/c02-background.tex` | 2 Background: GPUs, arithmetic, the transformer, attention kernels, inference |
| `chapters/c03-problem.tex` | 3 Problem Statement: traffic on the link, head-of-line blocking, research questions |
| `chapters/c04-rdma.tex` | 4 RDMA at a Low Level: sockets to verbs, libfabric, one transfer step by step, Ultra Ethernet |
| `chapters/c05-middleware.tex` | 5 The Middleware: overview figure and end-to-end algorithm, pool, blob channel with proofs, completion signals, connector |
| `chapters/c06-decisions.tex` | 6 Per-Transfer Decisions, Compression and Storage: classifier, rule tree, controller, quantizer, storage tier, each with its algorithm and analysis |
| `chapters/c07-testbed-method.tex` | 7 Testbed and Experimental Method |
| `chapters/c08-results.tex` | 8 Results and Discussion: the quantizer, decompression and storage results, then one section per transport experiment, then the discussion |
| `chapters/c09-related.tex` | 9 Related Work |
| `chapters/c10-conclusion.tex` | 10 Conclusion and Future Work: answers to the research questions, future work, and the conclusion, which places the work against high-performance computing |
| `chapters/aA-reproduction.tex` | A Reproducing the Results |
| `chapters/aB-calls.tex` | B libfabric and Verbs Call Reference |
| `chapters/aC-wire.tex` | C Wire Formats |

Other files: `thesis.tex` (preamble, title data, order of the chapters),
`thesis-macros.tex` (star notes, placeholders, tables, charts, headings),
`chapters/00-*.tex` (title page, approval page, abstract, dedication,
acknowledgments, terms, symbols), `figures/data.tex` (chart data taken from the results
files in the repository), `figures/newpaltz-logo.png`, `refs.bib`,
`audit/` (how each bibliography entry was checked), `tools/make_bib.py`,
`tools/notes.py` and `NOTES.md` (the list of star notes, see below).

There are no photographs or screenshots in this version.

## Algorithms and figures of the contribution

| Label | What it shows |
|---|---|
| `fig:timeline` | five eras of the history in section 1.1 as a grid: arithmetic, memory and storage, the path between machines; the cell with the heavy frame is the limit of the era (each date is cited in the text of that section) |
| `fig:architecture`, `alg:transfer` | the layers and one layer of cache from the prefill server to the decode server |
| `alg:pool` | posting an operation on a class and counting its completion |
| `alg:blob-send`, `alg:take-credit`, `alg:blob-recv`, `alg:blob-deliver`, `fig:credit` | the blob channel (sending, taking a credit, draining, receiving) and the credit cycle used in the proofs |
| `alg:static`, `alg:policy` | the static classifier and the rule tree |
| `fig:quant-pipeline`, `alg:quant` | the four steps of the quantizer |
| `alg:tier`, `alg:tier-read`, `alg:alloc` | the write path and the read path of the storage tier, and its allocator |

The algorithms were written from the code at commit c03d365. If the code
changes, change the algorithm with it. A long procedure is split at function
boundaries into blocks of at most about twenty lines, because a block is never
split across pages and a long one leaves white space on the page before it.
For the same reason a block may stand a paragraph or two after the sentence
that first names it.

## Star notes: everything that still has to be fixed, filled in or removed

The text is written as the finished thesis would read. It has no outline
section, no section on withdrawn results or corrections, and no paragraph
that tells the reader what is missing. Where something is missing, the place
holds a blank, an empty table cell or a placeholder figure, and a note marked
with a star says what it waits for. **Nothing else in the PDF uses the
character `*`, so a search for `*` finds every note.** This build has 50.

| Command | Prints | Used for |
|---|---|---|
| `\waiting{results from E3}` | \* *Waiting for results from E3.* | a result, figure or record that a run will supply |
| `\fixnote{text}` | \* *text* | anything else to fix, confirm, decide or write |
| `\blank` | `_____` | a value inside a drafted sentence; the sentence is followed by `\waiting{...}` |
| `\pendingfigure{label}{caption}{what it waits for}{steps}` | a dashed box that starts with \* **Waiting for ...** and lists the steps that produce the figure | a figure that waits for a run (13 places, all in chapter 8) |

`NOTES.md` lists every note with its page number. It is generated from the
last build:

    python3 tools/notes.py thesis.aux > NOTES.md

To clear a note: do what it says, then delete the command (for a table, fill
the cells and delete the `\waiting` line under it; for a placeholder figure,
replace the `\pendingfigure` call with a normal `figure` that keeps the same
label). The thesis is ready to hand in when the search for `*` finds nothing.

Where the notes are:

1. **Result tables with empty cells** in chapter 8, each with one note under
   it: `tab:baseline`, `tab:e1` to `tab:e8`, `tab:e8split`. `tab:bounds` holds
   lower bounds from arithmetic and is complete.
2. **Placeholder figures**: `fig:pending-quant-long`, `fig:pending-nvme`,
   `fig:pending-10g-baseline`, `fig:pending-100g-baseline`, `fig:pending-e1`
   to `fig:pending-e8`, `fig:pending-impact`.
3. **Drafted sentences with blanks**: the abstract, section 8.15.1, the three
   answers in section 10.1 (one note per research question: state the answer
   in one sentence where the note stands, then fill the blanks) and the third
   paragraph of the conclusion. They
   are written so that they do not assume an outcome. Read them again when
   the numbers are in.
4. **The hardware record** (run R0): the board and processor of server 1 in
   `tab:servers`, and which firmware change is active on server 4.
5. **Fixes in the repository** that the text depends on: the stall of blobs
   larger than one slot (section 5.3), the field `kv_compressed_bytes`, the
   `mamba3` file names, the rerun of the loopback table, the MIT notice of
   libmesh-rdma.
6. **Decisions**: the controller (repair it or keep the analysis), and the
   statements about the connector in section 5.1.
7. **Front matter**: the name and department of the third committee member
   on the approval page (two items in square brackets), and the DEDICATION
   and ACKNOWLEDGMENTS pages.

Appendix A of the thesis gives the runs (R0 to R8) that produce the results.
Two items are not in the PDF: the logo on the title page (see Switches), and
the corrections to the reference lists in the repository (sections 2.1 to
2.5 of the reference audit).

## Statements to confirm against the code

Chapter 5 states how the parts are connected today, as read from the code:

- the connector chooses the class of a blob with the static classifier, by
  size, and its codec is fixed by configuration;
- the learned classifier, the rule tree, the controller and the storage tier
  are tested as separate components and are not called by the connector;
- the sender of the connector has one queue for both classes;
- the decode side does not wait for the end-of-request marker.

A star note in section 5.1 asks for this check. If any of these changes in
the code, change section 5.1, the subsection "Where the Classes Separate on
the Serving Path", the limitations in section 8.15 and the first and second
items of the future work.

## Switches

- `\showlogofalse` in `thesis-macros.tex` removes the university logo from the
  title page. The Library's sample title page has no logo.
- The DEDICATION page is optional. To drop it, put a percent sign in front
  of `\frontchapter{DEDICATION}` and of the note under it in
  `chapters/00-front.tex`.
- The list of symbols (`chapters/00-symbols.tex`, two pages) is included by
  the two lines after the list of terms in `chapters/00-front.tex`. Remove
  them if the pages are needed.
- `\shownotesfalse` in `thesis-macros.tex` hides the star notes in the text
  and under the tables. Use it only to check the page count: the blanks, the
  empty cells and the placeholder figures stay.
- `pdfstandard = ua-1, pdfversion = 1.7` in `thesis.tex`, if a checker only
  understands PDF/UA-1 (see the comment there).

## Rules the text follows

- First person plural ("we"), used sparingly. Paragraphs carry one argument
  each, from claim to evidence to consequence.
- No number appears that is not in a results file in the repository, and
  arithmetic is labeled as arithmetic and kept out of tables of measurements.
- Chapters are not referred to by number. The text says "the previous
  chapter", "the next chapter" or "the two preceding chapters", drops the
  pointer where the sentence stands without it, or points to the section,
  table, equation or proposition that is meant. Do not `\cref` a chapter
  label (`ch:intro`, `ch:background`, `ch:problem`, `ch:lowlevel`,
  `ch:blobs`, `ch:deciding`, `ch:testbed`, `ch:results`, `ch:related`,
  `ch:conclusion`). Other labels that begin with `ch:` belong to sections.
- The word "defect" is not used: an open problem in the software is an
  "issue".
- No chapter or section announces itself with "In this chapter, we" or "In
  this section, we". An opening connects to what came before and leads into
  the content, and each chapter ends with a sentence that hands over to the
  next one.
- The setting is called commodity Ethernet. The rate of the laboratory link,
  10 gigabits per second, appears only beside a number that is computed from
  it, in the hardware of the testbed (chapter 7) and in the results
  (chapter 8).
- No paragraph narrates a missing result, a withdrawn result or a correction.
  A correction is made in the text; what cannot be settled yet is a blank or
  an empty cell with a star note.
- The machines are server 1 to server 4. Host names appear only inside file
  names.
- No bold type and no bullet lists in the text. A point is made in a
  sentence, and a list of points becomes a paragraph ("The first is ...",
  "The second is ..."). Bold remains only where the format calls for it:
  headings, the heads of propositions and algorithms, the keywords of
  pseudocode and the star of a note. A numbered list is used only for steps or
  facts that the text refers to by number, or for a sequence of steps
  (sections 3.4, 4.1.5, 4.3, 5.3.4, 5.5 and 7.4.1), and its items are plain
  sentences. A term is set in italics where
  it is defined.
- Every symbol of a displayed equation is defined in the sentence that
  follows the equation ("where $C$ is the rate of the link in bits per
  second, ..."), with its unit, and a proposition names its symbols in its
  statement. A duration is a $t$ and a size in bytes is an $s$, each with a
  word as subscript. The front matter has a list of symbols by section
  (`chapters/00-symbols.tex`): keep it in step with the text. Within one
  section a letter has one meaning.
- A proof of more than a few sentences is laid out in named steps, each a
  paragraph that begins with its name in italics (`\emph{Base case.}`), and
  its key relations are displayed.
- The three research questions are stated once, as `\rqone`, `\rqtwo` and
  `\rqthree` in `thesis-macros.tex`, so that section 3.4 and section 10.1
  repeat them in the same words. Section 10.1 answers each in the same form:
  the question, the answer in one sentence, the evidence, and the limit of
  the evidence.
- Every caption has a short form without a final period for the lists of
  figures and tables: `\caption[Short form]{Long form.}`.
- Every figure has alt text (`alt={...}`), and every formula has alt text
  (`\mathalt{words}{formula}` where the words were written by hand).
- Pseudocode uses the `pseudocode` environment
  (`\begin{pseudocode}{title}{label}`), which is never split across pages.
- Lemmas and definitions share the proposition counter. Label them with the
  kind named, `\label[lemma]{lem:name}`, so that `\cref` prints the right word.

## Bibliography

`refs.bib` is generated from `audit/bib_verified.json` by
`tools/make_bib.py`. Only cited entries are printed (126 of 145). Entries for
web pages carry the date they were read, November 23, 2026.
