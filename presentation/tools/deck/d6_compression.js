// Part VII: compression (the quantizer) and the storage tier.
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, dia, tbl, CH, linesOf } = require("./lib");

opener("c", "This part covers the two components that act, which are a quantizer that halves the bytes of the cache on the wire and a storage tier that gives blocks a place to wait.");

def("c01", () => {
  const s = newSlide("c01", "Two columns", "What comes from published work, and what we add",
    "The method comes from published work: the scheme of TurboQuant, which rotates a vector and then rounds each coordinate, the sign sketch of QJL, and the levels of Lloyd and Max. The next two slides show TurboQuant, and then where ours differs.\n\nOur part is the packed wire format, sizes measured from the bytes written, and the placement, which is on data in transit and at rest while the cache on the GPU stays as it is.");
  B(s, [{ t: "Taken from published work", plain: true, bold: true, color: NAVY, size: 24 },
    "The scheme of TurboQuant: rotate a vector, then round each coordinate", "The sign sketch of QJL", "The levels of Lloyd and Max"]);
  B2(s, [{ t: "Contributed here", plain: true, bold: true, color: NAVY, size: 24 },
    "A packed wire format", "Sizes measured from the bytes written", "The placement: data in transit and at rest, with the cache on the GPU left as it is"]);
  vline(s, 6.66, Y0 + 0.05, 3.5);
});

// added in version 10: TurboQuant as the Google Research post of March 24, 2026 presents it, and ours beside it.
// Both slides have the same three panels at the same places, so that going from one to the other shows what
// differs. The pictures are drawn by tools/quant_figures.py at the size they have here.
const QG = (CW - 3.6 - 5.3 - 2.4) / 2;
const QP = [{ x: MX, w: 3.6 }, { x: MX + 3.6 + QG, w: 5.3 }, { x: MX + 8.9 + 2 * QG, w: 2.4 }];
const QY = 4.8;                                   // top of the captions
// caps: one sentence per panel, or [ours, TurboQuant] for the slide that compares
function quantPanels(s, heads, pics, caps) {
  let bottom = 0;
  heads.forEach((head, k) => {
    const p = QP[k];
    node(s, p.x, 1.62, p.w, 0.45, [{ text: (k + 1) + "   ", options: { bold: true, color: NAVY } }, { text: head, options: { bold: true } }], { size: 18, kind: "panel", name: "step " + (k + 1) });
    if (k < 2) arrow(s, p.x + p.w + 0.03, 1.845, QP[k + 1].x - 0.03, 1.845, { color: NAVY, width: 2 });
    dia(s, pics[k], p.x, 2.12);
    const c = caps[k];
    let runs_, lines, gap = 0;
    if (typeof c === "string") { runs_ = c; lines = linesOf(c, 16, p.w); }
    else {
      // the first run of a paragraph carries its spacing and the last one its line break
      runs_ = [{ text: "Ours: ", options: { bold: true, color: NAVY, paraSpaceAfter: 6 } }, { text: c[0], options: { color: INK, breakLine: true } },
        { text: "TurboQuant: ", options: { bold: true, color: GRAY } }, { text: c[1], options: { color: GRAY } }];
      lines = linesOf("Ours: " + c[0], 16, p.w - 0.05) + linesOf("TurboQuant: " + c[1], 16, p.w - 0.05); gap = 6;
    }
    const h = (lines * 16 * 1.2 + gap) / 72;
    T(s, runs_, p.x, QY, p.w, h + 0.05, { fontSize: 16, objectName: "caption " + (k + 1) });
    bottom = Math.max(bottom, QY + h);
  });
  return bottom;
}

def("c22", () => {
  const s = newSlide("c22", "Title only", "TurboQuant: a rotation, then polar coordinates",
    "This is the method ours comes from, drawn the way Google presents it, in three steps.\n\n" +
    "First the vector is rotated at random. A cache vector often has a few large channels. After the rotation its length is the same and it is spread evenly over the coordinates.\n\n" +
    "Second, the rounding, here in polar coordinates. Two coordinates become a radius and an angle, the radii are paired again, and this repeats until one radius is left. The angles are rounded on a fixed grid.\n\n" +
    "Third, one sign per coordinate describes what the rounding lost, which removes the bias of inner products.\n\n" +
    "For questions: the polar form is the PolarQuant step, and in the TurboQuant paper the second step rounds each rotated coordinate to a level. Because the distribution after the rotation is known, the grid is fixed and no scale is stored for a block. PolarQuant uses four bits for an angle of the first level and two bits above.");
  const bottom = quantPanels(s, ["Rotate", "Round, in polar coordinates", "Signs of the error"], ["tq_rotation", "tq_polar", "tq_signs"],
    ["A random rotation matrix spreads the vector evenly over its coordinates. The length stays the same.",
     "Pairs of coordinates become a radius and an angle, and the radii are paired again until one is left. The angles are rounded on a fixed grid.",
     "One sign per coordinate, for what the rounding lost."]);
  if (bottom > 5.68) console.warn("  ! c22: captions reach " + bottom.toFixed(2));
  T(s, "After the Google Research post on TurboQuant of March 24, 2026, and the papers on TurboQuant, PolarQuant and QJL. The polar form is the PolarQuant step. In the TurboQuant paper, the second step rounds each rotated coordinate to a level. " +
    "Illustration with one synthetic vector of 64 coordinates, computed from our reading of the published steps.",
    MX, 5.78, CW, 0.74, { fontSize: 14, color: GRAY, objectName: "note" });
});

def("c23", () => {
  const s = newSlide("c23", "Title only", "Our quantizer, and where it differs",
    "Ours has the same three steps. The first and the third are built differently, and the second follows the TurboQuant paper in place of the polar form.\n\n" +
    "The rotation is a diagonal of random signs followed by a Hadamard matrix. Only 64 signs are random, where a rotation matrix has 4,096 random numbers, and the transform takes additions and subtractions.\n\n" +
    "The rounding stays in ordinary coordinates. Each coordinate goes to one of eight fixed levels, which takes three bits, and the length of the vector is stored once.\n\n" +
    "For the error we keep 256 signs for every vector, four per coordinate here, where TurboQuant keeps one.\n\n" +
    "Packed, that is 64 bytes for a vector of 64 coordinates. The next slides take the steps one at a time.\n\n" +
    "For questions: the levels can be fixed in advance because the rotation makes the distribution of a coordinate known. Our signs come from projections with entries plus and minus one, and those of TurboQuant from Gaussian projections. In bits per coordinate, ours is three for the level, four for the signs and one for the two lengths.");
  const bottom = quantPanels(s, ["Rotate", "Round, coordinate by coordinate", "Signs of the error"], ["sq_rotation", "sq_levels", "sq_signs"],
    [["64 random signs and a Hadamard matrix.", "a random rotation matrix, 4,096 numbers here."],
     ["each coordinate goes to one of eight fixed levels (3\u00A0bits), and the length is stored once.", "a radius and angles in Google's post. In the paper, levels per coordinate, as here."],
     ["256 signs per vector.", "one sign per coordinate."]]);
  if (bottom > 6.12) console.warn("  ! c23: captions reach " + bottom.toFixed(2));
  T(s, "Illustration with the same synthetic vector, computed with the code of the repository. Packed, the vector takes 64 bytes.",
    MX, 6.24, CW, 0.36, { fontSize: 14, color: GRAY, align: "center", valign: "middle", objectName: "note" });
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

// added in version 9: the two lemmas of the rotation as a picture in three dimensions
def("c21", () => {
  const s = newSlide("c21", "Title only", "The rotation as a stick in a room",
    "Before the rotation of a real vector, a picture in three dimensions. A stick of length one lies along one wall of a room. Its shadows on the three edges are its three coordinates: one is long, and two have no length.\n\n" +
    "One ruler with eight marks has to measure all three. The long shadow runs past the last mark, and the other two use no mark. On the diagonal of the room the length is the same, the three shadows are equal, and the one ruler fits them.\n\n" +
    "Turning back gives the same stick. These are the two lemmas that follow: the rotation keeps lengths and can be undone, and on average it spreads a vector evenly.");
  gif(s, "x4_stick", "Animation. On the left a room drawn as a box, with a stick of length 1.00 that starts in one corner and lies along the edge named length. On the right three bars give the shadows of the stick on the edges length, width and height, under one ruler with eight marks. At first the bars read 1.00, 0.00 and 0.00, and the first bar runs past the last mark of the ruler. The stick turns onto the diagonal of the room: its length stays 1.00 and the three bars become 0.58 each, inside the ruler. The stick turns back and onto the diagonal once more. A legend maps the stick to a cache vector, a shadow to a coordinate, the ruler to the eight levels, and the turn to the rotation. The last caption reads: Lemmas 6.7 and 6.8, same length, even spread on average, and it can be undone.");
  note(s, "Illustration in three dimensions, with a ruler chosen for the picture. A cache vector of the model used here has 64 dimensions.", { align: "center", y: 6.28 });
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
