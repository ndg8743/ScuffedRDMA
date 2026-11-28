// Opening, Part I (the moving bottleneck) and Part II (a language model and its cache).
const { pres, A, STATIC, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, PARTS, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, tbl, CH } = require("./lib");

// dated events along one line: [label, text]
function timeline(s, events, y, o = {}) {
  const n = events.length, slot = CW / n;
  s.addShape(pres.ShapeType.line, { x: MX, y, w: CW, h: 0, line: { color: NAVY, width: 2, endArrowType: "triangle" }, objectName: "time axis" });
  events.forEach(([year, text], k) => {
    const x = MX + slot * k + 0.12;
    s.addShape(pres.ShapeType.ellipse, { x: x - 0.02, y: y - 0.09, w: 0.18, h: 0.18, fill: { color: NAVY }, line: { color: WHITE, width: 1.5 }, objectName: "event " + year });
    T(s, year, x, y - 0.66, slot - 0.2, 0.46, { fontSize: 22, bold: true, color: NAVY, valign: "bottom", objectName: "year " + year });
    T(s, text, x, y + 0.24, slot - 0.26, o.h || 2.0, { fontSize: o.size || 17, objectName: "event text " + year });
  });
}
// two-line label of a diagram node: a name in bold and one line under it
const two = (a, b, size) => [{ text: a, options: { bold: true, breakLine: true } }, { text: b, options: { fontSize: size || 15 } }];

// ------------------------------------------------------------------ opening
def("a01", () => {
  const s = newSlide("a01", "Title slide", "Adaptive RDMA Middleware for Disaggregated LLM Inference over Commodity Ethernet",
    "Good afternoon, and thank you for coming. This thesis is about serving a large language model on two machines when the network between them is ordinary Ethernet.\n\n" +
    "The strip at the bottom shows the idea, with short urgent messages in orange and bulk data in blue, each in its own lane.\n\n" +
    "* The third committee member is still to be named on this slide.\n* Confirm that this use of the university logo follows the brand guidelines, or delete it in the slide master.");
  hline(s, MX, 3.52, CW);
  T(s, "Nathan Gopee", MX, 3.78, 7.4, 0.5, { fontSize: 28, bold: true, objectName: "author" });
  T(s, "M.S. thesis defense, Department of Computer Science", MX, 4.36, 7.6, 0.4, { fontSize: 20, objectName: "occasion" });
  T(s, "State University of New York at New Paltz, December 2026", MX, 4.78, 7.6, 0.4, { fontSize: 20, color: GRAY, objectName: "place and date" });
  T(s, [
    { text: "Thesis advisor", options: { color: GRAY, fontSize: 16, breakLine: true } },
    { text: "Ashley Suchy", options: { bold: true, breakLine: true, paraSpaceAfter: 10 } },
    { text: "Committee", options: { color: GRAY, fontSize: 16, breakLine: true } },
    { text: "Wafi Danesh", options: { bold: true, breakLine: true } },
    { text: "* [third member]", options: { color: ORANGE, italic: true } },
  ], 8.9, 3.78, 3.73, 1.8, { fontSize: 20, objectName: "committee" });
  s.addImage({ path: A + "/clips/t0_title." + (STATIC ? "first.png" : "gif"), x: 0, y: 5.83, w: W, h: W / 8, objectName: "animation title strip",
    altText: "Animated strip with two lanes. In the upper lane small orange squares, the short urgent messages, move quickly. In the lower lane large blue blocks, the bulk data, move slowly. The small squares pass without waiting behind the blocks." });
});

def("a02", () => {
  const s = newSlide("a02", "Text and figure", "A language model answers in two phases",
    "A language model answers in two phases. First it reads the whole prompt and builds a working state, the key-value cache. Then it generates the answer one token at a time from that state.\n\nServing systems increasingly run the two phases on different machines, so the cache has to cross a network.");
  B(s, ["**Prefill:** the model reads the whole prompt and builds a working state, the key-value cache",
    "**Decode:** it generates the answer one token at a time from that cache",
    "The two phases load a GPU in different ways, so serving systems increasingly run them on different machines",
    "The cache then has to cross a network"]);
  const cx = FX + FW / 2, w = 4.0, x = cx - w / 2;
  T(s, "prompt", x, 1.66, w, 0.34, { fontSize: 17, color: GRAY, align: "center", objectName: "label prompt" });
  arrow(s, cx, 2.02, cx, 2.3);
  node(s, x, 2.32, w, 0.95, two("Prefill server", "reads the prompt, builds the cache"), { size: 19, name: "prefill server" });
  arrow(s, cx, 3.3, cx, 4.3, { color: BLUE, width: 4, name: "cache transfer" });
  T(s, "key-value cache, across a network", cx + 0.2, 3.52, 2.6, 0.6, { fontSize: 16, color: BLUE, bold: true, valign: "middle", objectName: "label cache" });
  node(s, x, 4.33, w, 0.95, two("Decode server", "generates the answer, token by token"), { size: 19, name: "decode server" });
  arrow(s, cx, 5.3, cx, 5.58);
  T(s, "answer", x, 5.6, w, 0.34, { fontSize: 17, color: GRAY, align: "center", objectName: "label answer" });
});

def("a03", () => {
  const s = newSlide("a03", "Two columns", "The network that this split assumes",
    "In a data center the network is built for this, with hundred-gigabit links, network cards that bypass the operating system, and GPUs that those cards can write into directly.\n\nOur laboratory has commodity Ethernet, RDMA in software, and a cache that is staged through host memory.");
  B(s, [{ t: "In a data center", plain: true, bold: true, color: NAVY, size: 26 },
    "Hundred-gigabit links", "Network cards that move data without involving the operating system", "GPUs into which those cards can write directly"], { size: 24, gap: 18 });
  B2(s, [{ t: "In a university laboratory", plain: true, bold: true, color: NAVY, size: 26 },
    "Two GPU servers on commodity Ethernet", "RDMA provided in software", "The cache staged through host memory"], { size: 24, gap: 18 });
  vline(s, 6.66, Y0 + 0.05, 3.9);
});

def("a04", () => {
  const s = newSlide("a04", "Statement", "The question of this thesis",
    "This is the question as the thesis asks it. The rest of the talk is our answer to it, which is a middleware built in software and the measurements we have for it so far.");
  B(s, [{ t: "A university laboratory with two GPU machines and ordinary Ethernet has none of these, and in this thesis we ask what can be achieved in less ideal network situations.", plain: true }]);
});

def("a05", () => {
  const s = newSlide("a05", "Title only", "Outline",
    "The talk has ten parts. The first four are background, the next three are what we built, and the last three cover how we measured, what we found and what it means.\n\nEach row links to its part, and the same names are in the footer of the slides.\n\nTiming: read in full, the notes take about 59 minutes. Without parts I and IV, the five completion signals, the NUMA details, the rule tree, the storage tier and the related work, about 45 minutes.");
  const parts = PARTS.filter((p) => p.n), y0 = 1.5, rh = 0.49;
  hline(s, MX, y0, CW, { color: INK, width: 1.25 });
  parts.forEach((p, k) => {
    const y = y0 + k * rh;
    T(s, p.n, MX, y, 0.8, rh, { fontSize: 20, bold: true, color: NAVY, valign: "middle", align: "right", objectName: "numeral " + p.n });
    T(s, p.title, MX + 1.05, y, 3.75, rh, { fontSize: 20, bold: true, valign: "middle", objectName: "part " + p.n });
    T(s, p.line, MX + 4.85, y, 6.4, rh, { fontSize: 17, color: GRAY, valign: "middle", objectName: "line " + p.n });
    T(s, String(num(p.first)), MX + CW - 0.6, y, 0.6, rh, { fontSize: 16, color: GRAY, valign: "middle", align: "right", objectName: "slide of part " + p.n });
    hline(s, MX, y + rh, CW, k === parts.length - 1 ? { color: INK, width: 1.25 } : {});
    s.addShape(pres.ShapeType.rect, { x: MX, y, w: CW, h: rh, fill: { color: WHITE, transparency: 100 }, line: { color: WHITE, width: 0, transparency: 100 },
      hyperlink: { slide: num(p.first), tooltip: "Go to part " + p.n + ": " + p.title }, objectName: "link to part " + p.n });
  });
});

// ------------------------------------------------------------------ Part I
opener("h", "We start with some history, because the mechanisms we use later were built to remove limits that earlier machines ran into.");

def("h01", () => {
  const s = newSlide("h01", "Text above", "One bottleneck that keeps moving",
    "The history of computing can be read as the history of one bottleneck that keeps moving: first the arithmetic itself, then the memory that feeds the arithmetic, and then the path between one machine and another.\n\n" +
    "We follow it through four names that return later in the talk: ENIAC, IBM, Sun and Cray.");
  B(s, ["The history of computing can be read as the history of one bottleneck that keeps moving",
    "The mechanisms used in this work were built to remove limits that earlier machines ran into"], { size: 24 });
  const stages = [["1", "The arithmetic itself", "Removed by electronic computers"],
    ["2", "The memory that feeds the arithmetic", "Removed by the stored program and by random access storage"],
    ["3", "The path between one machine and another", "Removed by adapters that deliver data into the memory of another machine"]];
  stages.forEach(([n, head, sub], k) => {
    const x = MX + k * 4.1, w = 3.73;
    node(s, x, 3.95, w, 0.95, [{ text: n + "   ", options: { bold: true, color: NAVY } }, { text: head, options: { bold: true } }], { size: 19, kind: k === 2 ? "panel" : "plain", name: "stage " + n });
    T(s, sub, x, 5.05, w, 0.95, { fontSize: 17, color: GRAY, objectName: "stage text " + n });
    if (k < 2) arrow(s, x + w + 0.04, 4.42, x + 4.06, 4.42, { color: NAVY, width: 2 });
  });
});

def("h02", () => {
  const s = newSlide("h02", "Text below", "First the arithmetic, then the memory",
    "Tabulating machines counted the census of 1890 in six months, where the count of 1880 had taken more than eight years. ENIAC removed the mechanical limit on arithmetic, but it was set up by hand.\n\nThe remedy was the stored program. Once arithmetic was fast, the limit became keeping the right data close to it.");
  timeline(s, [["1890", "Tabulating machines count the census in six months"],
    ["1945", "The stored program: instructions and data in one memory"],
    ["1946", "ENIAC: arithmetic at electronic speed, set up by hand"],
    ["1956", "The first commercial hard disk: random access to records"],
    ["1964", "System/360: software written for one model runs on the others"],
    ["1967", "Amdahl: the part that cannot be divided caps the speed-up"]], 2.42);
  B(s, ["Once arithmetic was fast, the limit became keeping the right data close to it",
    "The key-value cache of a language model is held in GPU memory for the same reason"]);
});

// Amdahl's law (thesis, Section 1.1) and a simple example of it: digging a hole
def("h21", () => {
  const s = newSlide("h21", "Text and figure", "Amdahl's law",
    "Amdahl's law says how much a computation gains from more processors. If a share P of the running time can be divided among N processors and the rest cannot, the speed-up is one over the sum of the undivided share and P over N.\n\n" +
    "As N grows, the speed-up approaches one over one minus P. With 95 percent of the work divisible the limit is 20, and with 60 percent it is two and a half. The law assumes a workload of fixed size.");
  B(s, ["**1967:** Gene Amdahl, then at IBM, argues that the gain from more processors is limited by the work that cannot be divided among them",
    "P is the share of the running time that can be divided, 1 − P the sequential share, and N the number of processors",
    "As N grows, the speed-up S(N) approaches 1/(1 − P)",
    "The law assumes a workload of fixed size"], { size: 21, gap: 10 });
  eq(s, "amdahl", FX + FW / 2, 1.6, { size: 30, center: true });
  const NS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024];
  const S = (p) => NS.map((n) => Math.round(1000 / ((1 - p) + p / n)) / 1000);
  const labels = NS.map((n) => n.toLocaleString("en-US"));
  s.addChart(pres.charts.LINE, [{ name: "P = 0.95 (limit 20)", labels, values: S(0.95) }, { name: "P = 0.80 (limit 5)", labels, values: S(0.8) }, { name: "P = 0.60 (limit 2.5)", labels, values: S(0.6) }],
    Object.assign({}, CH, {
      x: FX, y: 2.75, w: FW, h: 3.3, chartColors: [H.dk2, H.accent5, H.accent3], lineSize: 2.75, lineDataSymbol: "none", lineDash: "solid",
      valAxisMinVal: 0, valAxisMaxVal: 20, valAxisMajorUnit: 5, catAxisLabelFontSize: 12,
      title: "Speed-up S(N) by number of processors N", showLegend: true, legendPos: "b", showValue: false,
      altText: "Line chart of the speed-up by Amdahl's law for 1 to 1,024 processors. With P equal to 0.95 the speed-up rises from 1 to 19.6 and approaches 20. With P equal to 0.80 it rises to 4.98 and approaches 5. With P equal to 0.60 it rises to 2.5 and stays there.",
    }));
  note(s, "Computed from the formula for three values of P.", { x: FX, y: 6.05, w: FW, h: 0.4 });
});

def("h22", () => {
  const s = newSlide("h22", "Title only", "Amdahl's law in a simple example",
    "A simple example shows what the law says. One worker with one shovel digs a hole one meter deep in an hour. If we add nine workers and no shovels, nine of them are idle and the meter still takes an hour.\n\n" +
    "If we give all ten a shovel, they get in each other's way in the one hole, so the work is less than ten times faster. Amdahl's law gives the time. Suppose that 12 of the 60 minutes cannot be shared. The other 48 minutes are divided by ten, and the meter takes 16.8 minutes, which is 3.6 times faster.\n\n" +
    "We come back to this limit in the results, where the transfer of the cache is the part that faster GPUs leave as it is.");
  gif(s, "h1_amdahl_dig", "Animation in three rows that compares the time to dig a hole 1 meter deep. One worker with one shovel needs 60 minutes. Ten workers with one shovel also need 60 minutes, because nine are idle. Ten workers with ten shovels crowd around the one hole. If all of the digging could be shared they would need 6 minutes. With the assumption that 12 of the 60 minutes cannot be shared, Amdahl's law gives 12 minutes plus 48 minutes divided by 10, which is 16.8 minutes, a speed-up of 3.6.");
  note(s, "Illustration: the 12 minutes that cannot be shared are assumed (P = 0.80, as on the previous slide).", { align: "center", y: 6.28 });
});

def("h03", () => {
  const s = newSlide("h03", "Text below", "Then the path between machines",
    "Sun treated the network as part of the machine, but each operation went through two operating systems, and clusters made that cost visible.\n\nThe CRAY T3D already let one processor read or write the memory of another, and InfiniBand made that operation a service of the network adapter.");
  timeline(s, [["1985", "Sun Network Filesystem: files on another machine, through two operating systems"],
    ["1993", "CRAY T3D: one processor reads or writes the memory of another"],
    ["1994", "The first Beowulf cluster, and MPI 1.0: ordinary computers on ordinary Ethernet"],
    ["1999", "InfiniBand Trade Association: the adapter delivers data into another server's memory"],
    ["2002", "Intel drops its InfiniBand hardware. GPFS is presented"]], 2.42);
  B(s, ["As programs exchanged data more often than they computed alone, the trip through two operating systems became the limit",
    "InfiniBand found its place as the interconnect of supercomputers"]);
});

def("h04", () => {
  const s = newSlide("h04", "Text and figure", "Ethernet returns",
    "The last decade changed who owns the interconnects. On the TOP500 list of November 2026, InfiniBand connects the most systems, but Slingshot, which is a form of Ethernet, carries the largest share of the performance.\n\nIn the clusters built for machine learning, Ethernet has taken more than two-thirds of the switch sales.");
  B(s, ["**2015:** libfabric 1.0, a portable interface",
    "**2019:** HPE acquires Cray, whose Slingshot network is an optimized Ethernet",
    "**2020:** NVIDIA acquires Mellanox, the maker of the ConnectX cards in our testbed",
    "**2023:** the Ultra Ethernet Consortium. **2025:** its specification 1.0"]);
  s.addChart(pres.charts.BAR, [{ name: "Share of systems", labels: ["InfiniBand", "Slingshot"], values: [60.6, 12] }, { name: "Share of aggregate performance", labels: ["InfiniBand", "Slingshot"], values: [37.8, 39.7] }], Object.assign({}, CH, {
    x: FX, y: 1.55, w: FW, h: 4.2, barDir: "col", chartColors: [H.dk2, H.accent3], barGapWidthPct: 55,
    valAxisMinVal: 0, valAxisMaxVal: 80, valAxisMajorUnit: 20, title: "TOP500, November 2026 (%)", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "General",
    altText: "Column chart for the TOP500 list of November 2026. InfiniBand: 60.6 percent of the systems and 37.8 percent of the aggregate performance. Slingshot: 12 percent of the systems, and its current generation carries 39.7 percent of the aggregate performance.",
  }));
  note(s, "Networks for machine learning: InfiniBand over 80 % of switch sales in late 2023, Ethernet more than two-thirds in 2025.", { x: FX, y: 5.78, w: FW, h: 0.7 });
});

def("h05", () => {
  const s = newSlide("h05", "Title only", "The same operation, from the T3D to libfabric",
    "The programming model stayed the same while the fabric changed. The one-sided operation of the T3D was standardized by InfiniBand, carried over Ethernet almost unchanged, and is now reached through libfabric.\n\nA design built on those semantics can move from one fabric to another, which is why the middleware is written against libfabric.");
  const steps = [["CRAY T3D", "1993", "One processor reads or writes the memory of another, and the remote processor takes no part"],
    ["InfiniBand", "1999", "The same operation becomes a service of the network adapter: remote direct memory access"],
    ["RoCE", "over Ethernet", "The InfiniBand transport is carried over Ethernet almost unchanged"],
    ["libfabric", "2015", "A portable interface, and the native interface of Slingshot"],
    ["Ultra Ethernet", "2025", "The next transport adopts libfabric as its interface"]];
  const w = 2.12, gap = (CW - 5 * w) / 4;
  steps.forEach(([head, year, text], k) => {
    const x = MX + k * (w + gap);
    node(s, x, 1.72, w, 0.82, [{ text: head, options: { bold: true, color: NAVY, breakLine: true } }, { text: year, options: { fontSize: 15, color: GRAY } }], { size: 18, kind: "panel", name: "step " + head });
    T(s, text, x + 0.04, 2.68, w - 0.08, 1.9, { fontSize: 17, objectName: "step text " + head });
    if (k < 4) arrow(s, x + w + 0.03, 2.13, x + w + gap - 0.03, 2.13, { color: NAVY, width: 2 });
  });
  claim(s, "", "The programming model stayed the same while the fabric changed, so a design built on those semantics can move from one fabric to another.", MX, 4.75, CW, 1.3, { size: 22 });
});

def("h06", () => {
  const s = newSlide("h06", "Text and figure", "Inference has reached the third stage",
    "Inference has arrived at the third stage quickly. A single GPU does the arithmetic, the working state lives in the memory of that GPU, and when the work is split across two servers the state has to cross from one memory to the other.\n\nIn a university laboratory that link is commodity Ethernet. That is the setting we study.");
  B(s, ["A single GPU does the arithmetic",
    "The working state of the model lives in the memory of that GPU",
    "When the work is split across two servers, the state has to cross from one memory to the other",
    "National laboratory: InfiniBand or Slingshot. University laboratory: commodity Ethernet"]);
  tbl(s, ["Stage of the bottleneck", "In language-model inference"], [
    ["1   Arithmetic", "a single GPU"],
    ["2   Memory", "the key-value cache, held in GPU memory"],
    [{ text: "3   The path between machines", options: { bold: true } }, { text: "the link between two servers", options: { bold: true } }],
  ], FX, 1.75, FW, [2.75, 2.93], { size: 18, rowH: 0.85, name: "three stages" });
  note(s, "The third stage, on commodity Ethernet, is the setting of this thesis.", { x: FX, y: 5.35, w: FW, h: 0.6, size: 17 });
});

// ------------------------------------------------------------------ Part II
opener("k", "To see what has to cross the link, we need one attention layer and the cache it leaves behind.");

def("k01", () => {
  const s = newSlide("k01", "Text and figure", "How a language model produces text",
    "Text is cut into tokens, and each token becomes a vector. The model is a stack of identical layers, with one vector per position in and one out.\n\nThe last layer gives a score for every word of the vocabulary. The model predicts one token, appends it, and predicts the next.");
  B(s, ["Text is cut into tokens, and each token becomes a vector",
    "The model is a stack of identical layers: one vector per position in, one vector per position out",
    "The last layer, at the last position, gives a score for every word of the vocabulary",
    "The model predicts one token, appends it, and predicts the next"]);
  const cx = FX + FW / 2, w = 3.7, x = cx - w / 2;
  node(s, x, 1.72, w, 0.52, "tokens", { size: 18 });
  arrow(s, cx, 2.26, cx, 2.56);
  node(s, x, 2.58, w, 0.52, "one vector per token", { size: 18 });
  arrow(s, cx, 3.12, cx, 3.42);
  rect(s, x + 0.14, 3.3, w, 1.0, { name: "layer behind" }); rect(s, x + 0.07, 3.37, w, 1.0, { name: "layer behind" });
  node(s, x, 3.44, w, 1.0, two("a stack of identical layers", "attention, then a small network", 16), { size: 18, kind: "panel", name: "layers" });
  arrow(s, cx, 4.46, cx, 4.76);
  node(s, x, 4.78, w, 0.7, "a score for every word of the vocabulary", { size: 18 });
  arrow(s, cx, 5.5, cx, 5.8);
  node(s, x, 5.82, w, 0.52, "the next token", { size: 18, bold: true });
  // the loop back to the top
  const xr = x + w + 0.42;
  s.addShape(pres.ShapeType.line, { x: x + w, y: 6.08, w: 0.42, h: 0, line: { color: GRAY, width: 1.5 }, objectName: "loop" });
  s.addShape(pres.ShapeType.line, { x: xr, y: 1.98, w: 0, h: 4.1, line: { color: GRAY, width: 1.5 }, objectName: "loop" });
  arrow(s, xr, 1.98, x + w + 0.02, 1.98, { name: "loop" });
  T(s, "appended", xr + 0.08, 3.6, 0.36, 1.3, { fontSize: 15, color: GRAY, align: "center", valign: "middle", vert: "vert270", objectName: "label appended" });
});

def("k02", () => {
  const s = newSlide("k02", "Text and figure", "Attention: queries, keys and values",
    "Inside a layer, positions exchange information through attention. Each position computes a query, a key and a value: what it is looking for, what it offers, and what it hands over.\n\nThe score is the dot product of a query with a key. A softmax turns the scores into weights, and the result is the weighted sum of the values.");
  B(s, ["Each position computes three vectors from its own vector",
    ["**Query:** what the position is looking for", "**Key:** what the position offers", "**Value:** what it hands over"],
    "The score of an earlier position is the dot product of the query with its key",
    "A softmax turns the scores into weights, and the result is the weighted sum of the values"]);
  T(s, "For all positions at once", FX, 1.75, FW, 0.4, { fontSize: 18, color: GRAY, objectName: "label" });
  eq(s, "attention", FX, 2.3, { size: 26, maxW: FW });
  T(s, "The softmax, applied to each row", FX, 3.75, FW, 0.4, { fontSize: 18, color: GRAY, objectName: "label" });
  eq(s, "softmax_def", FX, 4.25, { size: 26 });
  note(s, "The rows of Q, K and V are the queries, keys and values of the positions. d is the number of entries of a key.", { x: FX, y: 5.5, w: FW, h: 0.8 });
});

def("k03", () => {
  const s = newSlide("k03", "Title only", "One attention layer as matrices",
    "This is one attention layer as matrices, with four positions and three dimensions. The score of position i for position j is a dot product, so all the scores together are Q times K transposed.\n\nThe causal mask removes the positions after i. A softmax turns each row into weights that sum to one, and each output row is the mix of the value rows with those weights.");
  gif(s, "m1_attention", "Animation of one attention layer with 4 positions and 3 dimensions. Matrices Q and K appear; one entry of the score matrix S is computed as the dot product of a row of Q and a row of K; the entries above the diagonal are masked; each row is divided by the square root of d and passed through a softmax so that it sums to 1; the result A is multiplied by V to give the output. The final line is the attention formula.");
  note(s, "Rows are positions. The entry in row i and column j of the score matrix is the dot product of query i with key j.", { align: "center", y: 6.28 });
});

def("k04", () => {
  const s = newSlide("k04", "Text and figure", "Why the model keeps a cache",
    "Without a cache, each new token would run the whole sequence through all the layers again, and the work would grow with the square of the answer length.\n\nThe causal mask makes that unnecessary. The keys and values of earlier positions do not change, so they are stored the first time they are computed. That store is the key-value cache.");
  B(s, ["Without a cache, each new token runs the whole sequence through all the layers again",
    "The work then grows with the square of the answer length, in every layer",
    "With the causal mask, the keys and values of earlier positions do not change when a token is added",
    "So they are stored the first time they are computed: the key-value cache"]);
  const xs = [FX + 0.25, FX + 2.45], w = 1.9, rh = 0.34, y0 = 2.3;
  ["keys", "values"].forEach((lab, c) => {
    T(s, lab, xs[c], 1.8, w, 0.4, { fontSize: 18, bold: true, color: NAVY, align: "center", objectName: "label " + lab });
    for (let r = 0; r < 6; r++) {
      const isNew = r === 5;
      s.addShape(pres.ShapeType.rect, { x: xs[c], y: y0 + r * (rh + 0.08), w, h: rh, fill: { color: BLUE, transparency: isNew ? 0 : 75 }, line: { color: BLUE, width: 0.75 }, objectName: lab + " row " + (r + 1) });
    }
  });
  const xl = FX + 4.5;
  vline(s, xl, y0, 5 * (rh + 0.08) - 0.08, { color: GRAY, width: 1.25 });
  T(s, "computed once, then reused", xl + 0.12, y0, 1.1, 5 * (rh + 0.08) - 0.08, { fontSize: 16, color: GRAY, valign: "middle", objectName: "label stored rows" });
  T(s, "the new position", xl + 0.12, y0 + 5 * (rh + 0.08) - 0.05, 1.1, 0.5, { fontSize: 16, bold: true, color: BLUE, valign: "middle", objectName: "label new row" });
  note(s, "One row per token, in every layer of the model.", { x: FX + 0.25, y: 5.05, w: FW - 0.25, h: 0.45, size: 17 });
});

def("k05", () => {
  const s = newSlide("k05", "Title only", "The cache grows by one row per token",
    "Prefill gives each prompt token one key row and one value row in each layer. During decoding each new token adds one row, and the earlier rows stay as they are.\n\n" +
    "This is what lets the two phases be split, because the rows can be built on one machine and used on another once they are carried across.");
  gif(s, "m2a_cache_rows", "Animation. A key matrix K and a value matrix V have one row per token. Prefill fills four rows at once. Each decoding step appends one new row; the earlier rows are marked computed once, reused. At the end the two matrices move over one link from a prefill server to a decode server.");
  note(s, "The same holds in every layer of the model: 40 layers for the model used here.", { align: "center", y: 6.28 });
});

// added in version 9: a picture from everyday life before the proposition (as on the slide with the shovels)
def("k21", () => {
  const s = newSlide("k21", "Title only", "The cache as a bank statement",
    "Before the proposition, a picture from everyday life. On a bank statement each line shows an amount and the balance after it. A balance is computed from the lines above it, so a new line changes no balance that is already printed.\n\n" +
    "The cache behaves in the same way. A line is a token, and its balance is the row of keys and values of that token. The old lines are not added up again, and another branch can carry on from a copy of the statement. That branch is the decode server.");
  gif(s, "x1_statement", "Animation of a bank statement with the columns line, amount and balance. Four lines stand on the statement at branch A. The balance of line 3 is marked as the sum of the amounts of lines 1 to 3: 120 minus 45 plus 30 equals 105. A fifth line is added with its balance, and check marks show that the balances of lines 1 to 4 are unchanged. A copy of the statement goes to branch B, where a sixth line is added. A legend maps a line to a token, a balance to its keys and values, the statement to the cache, and branch B to the decode server. The last caption reads: Proposition 2.1, a new token changes no earlier row of the cache.");
  note(s, "Illustration with made-up amounts. The next slide states the proposition.", { align: "center", y: 6.28 });
});

def("k06", () => {
  const s = newSlide("k06", "Text below", "Reusing the cache gives the same result",
    "This is Proposition 2.1. The proof is an induction on the layers. With the mask, attention at a position reads the positions before it, so a later token does not change an earlier row.\n\nTwo consequences follow. Reusing the cache gives the same output as recomputing it, and a cache computed on one machine can be used on another, which is what makes the split possible.");
  claim(s, "Proposition 2.1", "Let a transformer with a causal mask process a sequence of t tokens, and then the same sequence extended by one token. For every layer, the keys and values at positions 1 to t are identical in the two runs.", MX, 1.62, CW, 1.45, { size: 21 });
  T(s, "Proof by induction on the layers: with the mask, attention at a position reads the positions before it.", MX, 3.22, CW, 0.5, { fontSize: 18, color: GRAY, valign: "middle", objectName: "proof idea" });
  T(s, "Two consequences", MX, 4.12, CW, 0.45, { fontSize: 22, bold: true, color: NAVY, valign: "middle", objectName: "heading" });
  B(s, ["Reusing the cache gives the same output as recomputing it, up to rounding",
    "The cache depends on the prompt and the weights, so a cache computed on one machine can be used on another"]);
  more(s, [["Proof", "b01"]]);
});

def("k07", () => {
  const s = newSlide("k07", "Text below", "Two phases with different bottlenecks",
    "In prefill all positions are computed in parallel, and the arithmetic units of the GPU are the limit. In decode each step computes little and reads the whole cache, so memory is the limit.\n\nThe two phases interfere when they share a GPU, which is the reason for running them on separate machines.");
  tbl(s, ["Question", "Prefill", "Decode"], [
    ["What it does", "processes the whole prompt at once and fills the cache", "produces the answer one token at a time"],
    ["What limits it", "the arithmetic units of the GPU", "how fast the GPU reads its own memory"],
    ["What the user sees of it", "time to first token", "inter-token latency"],
  ], MX, 1.68, CW, [2.4, 4.9, 4.633], { size: 19, rowH: 0.62, name: "two phases" });
  B(s, ["When the phases share a GPU, a long prefill delays the decode steps of the other requests",
    "On separate machines, each tuned for its phase, the same hardware delivers better service"]);
});

def("k08", () => {
  const s = newSlide("k08", "Text and figure", "Splitting the two phases",
    "In split serving, a prefill server computes the cache and a decode server generates the answer from it. The engine keeps the cache in blocks of 16 tokens, so the cache crosses the link as blocks.\n\nThe split adds one term to the time to first token, which is the transfer.");
  B(s, ["A prefill server computes the cache, and a decode server generates the answer from it",
    "The engine keeps the cache in blocks of 16 tokens, so the cache crosses the link as blocks",
    "The split adds one term to the time to first token, which is the transfer"]);
  node(s, FX, 1.9, 1.85, 1.1, two("Prefill server", "builds the cache"), { size: 18, name: "prefill server" });
  node(s, FX + FW - 1.85, 1.9, 1.85, 1.1, two("Decode server", "uses the cache"), { size: 18, name: "decode server" });
  arrow(s, FX + 1.9, 2.62, FX + FW - 1.9, 2.62, { color: BLUE, width: 3, name: "link" });
  for (let k = 0; k < 3; k++) s.addShape(pres.ShapeType.rect, { x: FX + 2.24 + k * 0.42, y: 2.12, w: 0.32, h: 0.32, fill: { color: BLUE, transparency: 70 }, line: { color: BLUE, width: 0.75 }, objectName: "cache block" });
  T(s, "blocks of 16 tokens", FX + 1.85, 3.05, FW - 3.7, 0.4, { fontSize: 16, color: BLUE, bold: true, align: "center", objectName: "label blocks" });
  T(s, "Time to first token", FX, 3.75, FW, 0.4, { fontSize: 18, color: GRAY, objectName: "label" });
  eq(s, "ttft", FX, 4.25, { size: 24, maxW: FW });
  note(s, "The middle term is the part that belongs to the transport.", { x: FX, y: 4.9, w: FW, h: 0.45, size: 17 });
});
