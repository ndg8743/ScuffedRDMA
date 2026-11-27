// Part IX: results (measured, fixed by arithmetic, pending).
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, tbl, CH } = require("./lib");

const bold = (t) => ({ text: t, options: { bold: true } });
const wait = (t) => ({ text: "* " + t, options: { italic: true, color: ORANGE } });
const blank = { text: "", options: {} };
const NXX = 5.75, NWW = W - MX - NXX;
const OVERLAP = [90.62, 82.81, 90.62, 85.94, 96.88, 92.19, 90.62, 90.62, 89.06, 93.75, 89.06, 87.50, 89.06, 89.06, 93.75, 89.06, 92.19, 89.06, 92.19, 90.62, 96.88, 92.19, 87.50, 87.50, 93.75, 87.50, 87.50, 92.19, 90.62, 89.06, 87.50, 92.19, 89.06, 96.88, 93.75, 93.75, 95.31, 93.75, 96.88, 95.31];

opener("r", "The results come in three kinds: what is measured, what follows from arithmetic, and what is still pending.");

def("r01", () => {
  const s = newSlide("r01", "Title only", "What is measured, and what is pending",
    "Before the numbers, this slide gives their status. Three results are measured today: the quantizer on the cache of a real model, its decompression on a GPU, and the storage tier. The lower bounds are arithmetic. The eight transport experiments are pending, and their tables are shown empty.");
  tbl(s, ["Result", "Status", "Remark"], [
    ["The quantizer on the cache of a real model", bold("measured"), "one prompt of 58 tokens; a long-prompt rerun is pending"],
    ["Decompression on the GPU", bold("measured"), "on two GPU generations"],
    ["The storage tier", bold("measured"), "the drive was not recorded; a rerun is pending"],
    ["Lower bounds of the cache transfer", bold("arithmetic"), "computed from the sizes and the link rate"],
    ["E1 to E5: the pool", wait("waiting for run R2"), "on both pairs of servers"],
    ["E6: the blob channel", wait("waiting for run R5"), "after the channel tests on verbs"],
    ["E7, E8: the split engine", wait("waiting for runs R6, R7"), "time to first token"],
  ], MX, 1.62, CW, [4.8, 3.0, 4.133], { size: 18, rowH: 0.56, name: "status of the results" });
});

def("r02", () => {
  const s = newSlide("r02", "Title only", "The quantizer on a real cache",
    "This is measured on the cache of Granite 3.3 2B. For each of the 40 layers the key of the last token is the query, and we compare the eight highest-scoring positions with the original keys and with the reconstructed keys.\n\nOn average the two agree on 91.1 percent, with 82.8 percent in the weakest layer, layer 1.");
  s.addChart(pres.charts.BAR, [{ name: "Top-8 overlap, %", labels: OVERLAP.map((_, i) => String(i)), values: OVERLAP }], Object.assign({}, CH, {
    x: MX, y: 1.45, w: CW, h: 4.7, barDir: "col", chartColors: [H.dk2], barGapWidthPct: 35,
    valAxisMinVal: 70, valAxisMaxVal: 100, valAxisMajorUnit: 10, catAxisLabelFrequency: 5,
    title: "Agreement of the eight most-attended positions, by layer (%)", showLegend: false,
    showCatAxisTitle: true, catAxisTitle: "layer", showValue: false,
    altText: "Column chart of the top-8 attention overlap for each of the 40 layers of Granite 3.3 2B after packing to 3 bits with a 256-bit sign sketch. The values lie between 82.8 percent at layer 1 and 96.9 percent, with a mean of 91.1 percent.",
  }));
  take(s, "On average the two rankings agree on 91.1 % of the eight most-attended positions.", { y: 6.22 });
});

def("r03", () => {
  const s = newSlide("r03", "Narrow text and figure", "The quantizer in numbers",
    "The bytes are halved against 16-bit. On this cache the sketch is worth its 32 bytes, since the error in the inner products falls from 58.2 to 25.1.\n\n* The rerun with a long prompt is pending (run R4).");
  B(s, ["The bytes are halved against 16-bit",
    "With the 32-byte sketch, the inner-product error on this cache falls by more than half",
    "Layer 1 is the weakest, the last layers the strongest"]);
  const bottom = tbl(s, ["Quantity", "Value"], [
    ["Top-8 overlap, mean of 40 layers", "91.1 %, deviation 3.3"],
    ["Lowest layer", "82.8 % (layer 1)"],
    ["Highest layer", "96.9 %"],
    ["Inner-product error with the sketch", "25.1"],
    ["Inner-product error without it", "58.2"],
    ["Packed size per vector", "64 bytes"],
    ["Compression time per layer, processor", "5.8 ms"],
  ], NXX, 1.62, NWW, [4.3, 2.583], { size: 18, rowH: 0.48, align: ["left", "right"], name: "quantizer results" });
  star(s, "Long-prompt rerun pending (run R4).", NXX, bottom + 0.1, NWW, 0.42);
});

def("r04", () => {
  const s = newSlide("r04", "Title and text", "Five limits of this result",
    "Five limits apply to the previous two slides. The most important ones are the single prompt of 58 tokens, where the top 8 of 58 is easier than the top 8 of thousands, and the fact that the overlap is a proxy for the text the model produces.");
  B(s, ["The overlap is computed with the sketch in use, and the connector's receiver reconstructs without it",
    "One prompt of 58 tokens: the top 8 of 58 is easier than the top 8 of thousands",
    "The query is a key, standing in for a real query vector",
    "The cache was held in 32-bit",
    "The overlap is a proxy for the text the model produces"], { size: 23 });
  more(s, [["Detail", "b13"]]);
});

def("r05", () => {
  const s = newSlide("r05", "Narrow text and figure", "Decompression on the GPU",
    "Unpacking 131,072 vectors takes 20.8 milliseconds on the GPU of server 1 and 33.6 on server 2, against 572 and 1,026 milliseconds on the processors. That is about 28 and 31 times faster. Compiling the routine gave no gain, which we report as a negative result.");
  B(s, ["20.8 ms and 33.6 ms on the GPUs of servers 1 and 2",
    "572 ms and 1,026 ms on their processors",
    "About 28 and 31 times faster, on two GPU generations",
    "Compiling the routine gave no gain, which we report as a negative result"]);
  s.addChart(pres.charts.BAR, [{ name: "GPU", labels: ["Server 1", "Server 2"], values: [20.763, 33.583] }, { name: "Processor", labels: ["Server 1", "Server 2"], values: [572.297, 1026.065] }], Object.assign({}, CH, {
    x: NXX, y: 1.5, w: NWW, h: 4.75, barDir: "col", chartColors: [H.dk2, H.accent3], barGapWidthPct: 60,
    valAxisLogScaleBase: 10, valAxisMinVal: 1, valAxisMaxVal: 10000,
    title: "Unpacking 131,072 vectors (ms, logarithmic axis)", showLegend: true, legendPos: "b",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "#,##0.0",
    altText: "Column chart on a logarithmic axis. Unpacking 131,072 vectors of 128 dimensions at 3 bits takes 20.8 milliseconds on the GPU of server 1 and 33.6 on the GPU of server 2, against 572.3 and 1,026.1 milliseconds on the processors.",
  }));
});

def("r06", () => {
  const s = newSlide("r06", "Narrow text and figure", "The storage tier: batching",
    "On server 2, batching raises the write rate from 662 megabytes per second for single blocks to 827 for batches of 50. Most of the gain is reached at a batch of 20.\n\n* The sweep wrote to a temporary directory and did not record the drive, so run R3 replaces it.");
  B(s, ["From 662 MB/s for single blocks to 827 MB/s for batches of 50",
    "About a quarter more, most of it reached at a batch of 20",
    "The model fits the larger batches and overestimates a single-block write by about 45 %"]);
  s.addChart(pres.charts.BAR, [{ name: "Write with flush, MB/s", labels: ["1", "10", "20", "50"], values: [662.1, 730.7, 802.7, 827.4] }], Object.assign({}, CH, {
    x: NXX, y: 1.5, w: NWW, h: 4.1, barDir: "col", chartColors: [H.dk2], barGapWidthPct: 60,
    valAxisMinVal: 0, valAxisMaxVal: 1000, valAxisMajorUnit: 250,
    title: "Write rate by batch size (MB/s)", showLegend: false,
    showCatAxisTitle: true, catAxisTitle: "blocks per write", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
    altText: "Column chart of the write rate of the storage tier on server 2 by batch size: 662.1 megabytes per second for single blocks, 730.7 for batches of 10, 802.7 for 20 and 827.4 for 50.",
  }));
  star(s, "The sweep wrote to a temporary directory and did not record the drive. Run R3 replaces it.", NXX, 5.7, NWW, 0.7);
});

def("r07", () => {
  const s = newSlide("r07", "Narrow text and figure", "The wire time, from arithmetic",
    "Arithmetic already bounds part of the answer to the third question. A prompt of 2,048 tokens needs at least about 137 milliseconds on the laboratory link. In the terms of Amdahl's law the transfer is the sequential part of a request, since faster GPUs do not shorten it.\n\n" +
    "What we can change is the number of bytes and the order in which they are sent. The quantizer works on the first and the endpoints on the second.");
  B(s, ["Lower bounds of the cache transfer, with packet headers",
    "2,048 tokens: at least 137 ms on the laboratory link",
    "4,096 tokens: at least 274 ms",
    "What can be changed: the number of bytes, and the order in which they are sent"]);
  s.addChart(pres.charts.BAR, [{ name: "10 Gb/s", labels: ["128", "512", "1,024", "2,048", "4,096"], values: [8.6, 34.2, 68.5, 136.9, 273.8] }, { name: "100 Gb/s", labels: ["128", "512", "1,024", "2,048", "4,096"], values: [0.9, 3.4, 6.8, 13.7, 27.4] }], Object.assign({}, CH, {
    x: NXX, y: 1.5, w: NWW, h: 4.75, barDir: "col", chartColors: [H.dk2, H.accent3], barGapWidthPct: 45,
    valAxisMinVal: 0, valAxisMaxVal: 300, valAxisMajorUnit: 50,
    title: "Lower bound of the cache transfer (ms)", showLegend: true, legendPos: "b",
    showCatAxisTitle: true, catAxisTitle: "prompt length, tokens", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
    altText: "Column chart of the lower bound of the cache transfer time by prompt length. At 10 gigabits per second: 8.6, 34.2, 68.5, 136.9 and 273.8 milliseconds for 128, 512, 1,024, 2,048 and 4,096 tokens. At 100 gigabits per second: 0.9, 3.4, 6.8, 13.7 and 27.4 milliseconds.",
  }));
  more(s, [["Detail", "b14"]]);
});

def("r08", () => {
  const s = newSlide("r08", "Title only", "Pending: head-of-line blocking (E3)",
    "This is the central experiment, and its table is still empty. One part follows from the design: with one endpoint per class the hot class has its own send queue, so cold messages do not queue ahead of hot ones there.\n\nWe do not know yet whether that is enough on Soft-RoCE.\n\n* Waiting for results from E3 (run R2), on both pairs of servers.");
  const bottom = tbl(s, ["Stack", "Hot p99, no cold stream", "Hot p99, cold stream of 1 MiB", "Penalty", "Cold MB/s"], [
    ["Raw verbs, one queue pair", blank, blank, blank, blank],
    ["Raw verbs, two queue pairs", blank, blank, blank, blank],
    ["libfabric connected, one endpoint", blank, blank, blank, blank],
    ["libfabric connected, two endpoints", blank, blank, blank, blank],
    ["libfabric rxm, two endpoints", blank, blank, blank, blank],
  ], MX, 1.62, CW, [4.0, 2.4, 2.8, 1.3, 1.433], { size: 18, rowH: 0.5, headH: 0.78, name: "E3 results, to be filled" });
  star(s, "Waiting for results from E3 (run R2). One table for each pair of servers.", MX, bottom + 0.08, CW, 0.42, { fontSize: 18 });
  claim(s, "From the design", "With one endpoint per class, the hot class has its own send queue, so cold messages do not queue ahead of hot messages there.", MX, bottom + 0.62, CW, 1.0, { size: 19 });
});

def("r09", () => {
  const s = newSlide("r09", "Title only", "Pending: the portable interface (E1, E2, E5)",
    "For the second question the comparison is controlled: two implementations of the pool behind one interface, measured by one benchmark source. The table waits for run R2.\n\n* Waiting for results from E1, E2 and E5 (run R2).");
  const bottom = tbl(s, ["Stack", "64 B, median", "64 B, p99", "4 KB, p99", "1 MB writes, MB/s"], [
    ["Raw verbs", blank, blank, blank, blank],
    ["libfabric, connected endpoints", blank, blank, blank, blank],
    ["libfabric, reliable-datagram endpoints (rxm)", blank, blank, blank, blank],
  ], MX, 1.62, CW, [5.0, 1.7, 1.6, 1.6, 2.033], { size: 18, rowH: 0.56, name: "E1 and E2 results, to be filled" });
  star(s, "Waiting for results from E1, E2 and E5 (run R2).", MX, bottom + 0.08, CW, 0.42, { fontSize: 18 });
  note(s, "One-way latency of a write, as half a round trip. A controlled comparison: two implementations behind one interface, measured by the same benchmark source.", { y: bottom + 0.7, h: 0.7, size: 17 });
});

def("r10", () => {
  const s = newSlide("r10", "Title only", "Pending: time to first token (E7, E8)",
    "For the third question the time to first token is split into prefill, transfer and first decode, and the middle term is the part that belongs to the transport. The table will compare one machine, our connector over verbs and over TCP, and the engine's own connector over two back ends.\n\n* Waiting for results from E7 (run R6) and E8 (run R7).");
  const bottom = tbl(s, ["Setup", "128 tokens", "512", "2,048", "4,096"], [
    ["One machine", blank, blank, blank, blank],
    ["Our connector over verbs", blank, blank, blank, blank],
    ["Our connector over TCP", blank, blank, blank, blank],
    ["NIXL over UCX", blank, blank, blank, blank],
    ["NIXL over libfabric (TCP on this pair)", blank, blank, blank, blank],
  ], MX, 1.62, CW, [5.0, 1.9, 1.6, 1.7, 1.733], { size: 18, rowH: 0.5, name: "E8 results, to be filled" });
  star(s, "Waiting for results from E7 (run R6) and E8 (run R7).", MX, bottom + 0.08, CW, 0.42, { fontSize: 18 });
  eq(s, "ttft", MX, bottom + 0.8, { size: 22 });
  T(s, "The middle term is the part that belongs to the transport.", MX + 6.2, bottom + 0.72, CW - 6.2, 0.6, { fontSize: 18, color: GRAY, valign: "middle", objectName: "ttft explained" });
});

def("r11", () => {
  const s = newSlide("r11", "Title and text", "Findings so far",
    "We have five findings so far, before the pending runs. Two come from arithmetic, one from a proof, and two from measurements with stated limits.");
  B(s, ["The size of the problem follows from arithmetic",
    "What can be changed is the number of bytes and the order in which they are sent",
    "The byte count can be halved at a measured cost",
    "The static classifier does not recognize decode traffic, which we prove as Proposition 6.1",
    "Batching helps the storage tier by about a quarter"]);
});
