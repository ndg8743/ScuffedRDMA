// Backup slides: proofs and details, reached from the Proof and Detail buttons and from the last slide.
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, B, B2, T, L, note, take, star, claim, stat, more, back, node, arrow, hline, vline, rect, eq, gif, pic, caption, code, tbl, CH } = require("./lib");

const bold = (t) => ({ text: t, options: { bold: true } });
const mono = (t) => ({ text: t, options: { fontFace: "Courier New" } });
const head = (t) => ({ t, plain: true, bold: true, color: NAVY, size: 22 });
// steps of a proof: plain paragraphs that start with a name in bold
const steps = (s, items, y, h, o = {}) => L(s, items.map((t) => ({ t, plain: true })), o.x === undefined ? MX : o.x, y, o.w || CW, h, { size: o.size || 20, gap: o.gap === undefined ? 12 : o.gap, name: "proof steps" });

def("b01", () => {
  const s = newSlide("b01", "Title only", "Proof of Proposition 2.1",
    "Proposition 2.1 with its proof, by induction on the layers. The proof rests on the mask, because attention at a position reads the positions before it, so a later token does not change an earlier row.");
  back(s, "k06");
  claim(s, "Proposition 2.1", "Let a transformer with a causal mask process a sequence of t tokens, and then the same sequence extended by one token. For every layer, the keys and values at positions 1 to t are identical in the two runs.", MX, 1.62, CW, 1.3, { size: 20 });
  steps(s, ["**First layer.** Its input vectors at positions 1 to t are the embeddings of the same tokens in both runs, so they are identical.",
    "**Keys and values.** In every layer the key and the value of a position are computed from that position's own input vector.",
    "**Attention.** At a position i up to t, attention reads only keys and values at positions up to i, because of the mask. Its result is the same in both runs.",
    "**Rest of the layer.** The remaining steps act on each position separately, so the inputs of the next layer agree at positions 1 to t.",
    "**Conclusion.** By induction on the layers, the rows of positions 1 to t agree in every layer."], 3.1, 3.4, { size: 19, gap: 10 });
});

def("b02", () => {
  const s = newSlide("b02", "Two columns", "Detail: one chunk on the wire",
    "The header of a slot and the steps of the protocol. A chunk and its notification are a single operation, so the notification comes once the data is in place.");
  back(s, "m06");
  B(s, [head("The 64-byte header of a slot"), "magic number", "blob identifier", "key length", "flags", "total length", "chunk offset", "chunk length"], { size: 20, gap: 7 });
  B2(s, [head("For each chunk"),
    { t: "The sender takes a credit for slot s", num: true },
    { t: "It builds header, key and chunk in its staging slot s", num: true },
    { t: "One RDMA write with immediate data goes to receive slot s. The immediate value holds the kind and the slot number", num: true },
    { t: "The receiver copies the chunk out to its place, by blob identifier and offset", num: true },
    { t: "It then returns the credit, as an 8-byte write on the hot endpoint", num: true }], { size: 20, gap: 9 });
  vline(s, 6.66, Y0 + 0.05, 4.5);
});

def("b03", () => {
  const s = newSlide("b03", "Title only", "Proofs: slots and notification",
    "Proposition 5.1 follows from the three conditions a slot can be in and the transitions between them. Proposition 5.2 follows from the fact that the chunk and its notification are one operation.");
  back(s, "m09");
  claim(s, "Proposition 5.1", "A receive slot is not overwritten while it is in use.", MX, 1.62, CW, 0.7, { size: 20 });
  const cond = [["A   Free", "the sender holds the credit"], ["B   In use", "written, being copied out"], ["C   Copied out", "the credit is on its way back"]];
  cond.forEach(([n, t], k) => {
    const x = MX + k * 2.25;
    node(s, x, 2.48, 2.0, 1.0, [{ text: n, options: { bold: true, breakLine: true } }, { text: t, options: { fontSize: 14 } }], { size: 17, name: "condition " + n });
    if (k < 2) arrow(s, x + 2.02, 2.98, x + 2.23, 2.98, { color: NAVY, width: 2 });
  });
  T(s, "and from C back to A when the sender processes the credit", MX, 3.55, 6.5, 0.38, { fontSize: 16, color: GRAY, objectName: "cycle" });
  steps(s, ["**A to B.** The sender takes the credit and posts the write.", "**B to C.** The receiver copies the chunk, then posts the credit.", "**Invariant.** A write is posted to the slot only in condition A."], 2.45, 1.75, { x: 7.4, w: 5.23, size: 16, gap: 6 });
  claim(s, "Proposition 5.2", "The notification of a chunk does not precede its data.", MX, 4.3, CW, 0.7, { size: 20 });
  T(s, "The chunk and its notification are one RDMA write with immediate data, and its completion follows the placement of every byte (fact 3). There is no second message that could arrive first. A separate done message on another endpoint would need an ordering guarantee between endpoints, which the specification does not give.",
    MX, 5.12, CW, 1.35, { fontSize: 18, objectName: "proof of 5.2" });
});

def("b04", () => {
  const s = newSlide("b04", "Title only", "Proof: the throughput bound",
    "The bound of Proposition 5.4. Between two writes to the same slot lies one full round trip of its credit. Counting those round trips over an observation time gives the bound.");
  back(s, "m09");
  claim(s, "Proposition 5.4", "The throughput X of the channel is at most the window N B divided by the time t credit that a credit needs to return.", MX, 1.62, 8.6, 1.1, { size: 20 });
  eq(s, "bound", 9.8, 1.72, { size: 28 });
  steps(s, ["**Observe.** Watch the channel for a time t obs. Let K be the number of writes, summed over the N slots.",
    "**Count round trips.** Two writes to the same slot are separated by one round trip of its credit, so at least K − N round trips are completed, and those of one slot fit into t obs:"], 2.95, 1.5, { size: 19 });
  eq(s, "proof54a", MX + 0.4, 4.35, { size: 19 });
  T(s, [{ text: "Bytes.  ", options: { bold: true } }, { text: "Each write carries at most B bytes, so" }], MX, 5.2, 4.9, 0.6, { fontSize: 19, valign: "middle", objectName: "step bytes" });
  eq(s, "proof54b", MX + 5.0, 5.15, { size: 19 });
  note(s, "The first term vanishes as t obs grows.", { y: 6.05, h: 0.4, size: 17 });
});

def("b05", () => {
  const s = newSlide("b05", "Title only", "Proof of Proposition 6.1",
    "The proof of Proposition 6.1 is two lines. The rest of the slide is the count for 40 layers and the two checks against data.");
  back(s, "d05");
  claim(s, "Proposition 6.1", "Let the layer numbers of consecutive transfers be 0, 1, ..., L − 1, repeating, with L at least 2. Then the static phase detector does not report decode.", MX, 1.62, CW, 1.1, { size: 20 });
  steps(s, ["**What decode needs.** The detector reports decode only if the last three layer numbers are equal.",
    "**What the stream gives.** Consecutive transfers differ: the next layer number is one higher, or it is 0 after L − 1, and 0 differs from L − 1 because L is at least 2.",
    "**Conclusion.** A window therefore does not hold three equal numbers, and the detector does not answer decode."], 2.95, 2.2, { size: 19 });
  hline(s, MX, 5.2, CW);
  T(s, [{ text: "The count for 40 layers.  ", options: { bold: true } }, { text: "7 of every 40 windows contain the wrap from 39 to 0: prefill 33 of 40, unknown 7 of 40." }], MX, 5.3, 5.75, 1.1, { fontSize: 17, objectName: "count" });
  T(s, [{ text: "Checked against data.  ", options: { bold: true } }, { text: "8,000 synthetic decode transfers: 6,605 prefill, 1,395 unknown, 0 decode. One recorded run on a real device: no decode labels." }], 6.88, 5.3, 5.75, 1.1, { fontSize: 17, objectName: "check" });
});

def("b06", () => {
  const s = newSlide("b06", "Title only", "Detail: the learned classifier",
    "The model, the objective, and the two properties that are proved. Strict convexity means that the weights training converges to do not depend on where it starts. Proposition 6.3 says the model can express a different size cut-off in each phase.");
  back(s, "d07");
  T(s, "The model", MX, 1.6, 5, 0.36, { fontSize: 17, color: GRAY, objectName: "label" });
  eq(s, "softmax", MX, 2.0, { size: 19 });
  T(s, "The training objective", 6.9, 1.6, 5, 0.36, { fontSize: 17, color: GRAY, objectName: "label" });
  eq(s, "objective", 6.9, 2.05, { size: 16, maxW: 5.73 });
  hline(s, MX, 3.2, CW);
  T(s, [{ text: "Proposition 6.2  ", options: { bold: true, color: NAVY } }, { text: "J is strictly convex and has a unique minimizer." }], MX, 3.35, 5.75, 0.75, { fontSize: 19, objectName: "proposition 6.2" });
  eq(s, "hessian", MX, 4.2, { size: 18, maxW: 5.75 });
  T(s, "The Hessian of the log-sum-exp function is a variance, so the first term is convex. The penalty adds a positive definite term, and J grows without bound in every direction.", MX, 4.75, 5.75, 1.6, { fontSize: 17, objectName: "proof idea 6.2" });
  T(s, [{ text: "Proposition 6.3  ", options: { bold: true, color: NAVY } }, { text: "A size cut-off per phase is representable." }], 6.88, 3.35, 5.75, 0.75, { fontSize: 19, objectName: "proposition 6.3" });
  eq(s, "delta", 6.88, 4.2, { size: 17, maxW: 5.75 });
  T(s, "The wanted difference of scores is linear in the features t p, t e, p and e. So one weight vector produces it for the hot state, and the zero vector serves the other state.", 6.88, 4.75, 5.75, 1.6, { fontSize: 17, objectName: "proof idea 6.3" });
  vline(s, 6.66, 3.35, 3.0);
});

def("b07", () => {
  const s = newSlide("b07", "Title only", "Detail: the controller",
    "The model, then the two rules side by side. Because the Hamiltonian is linear in u, the best control is 0 or 1, and the switching function S decides which.\n\n* Decide before submission which repair to make.");
  back(s, "d10");
  T(s, "The model: u is the share of the link for the hot queue", MX, 1.6, 6.2, 0.36, { fontSize: 17, color: GRAY, objectName: "label" });
  eq(s, "queues", MX, 2.0, { size: 18 });
  T(s, "The switching function", 7.2, 1.6, 5.43, 0.36, { fontSize: 17, color: GRAY, objectName: "label" });
  eq(s, "switching", 7.2, 2.1, { size: 20 });
  hline(s, MX, 3.0, CW);
  T(s, "Implemented: send cold when", MX, 3.15, 5.75, 0.4, { fontSize: 18, bold: true, objectName: "label implemented" });
  eq(s, "implemented", MX, 3.7, { size: 17, maxW: 5.75 });
  T(s, "Consistent with the model: send cold when", 6.88, 3.15, 5.75, 0.4, { fontSize: 18, bold: true, objectName: "label consistent" });
  eq(s, "consistent", 6.88, 3.6, { size: 16, maxW: 5.75 });
  vline(s, 6.66, 3.15, 1.3);
  T(s, [{ text: "Evidence.  ", options: { bold: true } }, { text: "One recorded run: 1,000 decisions, all of them cold. Synthetic grid of queue lengths: hot in 6 % of cases against 79 %. Simulation with Poisson arrivals: mean wait 1.76 ms against 0.28 ms. The simulation is synthetic, so we take the ordering as the finding." }],
    MX, 4.7, CW, 1.0, { fontSize: 17, valign: "middle", objectName: "evidence" });
  star(s, "Decide before submission: keep it a router and use the consistent rule, or make it allocate service and correct the sign.", MX, 5.85, CW, 0.6);
});

def("b08", () => {
  const s = newSlide("b08", "Title only", "Proof: rotation and sketch lemmas",
    "The lemmas behind the quantizer. On the left, why the rotation preserves lengths and why each rotated coordinate has variance one over d. On the right, the sign sketch: the estimate is unbiased for normal projections, and its standard deviation falls with the square root of the number of projections.");
  back(s, "c05");
  T(s, "The rotation", MX, 1.6, 5.75, 0.4, { fontSize: 20, bold: true, color: NAVY, objectName: "heading rotation" });
  T(s, [{ text: "Lemma 6.7  ", options: { bold: true } }, { text: "R is orthogonal." }], MX, 2.1, 5.75, 0.4, { fontSize: 18, objectName: "lemma 6.7" });
  eq(s, "hht", MX, 2.6, { size: 19 });
  T(s, "By induction on the doubling. D times its transpose is the identity.", MX + 2.6, 2.5, 3.15, 0.7, { fontSize: 15, color: GRAY, valign: "middle", objectName: "idea 6.7" });
  T(s, [{ text: "Lemma 6.8  ", options: { bold: true } }, { text: "Each coordinate of R u has mean 0 and variance 1/d." }], MX, 3.4, 5.75, 0.7, { fontSize: 18, objectName: "lemma 6.8" });
  eq(s, "yi", MX, 4.2, { size: 19 });
  T(s, "The signs are independent with mean 0. The variance is the sum of the squared entries of u divided by d, which is 1/d for a unit vector.", MX, 5.3, 5.75, 1.15, { fontSize: 16, objectName: "idea 6.8" });
  vline(s, 6.66, 1.65, 4.75);
  T(s, "The sign sketch", 6.88, 1.6, 5.75, 0.4, { fontSize: 20, bold: true, color: NAVY, objectName: "heading sketch" });
  eq(s, "sketch_est2", 6.88, 2.1, { size: 17, maxW: 5.75 });
  T(s, "z j is the sign of the projection of r on the random vector s j", 6.88, 3.0, 5.75, 0.4, { fontSize: 15, color: GRAY, objectName: "definition" });
  T(s, [{ text: "Lemma 6.10", options: { bold: true } }], 6.88, 3.5, 1.7, 0.6, { fontSize: 18, valign: "middle", objectName: "lemma 6.10" });
  eq(s, "lemma610", 8.6, 3.45, { size: 16 });
  T(s, [{ text: "Proposition 6.11  ", options: { bold: true } }, { text: "The estimate is unbiased for normal projections." }], 6.88, 4.25, 5.75, 0.7, { fontSize: 18, objectName: "proposition 6.11" });
  T(s, [{ text: "Proposition 6.12", options: { bold: true } }], 6.88, 4.95, 2.4, 0.5, { fontSize: 18, valign: "middle", objectName: "proposition 6.12" });
  eq(s, "sketch_sd", 6.88, 5.45, { size: 15, maxW: 5.75 });
  note(s, "At m = 256 the factor is 0.078.", { x: 6.88, y: 6.1, w: 5.75, h: 0.4 });
});

def("b09", () => {
  const s = newSlide("b09", "Title only", "Detail: packed sizes",
    "The packed size for other choices of dimension, bits and sketch length, computed from the formula and confirmed against the bytes written. The row in bold is the configuration used on the cache of the model.");
  back(s, "c07");
  const b = (t) => ({ text: t, options: { bold: true } });
  tbl(s, ["Dimension d", "Bits b", "Sketch m", "Bytes", "Ratio to 16-bit"], [
    ["64", "2", "64", "32", "4.00"], ["64", "3", "64", "40", "3.20"], [b("64"), b("3"), b("256"), b("64"), b("2.00")],
    ["64", "4", "256", "72", "1.78"], ["128", "3", "64", "64", "4.00"], ["128", "3", "256", "88", "2.91"], ["128", "4", "256", "104", "2.46"],
  ], MX, 1.62, 7.0, [1.6, 1.1, 1.3, 1.1, 1.9], { size: 18, rowH: 0.48, align: ["right", "right", "right", "right", "right"], name: "packed sizes" });
  T(s, "Size of a packed vector", 8.2, 1.65, 4.43, 0.38, { fontSize: 17, color: GRAY, objectName: "label" });
  eq(s, "packed", 8.2, 2.1, { size: 17, maxW: 4.43 });
  T(s, "Levels for d = 64 and b = 3, in units of one over the square root of d: −2.118, −1.338, −0.764, −0.257, 0.233, 0.738, 1.316, 2.097.", 8.2, 3.3, 4.43, 1.5, { fontSize: 16, color: GRAY, objectName: "levels" });
  note(s, "The row in bold is the configuration used on the cache of the model.", { y: 5.75, h: 0.4, size: 17 });
});

def("b10", () => {
  const s = newSlide("b10", "Title only", "Detail: storage tier properties",
    "Three properties of the storage tier that are proved, and the fit of the batching model to the sweep. The reads improve up to batches of 20 and then drop by half at 50, which we cannot explain yet.\n\n* The sweep is repeated in run R3 with the drive recorded.");
  back(s, "c09");
  const bottom = tbl(s, ["Proposition", "Statement", "Why"], [
    [bold("6.13"), "The conditions for direct I/O are met", "lengths, offsets and buffer addresses are multiples of 4,096 bytes"],
    [bold("6.14"), "Blocks do not share space", "blocks take the first free run of extents that fits, and freed runs are merged"],
    [bold("6.15"), "What the checksum detects", "any single bit, and any change within four consecutive bytes; a random change goes unreported with probability under 2 to the minus 32"],
  ], MX, 1.62, CW, [1.6, 3.6, 6.733], { size: 18, rowH: 0.75, name: "storage propositions" });
  T(s, [{ text: "Fit of the batching model.  ", options: { bold: true } }, { text: "t fix = 1.60 ms, t blk = 1.91 ms, ceiling near 839 MB/s. It overestimates the time of a single-block write by about 45 %." }], MX, bottom + 0.25, 5.75, 1.1, { fontSize: 17, objectName: "fit" });
  T(s, [{ text: "Reads.  ", options: { bold: true } }, { text: "They improve up to batches of 20, then drop by half at 50. Unexplained." }], 6.88, bottom + 0.25, 5.75, 1.1, { fontSize: 17, objectName: "reads" });
  star(s, "The sweep is repeated in run R3 with the drive recorded.", MX, bottom + 1.4, CW, 0.42);
});

def("b11", () => {
  const s = newSlide("b11", "Title only", "Detail: the replacement ACPI table",
    "The replacement table in detail. Two places change. The 64-bit memory descriptor of the PCI root gets a name, and the method that reports the resources of the root sets its range: from 132 gibibytes, above the installed memory, up to the 46-bit limit of the processor.\n\n" +
    "The table is used together with a kernel parameter that tells Linux to ignore the ranges ACPI reports, so we do not claim which of the two lets the regions fit.");
  back(s, "e24");
  const cw = 6.95;
  T(s, [{ text: "1   ", options: { bold: true, color: NAVY } }, { text: "The 64-bit memory descriptor of the PCI root gets a name" }], MX, 1.56, cw, 0.36, { fontSize: 17, valign: "middle", objectName: "step 1" });
  const c1 = code(s, ["QWordMemory (ResourceProducer, PosDecode, ...", "    ...", "    ,, _Y11, AddressRangeMemory, TypeStatic)"], MX, 1.96, cw, { size: 14, name: "first change" });
  T(s, [{ text: "2   ", options: { bold: true, color: NAVY } }, { text: "The method that reports the resources of the root sets its range" }], MX, c1.y + c1.h + 0.12, cw, 0.36, { fontSize: 17, valign: "middle", objectName: "step 2" });
  code(s, ["Method (_CRS, 0, Serialized)", "{",
    "    CreateQWordField (P0RS, \\_SB.PCI0._Y11._MIN, M2MN)",
    "    CreateQWordField (P0RS, \\_SB.PCI0._Y11._MAX, M2MX)",
    "    CreateQWordField (P0RS, \\_SB.PCI0._Y11._LEN, M2LN)",
    "    M2MN = 0x0000002100000000", "    M2MX = 0x00003FFFFFFFFFFF", "    M2LN = (M2MX - M2MN) + One", "    Return (P0RS)", "}"], MX, c1.y + c1.h + 0.52, cw, { size: 14, name: "second change" });
  const rx = MX + cw + 0.3, rw = W - MX - rx;
  L(s, [head("What the numbers mean"),
    "The window starts at 132 GiB, above the 128 GB of memory",
    "It ends at the 46-bit limit of the processor, 64 TiB",
    head("How it is used"),
    "The table is edited with iasl and loaded by the boot loader before the kernel starts",
    "The kernel command line carries PCI reallocation options"], rx, 1.56, rw, 4.3, { size: 18, gap: 9 });
  note(s, "Files dsdt-original and dsdt-modified in the repository x99-udp4-rebar.", { x: rx, y: 5.95, w: rw, h: 0.6, size: 15 });
});

def("b12", () => {
  const s = newSlide("b12", "Title only", "Detail: capabilities of the servers",
    "What each server can and cannot do. The last two rows explain two pieces of work: an import-order fix for the serving engine on server 1, and the firmware work on server 4.");
  back(s, "e01");
  tbl(s, ["Capability", "Server 1", "Server 2", "Server 3", "Server 4"], [
    [bold("RDMA in the network card"), "no", "no", "yes, RoCEv2", "yes, RoCEv2"],
    [bold("RDMA in software (Soft-RoCE)"), "yes", "yes", "not needed", "not needed"],
    [bold("Link"), "10 GbE", "10 GbE", "100 GbE", "100 GbE, eight-lane slot"],
    [bold("GPUDirect RDMA"), "no", "no", "no", "blocked (kernel module)"],
    [bold("Serving engine starts unmodified"), "no (import-order fix)", "yes", "not tested", "not tested"],
    [bold("Board starts with its GPUs unmodified"), "yes", "yes", "yes", "no (firmware work)"],
  ], MX, 1.62, CW, [3.9, 2.0, 1.6, 1.9, 2.533], { size: 17, rowH: 0.62, name: "capabilities" });
});

def("b13", () => {
  const s = newSlide("b13", "Title only", "Detail: other model families",
    "The same packing on other model families, on both GPU servers. It supports a limited statement: the packing runs on attention caches, on hybrid models and on a state-space model, with nearly the same result on both GPU generations. The rows are not meant to be compared with each other.");
  back(s, "r04");
  const bottom = tbl(s, ["Model", "Tokens", "Size ratio to 32-bit", "Overlap, server 1", "Overlap, server 2"], [
    ["Granite 3.3 2B, four layers", "36", "4.00", "83.59 %", "82.42 %"], ["Granite 4.0 H Micro", "19", "5.64", "96.25 %", "95.94 %"],
    ["Granite 4.0 H Tiny", "18", "7.60", "100 %", "100 %"], ["Mamba 130M", "30", "1.39", "97.40 %", "97.40 %"],
  ], MX, 1.62, CW, [4.2, 1.3, 2.3, 2.1, 2.033], { size: 18, rowH: 0.56, align: ["left", "right", "right", "right", "right"], name: "model families" });
  T(s, "Three bits per coordinate. The table supports a limited statement: the packing runs on attention caches, hybrid models and a state-space model, on two GPU generations, with nearly the same result on both. The rows are not meant to be compared, since the sequences are 18 to 36 tokens long.", MX, bottom + 0.3, CW, 1.5, { fontSize: 19, objectName: "statement" });
});

def("b14", () => {
  const s = newSlide("b14", "Title only", "Detail: lower bounds in full",
    "The lower bounds from arithmetic, for both link speeds. A measured transfer will take longer than the value in its row.");
  back(s, "p03");
  const b = (t) => ({ text: t, options: { bold: true } });
  tbl(s, ["Quantity", "10 Gb/s", "100 Gb/s"], [
    ["Highest payload rate", "1,225 MB/s", "12,255 MB/s"], ["One write of 1 MiB", "0.86 ms", "0.086 ms"], ["A blob of 32 MiB, the whole window", "27.4 ms", "2.7 ms"],
    ["Cache of a 128-token prompt (10 MiB)", "8.6 ms", "0.9 ms"], ["512 tokens (40 MiB)", "34.2 ms", "3.4 ms"], ["1,024 tokens (80 MiB)", "68.5 ms", "6.8 ms"],
    [b("2,048 tokens (160 MiB)"), b("136.9 ms"), b("13.7 ms")], ["4,096 tokens (320 MiB)", "273.8 ms", "27.4 ms"],
  ], MX, 1.62, 8.2, [4.6, 1.8, 1.8], { size: 18, rowH: 0.46, align: ["left", "right", "right"], name: "lower bounds" });
  T(s, [{ text: "How they are computed.  ", options: { bold: true } }, { text: "Packets of 4,096 bytes with 82 bytes of headers, trailer and gap. 80 KiB of cache per token." }], 9.3, 1.7, 3.33, 1.9, { fontSize: 17, objectName: "method" });
  T(s, [{ text: "Without overhead.  ", options: { bold: true } }, { text: "160 MiB at 10 Gb/s is 134.2 ms." }], 9.3, 3.7, 3.33, 1.0, { fontSize: 17, objectName: "without overhead" });
  note(s, "Computed from the sizes and the link rate.", { y: 6.12, h: 0.4, size: 17 });
});

def("b15", () => {
  const s = newSlide("b15", "Title only", "Detail: libfabric providers in this work",
    "The providers of libfabric that matter here. The verbs provider serves both pairs of servers. The cxi provider is the native interface of Slingshot, and it is the first choice of NIXL, whose libfabric back end does not look for the verbs provider that commodity RoCE cards need.");
  back(s, "n10");
  const bottom = tbl(s, ["Provider", "Network served", "Role in this work"], [
    [mono("verbs"), "InfiniBand, iWARP and RoCE devices, through the Linux verbs interface", "the provider for both pairs of servers"],
    [mono("tcp"), "any machine with sockets", "development and tests"],
    [mono("shm"), "shared memory on one machine", "tests, and experiment E7"],
    [mono("rxm"), "a utility provider: reliable-datagram endpoints over connected ones", "experiment E4, and the counter for hot completions"],
    [mono("cxi"), "the Cray Slingshot network", "not used here; the first choice of NIXL"],
  ], MX, 1.62, CW, [1.5, 6.1, 4.333], { size: 18, rowH: 0.62, name: "providers" });
  note(s, "The pool accepts the interface from version 1.9 (November 2019) and was developed against version 1.17 (December 2022); its tests also pass with version 2.7.0 on the tcp, shm and rxm providers. The verbs provider has no counters. The Ultra Ethernet specification maps version 2.0.", { y: bottom + 0.15, h: 0.95, size: 17 });
});

def("b16", () => {
  const s = newSlide("b16", "Two columns", "Detail: opening the pool",
    "The thirteen libfabric steps that open the pool for one class, on the connecting side. They run once per class. After them the pool holds two connected endpoints, two completion queues and one registered arena that both use.");
  back(s, "n10");
  const st = ["Ask what is available: provider, endpoint type, capabilities", "Open the fabric", "Open the domain, which is the device", "Create the event queue", "Create the completion queue of this class",
    "Create the endpoint with the queue depths of this class", "Attach the event queue and the completion queue", "Enable the endpoint", "Register the buffer arena for local and remote use",
    "Connect to the address of the peer", "Read the event queue until it reports the connection", "Exchange base address and key of the arena over TCP", "Post receive buffers: each write with immediate data consumes one"];
  B(s, st.slice(0, 7).map((t) => ({ t, num: true })), { size: 19, gap: 9 });
  B2(s, st.slice(7).map((t) => ({ t, num: true })), { size: 19, gap: 9, start: 8 });
  vline(s, 6.66, Y0 + 0.05, 4.5);
});

def("b17", () => {
  const s = newSlide("b17", "Title and text", "Detail: four changes for Ultra Ethernet",
    "The software described here has not run on Ultra Ethernet. We had no device, and the libfabric tree we read does not contain an Ultra Ethernet provider. From the specification and from our source we can say what would have to change.");
  back(s, "n11");
  B(s, [{ t: "**The endpoint type.** The mapping lists reliable-datagram endpoints, and the pool uses connected ones by default. The pool also has that mode, and E4 compares the two", num: true },
    { t: "**Memory registration.** The specification registers memory per endpoint, and the pool registers one arena per domain, so this code change is needed", num: true },
    { t: "**The write with completion data.** It is required in the AI Full and HPC profiles, and AI Base does not require it", num: true },
    { t: "**The library version.** The mapping is written against version 2.0. The pool builds against release 2.7.0 without a change, and its tests pass there on three software providers, so what remains is the provider", num: true }], { size: 21, gap: 14 });
  note(s, "The larger question is for future work: do separate endpoints still matter over a transport that spreads packets across many paths?", { y: 5.95, h: 0.55, size: 17 });
});

def("b18", () => {
  const s = newSlide("b18", "Two columns", "Detail: one request, eight steps",
    "The eight steps in full. The engine threads of the two servers are coupled through the staging area of the decode server, which is why a lost or late layer costs a timeout and a recomputation.");
  back(s, "m12");
  const st = ["The proxy assigns a transfer identifier and sends the request to the prefill instance with an output length of one token",
    "The scheduler side of the connector marks the request as a producer",
    "Around each attention layer the worker side gathers the blocks from the GPU, copies them to host memory and encodes them",
    "It queues one blob per layer, keyed by the transfer identifier and the layer name",
    "A done marker follows on the hot class",
    "The proxy forwards the request to the decode instance, whose scheduler reports all but the last prompt token as already computed",
    "Its worker waits for each layer blob, skips blocks it already holds, decodes, and writes into the block table on the GPU",
    "Decoding starts and tokens stream"];
  B(s, st.slice(0, 4).map((t) => ({ t, num: true })), { size: 19, gap: 10 });
  B2(s, st.slice(4).map((t) => ({ t, num: true })), { size: 19, gap: 10, start: 5 });
  vline(s, 6.66, Y0 + 0.05, 4.1);
  note(s, "The decode instance does not wait for the marker. The default timeout of a layer is 30 seconds.", { y: 6.1, h: 0.4, size: 17 });
});

def("b19", () => {
  const s = newSlide("b19", "Title only", "Detail: benchmark and definitions",
    "The three definitions used throughout the results, and how the benchmark takes its numbers.");
  back(s, "e07");
  T(s, "One-way latency", MX, 1.6, 5.75, 0.36, { fontSize: 17, color: GRAY, objectName: "label" });
  eq(s, "oneway", MX, 2.0, { size: 20 });
  T(s, "Penalty of the cold stream", MX, 3.0, 5.75, 0.36, { fontSize: 17, color: GRAY, objectName: "label" });
  eq(s, "penalty", MX, 3.4, { size: 18, maxW: 5.75 });
  T(s, "Time to first token", MX, 4.5, 5.75, 0.36, { fontSize: 17, color: GRAY, objectName: "label" });
  eq(s, "ttft", MX, 4.9, { size: 20, maxW: 5.75 });
  vline(s, 6.66, 1.65, 4.3);
  L(s, [head("How the benchmark measures"), "A monotonic raw clock", "1,000 warm-up iterations, then 20,000", "Minimum, mean, median, p90, p99, p99.9 and maximum", "Threads pinned to processor cores", "Instructions retired per posted operation"], 6.88, 1.6, 5.75, 4.4, { size: 20, gap: 10 });
});
