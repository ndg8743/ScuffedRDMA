// Part VII: compression (the quantizer) and the storage tier.
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, tbl, CH } = require("./lib");

opener("c", "This part covers the two components that act, which are a quantizer that halves the bytes of the cache on the wire and a storage tier that gives blocks a place to wait.");

def("c01", () => {
  const s = newSlide("c01", "Two columns", "What comes from published work, and what we add",
    "The method comes from published work: the rotation and the scalar quantizer of TurboQuant, the sign sketch of QJL, and the levels of Lloyd and Max.\n\nOur part is the packed wire format, sizes measured from the bytes written, and the placement, which is on data in transit and at rest while the cache on the GPU stays as it is.");
  B(s, [{ t: "Taken from published work", plain: true, bold: true, color: NAVY, size: 24 },
    "The rotation and the scalar quantizer of TurboQuant", "The sign sketch of QJL", "The levels of Lloyd and Max"]);
  B2(s, [{ t: "Contributed here", plain: true, bold: true, color: NAVY, size: 24 },
    "A packed wire format", "Sizes measured from the bytes written", "The placement: data in transit and at rest, with the cache on the GPU left as it is"]);
  vline(s, 6.66, Y0 + 0.05, 3.5);
});

def("c02", () => {
  const s = newSlide("c02", "Title only", "Four steps for one cache vector",
    "The quantizer turns one cache vector into fewer bytes in four steps. It stores the length and normalizes. It rotates, which spreads the energy over the coordinates. It rounds each coordinate to one of eight levels. And it sketches what the rounding lost.");
  const steps = [["1", "Normalize", "Store the length of the vector in 32 bits, and continue with the unit vector"],
    ["2", "Rotate", "Lengths and inner products are kept, and the energy is spread over the coordinates"],
    ["3", "Quantize", "Round each coordinate to one of eight levels, which takes 3 bits"],
    ["4", "Sketch the residual", "Store the length of what the rounding lost, and the signs of 256 random projections of it"]];
  const w = 2.72, gap = (CW - 4 * w) / 3;
  steps.forEach(([n, head, text], k) => {
    const x = MX + k * (w + gap);
    node(s, x, 1.75, w, 0.65, [{ text: n + "   ", options: { bold: true, color: NAVY } }, { text: head, options: { bold: true } }], { size: 19, kind: "panel", name: "step " + n });
    T(s, text, x + 0.05, 2.55, w - 0.1, 1.7, { fontSize: 18, objectName: "step text " + n });
    if (k < 3) arrow(s, x + w + 0.03, 2.07, x + w + gap - 0.03, 2.07, { color: NAVY, width: 2 });
  });
  hline(s, MX, 4.5, CW);
  T(s, "The rotation", MX, 4.7, 3.2, 0.4, { fontSize: 18, color: GRAY, objectName: "label rotation" });
  eq(s, "rotation", MX, 5.15, { size: 24 });
  T(s, "The receiver reconstructs", MX + 4.3, 4.7, 4, 0.4, { fontSize: 18, color: GRAY, objectName: "label reconstruction" });
  eq(s, "reconstruct", MX + 4.3, 5.15, { size: 24 });
  T(s, "u is the unit vector, H a Hadamard matrix, D a diagonal of random signs, d the dimension, and ℓ the stored length.", MX + 8.3, 4.75, CW - 8.3, 1.4, { fontSize: 16, color: GRAY, objectName: "symbols" });
});

def("c03", () => {
  const s = newSlide("c03", "Title only", "The rotation is built by doubling",
    "The rotation is built from a Hadamard matrix, which is defined by doubling: at each step, three copies and one negated copy in a square.\n\n" +
    "Any two different rows agree in half of the places and differ in the other half, so their dot product is zero. Scaled, and multiplied by a diagonal of random signs, it is a rotation.");
  gif(s, "m4_hadamard", "Animation. The Hadamard matrix is built by doubling: from the one by one matrix 1, three copies and one copy with every sign flipped give the 2 by 2 matrix, then the 4 by 4, then the 8 by 8. Two rows of the 8 by 8 matrix are compared: they agree in four places and differ in four, so their dot product is zero. The final lines are H times H transposed equals d times the identity, and R equals one over the square root of d times H D, with R times R transposed equal to the identity.");
  note(s, "Three copies and one copy with every sign flipped, repeated until the matrix has d rows.", { align: "center", y: 6.28 });
});

def("c04", () => {
  const s = newSlide("c04", "Title only", "What the rotation does to a vector",
    "The reason for the rotation is that cache vectors often have a few channels that are much larger than the rest, and one set of levels would fit such a vector poorly.\n\n" +
    "After the rotation the length is the same and it is spread over the coordinates, so one set of levels fits them.");
  gif(s, "m5_rotation", "Animation with an example vector of 16 dimensions. Before the rotation one entry is 0.88 and a few others are moderate. The vector passes through the rotation R. After it the entries are all of moderate size, the largest is 0.38, and the length is still 1.00. Dashed lines mark plus and minus one over the square root of d.");
  note(s, "The example vector has 16 dimensions. Its length is 1.00 before and after the rotation.", { align: "center", y: 6.28 });
});

def("c05", () => {
  const s = newSlide("c05", "Text and figure", "The rotation in symbols",
    "Two lemmas support this step. The rotation is orthogonal, so lengths and inner products are preserved and the receiver can undo it. Over the random signs, each rotated coordinate has mean zero and variance one over d.");
  B(s, ["D is a diagonal of random signs, H a Hadamard matrix",
    "**Lemma 6.7:** R is orthogonal, so lengths and inner products are preserved",
    "**Lemma 6.8:** each coordinate of the rotated vector has mean 0 and variance 1/d",
    "The inverse is the transpose, so the receiver can undo the rotation"]);
  eq(s, "rrt", FX, 1.85, { size: 24, maxW: FW });
  eq(s, "variance", FX, 3.35, { size: 24, maxW: FW });
  more(s, [["Proof", "b08"]]);
});

def("c06", () => {
  const s = newSlide("c06", "Title only", "Eight levels and 256 signs",
    "After the rotation eight levels serve the coordinates, and three bits name the level.\n\nThe rounding error is the residual. We keep its length and the signs of 256 random projections of it, which lets the receiver estimate its inner product with a query.");
  gif(s, "m6_quantize", "Animation. A bell curve of the rotated coordinates with eight Lloyd-Max levels, each named by a 3-bit code. Sample coordinates are rounded to the nearest level; the rounding error is drawn as a short segment. A grid of 256 squares shows the signs of random projections of the residual. Two bars compare 128 bytes in 16-bit with the packed 64 bytes: 4 plus 4 for two lengths, 24 for the codes, 32 for the sign sketch.");
  note(s, "The levels follow the rule of Lloyd and Max: each level is the mean of its cell.", { align: "center", y: 6.28 });
});

def("c07", () => {
  const s = newSlide("c07", "Text below", "The packed format: 64 bytes",
    "Packed, a vector of 64 dimensions is 4 plus 4 plus 24 plus 32 bytes: 64 bytes, for a vector that takes 128 in 16-bit. The sizes are measured from the bytes written and agree with the formula.");
  const u = 8.6 / 128, x0 = MX + 1.5;
  T(s, "16-bit", MX, 1.8, 1.4, 0.5, { fontSize: 19, valign: "middle", objectName: "label 16-bit" });
  rect(s, x0, 1.8, 128 * u, 0.5, { fill: { color: PANEL }, name: "128 bytes" });
  T(s, "128 bytes", x0 + 128 * u + 0.2, 1.8, 1.6, 0.5, { fontSize: 19, valign: "middle", objectName: "value 128 bytes" });
  T(s, "packed", MX, 2.55, 1.4, 0.5, { fontSize: 19, valign: "middle", objectName: "label packed" });
  const parts = [[4, INK, "4 length"], [4, GRAY, "4 residual length"], [24, NAVY, "24 codes: 64 × 3 bits"], [32, BLUE, "32 sketch: 256 signs"]];
  let x = x0;
  parts.forEach(([n, col]) => { rect(s, x, 2.55, n * u, 0.5, { fill: { color: col }, line: { color: WHITE, width: 1 }, name: n + " bytes" }); x += n * u; });
  T(s, "64 bytes", x + 0.2, 2.55, 1.6, 0.5, { fontSize: 20, bold: true, color: NAVY, valign: "middle", objectName: "value 64 bytes" });
  T(s, parts.map(([n, col, lab], k) => ({ text: lab + (k < 3 ? "      " : ""), options: { color: col, bold: true } })), x0, 3.15, 9.5, 0.4, { fontSize: 17, valign: "middle", objectName: "legend" });
  eq(s, "packed64", x0, 3.85, { size: 24 });
  B(s, ["Half of the 128 bytes that the vector takes in 16-bit",
    "The sizes are measured from the bytes written"]);
  more(s, [["Detail", "b09"]]);
});

def("c08", () => {
  const s = newSlide("c08", "Title and text", "Limits of the quantizer",
    "The quantizer has limits that we state here. On the serving path the receiver reconstructs the vector and the attention kernel uses that reconstruction, so the 32 sketch bytes cross the wire unused. We also did not run a quality comparison against other methods of cache compression.");
  B(s, ["On the serving path the receiver reconstructs the vector, and the attention kernel uses that reconstruction",
    "So the sketch and the residual length, 36 bytes, cross the wire unused. Without them a vector takes 28 bytes, at the higher inner-product error",
    "A sketch pays off from about 128 bits upward, on synthetic vectors with outlier channels",
    "A quality comparison against other methods of cache compression has not been run"]);
});

def("c09", () => {
  const s = newSlide("c09", "Text and figure", "The storage tier",
    "The storage tier is one step of the usual hierarchy, from memory to a local NVMe drive. It is spill space for one run and is not kept across a restart. Each block has a checksum that is verified when the block is read, so a damaged block is reported as an error.");
  B(s, ["One step of the usual hierarchy: from memory to a local NVMe drive",
    "One backing file, with blocks in runs of 4 KiB extents",
    "A 32-bit checksum per block, verified when the block is read",
    "Spill space for one run, which is not kept across a restart"]);
  const cx = FX + FW / 2, w = 3.9, x = cx - w / 2;
  const tiers = [["GPU memory", "plain"], ["host memory", "plain"], ["local flash: an NVMe drive", "panel"], ["shared file system", "plain"]];
  tiers.forEach(([n, kind], k) => {
    const y = 1.75 + k * 1.0;
    node(s, x, y, w, 0.62, n, { size: 18, kind, bold: kind === "panel", color: k === 3 ? GRAY : INK, dash: k === 3 ? "dash" : "solid", name: n });
    if (k < 3) arrow(s, cx, y + 0.64, cx, y + 0.98, k === 1 ? { color: NAVY, width: 2.5 } : {});
  });
  T(s, "this tier", x + w + 0.12, 3.75, 1.0, 0.62, { fontSize: 16, bold: true, color: NAVY, valign: "middle", objectName: "label this tier" });
  more(s, [["Detail", "b10"]]);
});

def("c10", () => {
  const s = newSlide("c10", "Text and figure", "Batching the writes",
    "Writes are batched, with one call and one flush per batch. A simple model gives the time of a batch as a fixed part plus a part per block, so the throughput approaches the block size divided by the per-block time as batches grow.\n\n" +
    "The experiments do not spill blocks of a running request.");
  B(s, ["Writes are batched: one call and one flush per batch",
    "As batches grow, the throughput approaches the block size divided by the time per block",
    "Direct I/O is used when the alignment conditions hold",
    "The experiments do not spill blocks of a running request"]);
  T(s, "Time of a batch of n blocks", FX, 1.72, FW, 0.38, { fontSize: 18, color: GRAY, objectName: "label" });
  eq(s, "batch_time", FX, 2.2, { size: 26 });
  T(s, "Throughput", FX, 3.2, FW, 0.38, { fontSize: 18, color: GRAY, objectName: "label" });
  eq(s, "batching", FX, 3.7, { size: 26, maxW: FW });
  note(s, "t fix is the fixed time of a batch, t blk the time per block, s blk the block size.", { x: FX, y: 4.95, w: FW, h: 0.7 });
});
