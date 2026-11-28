# Thesis source

Adaptive RDMA Middleware for Disaggregated LLM Inference over Commodity Ethernet.
Nathan Gopee, M.S. Computer Science, SUNY New Paltz. Draft of November 27, 2026 (version 14).

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

This draft has 168 pages, of which 18 are the bibliography, so 150 pages
count against the limit of 150 and no page is spare. Version 13 added
section 5.6 on NUMA (about a page and a half), and the page it cost was
recovered in chapter 6 (see "Page budget" below). Version 14 names AIX in
section 1.1 and makes one sentence of section 6.5.1 precise (see
"Bibliography"); every chapter and section starts on the same page as in
version 13. Text that is added from
here on needs a cut of the same length. The list of symbols takes two of the
pages and the Dedication page one, and both can be dropped (see Switches). It
builds with no LaTeX or BibTeX warnings and no overfull lines, every figure
and formula has alt text, and no heading level is skipped.

The count was checked on TeX Live 2026 and on TeX Live 2025, each built from
nothing on November 27, 2026: 168 pages on both, with every chapter starting
on the same page. The two releases do not set every line alike, so check the
count again after a change, on the release you hand in with.

### Page budget

Ten paragraphs carry the mark `\looseness=-1` at the start of their last
source line: nine in chapter 6 and the first paragraph of section 8.15.3.
The nine end "learned classifier trains on.", "in the training set.", "is
strictly convex.", "$\alpha > \beta$.", "that the checksum detects.", "size
and checksum of its block.", "are multiples of $A$." (Proposition 6.13),
"slot or a run of them." and "a time per block:". The mark asks TeX to set
that paragraph one line shorter if it can do so within its normal spacing
limits, and it changes no word. Each of the ten takes effect in this build.
They can be deleted once a page is spare, and a mark that no longer shortens
its paragraph after an edit does nothing.

One wording was shortened for the same reason, with the meaning kept: the
last sentence of Proposition 6.15 now reads "the probability of a change that
goes unreported is less than 2^-32" (before: "the probability that the block
is changed and the change goes unreported is less than 2^-32").

Three things were needed for TeX Live 2025 to give the same pages as TeX
Live 2026. With tagging on, the older release leaves the paragraph indent
after the word "Proof.", sets the end of the line of a `\label` that follows
`\begin{proposition}` as a space after the head, and puts 3 pt more above a
statement that follows a paragraph. `thesis.tex` takes the first and the
third out (the lines after the `\newtheorem` declarations, which are skipped
on TeX Live 2026), and for the second the `\label` of every proposition,
lemma and definition ends with a percent sign. None of the three changes the
output on TeX Live 2026.

Where there is room today, on both releases: the last pages of chapters 1,
2, 8 and 10 are full and those of chapters 5 and 6 have one free line, so
more than one line added to any of these adds a page. Chapter 3 ends with
about eighteen free lines, chapters 4 and 9 with four, and chapter 7 with
three.

## Structure

Ten chapters and three appendices, no parts. The contents list shows chapters
and sections only (`\setcounter{tocdepth}{1}` in `thesis.tex`).

| File | Chapter |
|---|---|
| `chapters/c01-introduction.tex` | 1 Introduction: History (ENIAC, IBM, Sun, InfiniBand, Cray and Slingshot under HPE, NVIDIA and Mellanox, the move to Ethernet, the industry today), Motivation and Contributions |
| `chapters/c02-background.tex` | 2 Background: GPUs, arithmetic, the transformer, attention kernels, inference |
| `chapters/c03-problem.tex` | 3 Problem Statement: traffic on the link, head-of-line blocking, research questions |
| `chapters/c04-rdma.tex` | 4 RDMA at a Low Level: sockets to verbs, libfabric, one transfer step by step, Ultra Ethernet |
| `chapters/c05-middleware.tex` | 5 The Middleware: overview figure and end-to-end algorithm, pool, blob channel with proofs, completion signals, connector, NUMA placement of the registered memory |
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

The algorithms were written from the code at commit c03d365. `alg:blob-send`
and `alg:take-credit` follow commit 5b0e9a7, where sending a blob waits until
its last chunk has completed; that commit is in `main` since November 26,
2026 (item 5 of the star notes below). If the code changes, change the
algorithm with it. A long procedure is split at function
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
character `*`, so a search for `*` finds every note.** This build has 51.

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
   `tab:servers`, which firmware change is active on server 4, and the number
   of NUMA nodes on each server (the note at the end of section 5.6; notebook
   00 already records the line "NUMA node(s)" of `lscpu`).
5. **Fixes in the repository** that the text depends on. The stall of blobs
   larger than one slot is fixed in `main` (commits 9ae6c93, 0c4c93e and
   5b0e9a7, merged on November 26, 2026), and sections 5.2.3 and 5.3
   describe that code. It is tested on the TCP, RXM and shared-memory
   providers with libfabric 1.17.0 and 2.7.0, and not yet on the verbs
   provider: run the tests marked `rdma` on the lab pair (the note in
   section 5.3, run R5). Still open: the field
   `kv_compressed_bytes`, the `mamba3` file names, the rerun of the loopback
   table, the MIT notice of libmesh-rdma.
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

Sections 5.2.3 and 5.3 state three things that were read from the libfabric
source or tested on November 26, 2026: on the TCP, RXM and shared-memory
providers a queued transfer advanced only during calls into the library, with
releases 1.17.0 and 2.7.0; the verbs provider has no counters and no events
for remote writes in either release, so the counter row of E4 needs
reliable-datagram endpoints and the remote-write counter of E5 cannot be
measured on the two pairs; and sending a blob returns when its last chunk has
completed at the sender. The last of these is true of `main` since the merge
of November 26, 2026.

Section 5.6 states four things about memory placement that were read from the
code at `main` (commit 8021e80) on November 27, 2026:

- the pool maps its arena and writes zeros to all of it in the thread that
  opens the pool (`sf_open`: `mmap`, then `memset`), and registers the arena
  afterwards, so the node of the arena follows from where that thread ran;
- the benchmark `sf_bench` pins its two threads to given processors;
- the Python pool, the sender and the receiver of the connector do not pin
  their threads;
- no call in the code sets a memory policy or reads the node of the card. The
  roadmap lists the NUMA-aware pool as open.

The section describes the binding as a design and says that it is not
implemented. If the binding is written, change the fourth and fifth
paragraphs of section 5.6, the sentence on NUMA in the limitations (section
8.15.3) and the last sentence of the third item of the future work. The
sentence "Servers 2, 3 and 4 have one processor socket each" rests on the
processors in `tab:servers`; the number of nodes that Linux reports on each
server is the record the star note waits for.

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
- A proposition, lemma or definition that ends with a displayed formula has
  `\par` between the formula and its `\end` line (`prop:credit` in chapter 5
  is the one case). Without it TeX Live 2025 stops with the tagpdf error
  "text-unit para hooks differ" whenever a page happens to break right after
  that formula; TeX Live 2026 builds either way.
- The `\label` of a proposition, lemma or definition stands on the line after
  its `\begin` and ends with a percent sign: `\label{prop:name}%`. Without
  the percent sign TeX Live 2025 sets a space after the head of the statement
  (see "Page budget").

## Bibliography

`refs.bib` is generated from `audit/bib_verified.json` by
`tools/make_bib.py`. Only cited entries are printed (134 of 153). Entries for
web pages carry the date they were read, November 23, 2026. One entry was
added for version 11 and read on November 26, 2026: Gustafson (1988), cited
in section 1.1 for the fixed-size form of Amdahl's law. For version 12 the
entry of the libfabric repository carries a second date, November 26, 2026,
for the provider sources of releases 1.17.0 and 2.7.0. Six entries were added
for version 13, each read on November 27, 2026 and cited in section 5.6 or
section 9.4: four pages of the Linux kernel documentation ("What is NUMA?",
"NUMA Memory Policy" in the version for kernel 6.8, "pin_user_pages() and
related calls" in the version for kernel 6.14, and the description of the
sysfs entry `numa_node` of a PCI device), NVIDIA's performance tuning notes
for ConnectX-4 and later cards, and the page "Interrupt Binding" of ESnet.
The thesis does not state that pinned pages cannot be moved between nodes,
because the page that was read for pinning does not say so.

One entry was added for version 14 and read on November 27, 2026: the IBM
book "GPFS on AIX Clusters: High Performance File System Administration
Simplified" (Farazdel and others, 2001), cited in section 1.1 for the clause
that GPFS was offered on the RS/6000 SP as GPFS for AIX. What was read is its
record and abstract on the publications page of Pacific Northwest National
Laboratory, which names the product "General Parallel File System for AIX"
and says that release 1.4 was the first offered for AIX systems outside an
RS/6000 SP. That page gives the authors by initials and no IBM order number,
and the book itself was not read. The GPFS paper of 2002 names AIX only in
the title of a manual it cites.

Section 6.5.1 says since version 14 how the rotation differs from that of
TurboQuant: a Hadamard matrix with random signs in place of a random rotation
matrix. Before, the sentence read "the rotation and scalar quantizer of
TurboQuant". Algorithm 1 of the TurboQuant paper (arXiv 2504.19874, version
1, read on November 27, 2026) draws a rotation matrix from the QR
decomposition of a matrix of normal entries and rounds each rotated
coordinate to a level; its second algorithm adds one sign per coordinate for
the residual. Its algorithms use no polar coordinates. Those belong to
PolarQuant (arXiv 2502.02617), which the paper compares itself with and which
the Google Research post of March 24, 2026 presents as the first stage of
TurboQuant. The thesis does not cite PolarQuant.
