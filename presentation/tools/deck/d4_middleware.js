// Part V: the middleware (pool, blob channel, connector).
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, tbl, CH } = require("./lib");

const two = (a, b, size) => [{ text: a, options: { bold: true, breakLine: true } }, { text: b, options: { fontSize: size || 15 } }];
const bold = (t) => ({ text: t, options: { bold: true } });
const row = (name, what) => [{ text: name + "   ", options: { bold: true } }, { text: what, options: { fontSize: 15 } }];

opener("m", "This is what we built: a pool with one endpoint per class, a channel that moves named byte strings over it, and a connector into the serving engine. The part ends with where the registered memory lies inside a server.");

def("m01", () => {
  const s = newSlide("m01", "Title only", "The layers of the middleware",
    "This is the middleware as the connector executes it. The engine calls the connector once per layer, the codec packs the blocks or leaves them raw, the sender chooses a class, and the blob channel cuts the layer into chunks.\n\nThe marker and the credits travel on the hot endpoint, the chunks on the cold endpoint.");
  const left = [["serving engine", "prefill pass, called per layer"], ["connector", "gather blocks, copy to host memory"], ["codec", "raw, or packed by the quantizer"], ["sender", "class from the static classifier"], ["blob channel", "chunks, credits, staging slots"]];
  const right = [["serving engine", "decode steps"], ["connector", "write blocks into the block table"], ["codec", "unpack, reconstruct"], ["receiver", "staging area, by key"], ["blob channel", "reassembly, return of credits"]];
  const xL = MX, xR = W - MX - 4.6, Wd = 4.6, y0 = 1.9, rh = 0.48, pitch = 0.55;
  T(s, "Prefill side", xL, 1.45, Wd, 0.38, { fontSize: 18, bold: true, color: NAVY, objectName: "heading prefill side" });
  T(s, "Decode side", xR, 1.45, Wd, 0.38, { fontSize: 18, bold: true, color: NAVY, objectName: "heading decode side" });
  [[left, xL], [right, xR]].forEach(([rows, x]) => {
    rows.forEach(([name, what], k) => node(s, x, y0 + k * pitch, Wd, rh, row(name, what), { size: 17, align: "left", margin: 9, name: name }));
    const yp = y0 + 5 * pitch;
    node(s, x, yp, Wd / 2 - 0.04, 0.62, two("hot endpoint", "depth 64, busy polling", 14), { size: 16, kind: "hot", color: ORANGE, name: "hot endpoint" });
    node(s, x + Wd / 2 + 0.04, yp, Wd / 2 - 0.04, 0.62, two("cold endpoint", "depth 512, blocking wait", 14), { size: 16, kind: "cold", color: BLUE, name: "cold endpoint" });
    node(s, x, yp + 0.69, Wd, rh, row("libfabric or raw verbs", "one RDMA device"), { size: 17, align: "left", margin: 9, kind: "panel", name: "transport library" });
  });
  const yp = y0 + 5 * pitch, xa = xL + Wd + 0.06, xb = xR - 0.06;
  arrow(s, xa, yp + 0.17, xb, yp + 0.17, { color: ORANGE, width: 2.25, both: true, name: "hot traffic" });
  T(s, "marker, credits", xa, yp - 0.2, xb - xa, 0.3, { fontSize: 15, bold: true, color: ORANGE, align: "center", objectName: "label hot traffic" });
  arrow(s, xa, yp + 0.46, xb, yp + 0.46, { color: BLUE, width: 4, name: "cold traffic" });
  T(s, "chunks", xa, yp + 0.54, xb - xa, 0.3, { fontSize: 15, bold: true, color: BLUE, align: "center", objectName: "label cold traffic" });
  T(s, "one link: Soft-RoCE on commodity Ethernet, or RoCEv2 on 100 GbE", xa + 0.1, y0 + 0.6, xb - xa - 0.2, 1.5, { fontSize: 16, color: GRAY, align: "center", valign: "middle", objectName: "label link" });
  node(s, MX, 6.03, CW, 0.5, [{ text: "Evaluated separately from this path:  ", options: { bold: true } }, { text: "learned classifier, rule tree and controller, storage tier" }], { size: 17, dash: "dash", align: "left", margin: 11, name: "evaluated separately" });
});

def("m02", () => {
  const s = newSlide("m02", "Two columns", "What runs on the serving path",
    "This slide separates two things. The left column is what the connector executes today. The right column lists components that have defined entry points and are evaluated on their own.");
  B(s, [{ t: "On the serving path", plain: true, bold: true, color: NAVY, size: 24 },
    "The class of a transfer is chosen by the static classifier, by size",
    "The marker and the credits use the hot endpoint",
    "The layers of the cache use the cold endpoint",
    "The encoding is fixed by configuration for a whole run"], { gap: 12 });
  B2(s, [{ t: "Evaluated separately", plain: true, bold: true, color: NAVY, size: 24 },
    "The learned classifier",
    "The rule tree and the controller",
    "The storage tier",
    "Connecting them to the connector is future work"], { gap: 12 });
  vline(s, 6.66, Y0 + 0.05, 3.9);
  note(s, "Experiments E1 to E5 exercise the pool, E6 the blob channel, E7 and E8 the connector.", { y: 6.2, h: 0.45, size: 17 });
});

def("m03", () => {
  const s = newSlide("m03", "Title only", "One endpoint per traffic class",
    "The pool gives each class its own endpoint and its own completion handling. The hot class spends a processor core on busy polling to save microseconds. The cold class sleeps on a kernel wait object, so it does not keep a core busy.");
  tbl(s, ["Property", { text: "Hot endpoint", options: { color: ORANGE } }, { text: "Cold endpoint", options: { color: BLUE } }], [
    [bold("Goal"), "low latency for small messages", "high throughput for large ones"],
    [bold("Queue depth"), "64", "512"],
    [bold("Waiting for completions"), "busy polling: a core is spent to save microseconds", "blocking wait: the core is free in the meantime"],
    [bold("Small payloads"), "copied by the provider at the call, so the buffer is free at once", "not applicable"],
    [bold("Transport"), "reliable connection", "reliable connection"],
  ], MX, 1.7, CW, [3.1, 4.6, 4.233], { size: 19, rowH: 0.66, name: "traffic classes of the pool" });
});

def("m04", () => {
  const s = newSlide("m04", "Text above, tall", "What a separate endpoint changes",
    "A separate endpoint removes the shared send queue, and a separate completion queue removes a second, less visible queue.\n\n" +
    "This property is about the queues of the endpoints. What happens below them is measured by E3.");
  B(s, ["A separate endpoint removes the shared send queue",
    "A separate completion queue removes a second, less visible queue: a hot completion behind k cold completions costs k polls",
    "Below the endpoints the packets still meet on one device and one cable. A hardware card arbitrates between queue pairs; on Soft-RoCE the kernel does"], { gap: 12 });
  claim(s, "By construction", "The hot class has its own send queue and its own completion queue, so cold messages and cold completions do not queue ahead of hot ones there.", MX, 5.05, CW, 1.25, { size: 21 });
});

def("m05", () => {
  const s = newSlide("m05", "Text and figure", "Two libraries behind one header",
    "The pool is one small C header and two libraries. The benchmark is one source file that is linked against either, so the library beneath the header is what changes between the two builds. This is the comparison behind the second research question.");
  B(s, ["The pool is one small C header and two libraries",
    "The benchmark is one source file, linked against either",
    "The library beneath the header is what changes between the two builds, which is the comparison behind RQ2",
    "A completion with an error status ends the operation with that error"]);
  const cx = FX + FW / 2;
  node(s, cx - 2.3, 1.75, 4.6, 0.7, "benchmark: one source file", { size: 18, bold: true });
  arrow(s, cx, 2.47, cx, 2.93);
  node(s, cx - 2.3, 2.95, 4.6, 0.7, "one small C header: the pool interface", { size: 18, bold: true, kind: "panel" });
  arrow(s, cx - 0.9, 3.67, FX + 1.35, 4.33); arrow(s, cx + 0.9, 3.67, FX + FW - 1.35, 4.33);
  node(s, FX, 4.35, 2.7, 1.15, two("libscuffedfabric", "on libfabric, the portable interface", 15), { size: 18 });
  node(s, FX + FW - 2.7, 4.35, 2.7, 1.15, two("libscuffedverbs", "on raw RDMA verbs, reliable connected queue pairs", 15), { size: 18 });
});

def("m06", () => {
  const s = newSlide("m06", "Text and figure", "The blob channel: slots",
    "A layer of the cache is a blob: a key and a byte string. Each side registers one memory region with 8 receive slots of 4 mebibytes, 8 staging slots, and a small area for credits. Each slot begins with a header of 64 bytes.");
  B(s, ["A blob is a key and a byte string: here, one layer of the cache",
    "Each side registers one memory region: 8 receive slots of 4 MiB, 8 staging slots, and a small area for credits",
    "Each slot begins with a 64-byte header, then the key, then the chunk"]);
  T(s, "One slot of 4 MiB", FX, 1.7, FW, 0.36, { fontSize: 17, color: GRAY, objectName: "label slot" });
  node(s, FX, 2.1, 1.35, 0.7, [{ text: "header", options: { bold: true, breakLine: true } }, { text: "64 bytes", options: { fontSize: 14 } }], { size: 16, kind: "navy", name: "header" });
  node(s, FX + 1.35, 2.1, 0.9, 0.7, "key", { size: 16, bold: true, kind: "panel", name: "key" });
  node(s, FX + 2.25, 2.1, FW - 2.25, 0.7, "chunk payload", { size: 16, bold: true, kind: "cold", color: BLUE, name: "chunk payload" });
  eq(s, "chunk_max", FX, 3.0, { size: 20 });
  T(s, "One registered memory region on each side", FX, 3.85, FW, 0.36, { fontSize: 17, color: GRAY, objectName: "label region" });
  for (let k = 0; k < 8; k++) {
    rect(s, FX + k * 0.36, 4.3, 0.3, 0.75, { name: "receive slot" });
    rect(s, FX + 3.1 + k * 0.3, 4.3, 0.25, 0.75, { fill: { color: PANEL }, name: "staging slot" });
  }
  T(s, "8 receive slots", FX, 5.1, 2.9, 0.34, { fontSize: 16, objectName: "label receive slots" });
  T(s, "8 staging slots", FX + 3.1, 5.1, 2.5, 0.34, { fontSize: 16, objectName: "label staging slots" });
  more(s, [["Detail", "b02"]]);
});

def("m07", () => {
  const s = newSlide("m07", "Title only", "The blob channel: credits",
    "A credit is the right to write into one specific receive slot of the peer. The sender starts with all eight, and takes one for each chunk.\n\nThe receiver copies the chunk out and then returns the credit, as an 8-byte write on the hot endpoint. With eight slots of 4 mebibytes, up to 32 mebibytes are in flight.");
  gif(s, "m9_credits", "Animation of the blob channel. A sender has 8 staging slots and 8 credits; a receiver has 8 slots of 4 mebibytes. The sender spends one credit and writes a chunk into the matching receive slot. The receiver copies the chunk out and then returns the credit as an 8-byte message. Then all eight slots are in flight at once, the sender waits without credit, and the credits return. The final line is the bound X at most N times B divided by t credit.");
  note(s, "A chunk and its notification are one RDMA write with immediate data. The credit returns on the hot endpoint.", { align: "center", y: 6.28 });
});

def("m08", () => {
  const s = newSlide("m08", "Title and text", "Three design choices",
    "The correctness of the channel rests on three choices. They follow from the ordering facts of the previous part, and each one is used in a proof.");
  B(s, [{ t: "**A chunk and its notification are a single operation,** so the notification comes once the data is in place", num: true },
    { t: "**The receiver posts the credit after it has copied the chunk out,** so a slot is not rewritten while it is being read", num: true },
    { t: "**The credit travels on the hot endpoint,** also when the data used the cold one", num: true }], { gap: 22 });
});

// added in version 9: the four propositions of the next slide in one picture
def("m21", () => {
  const s = newSlide("m21", "Title only", "The blob channel as parcel lockers",
    "Four properties of the channel are proved, and one picture carries all four. A locker is a receive slot, a box is a chunk, and the courier holds one token for each locker, which is the credit.\n\n" +
    "First, a token is handed in with every box and comes back after the locker has been emptied, so a full locker gets no second box. Second, the door sends the arrival message as it closes, so the message does not come before the box. Third, every box names its order and its place in it, so the order of arrival does not matter. Fourth, at most eight boxes are under way, so the pace is set by how fast the tokens return.");
  gif(s, "x3_lockers", "Animation of a wall of eight parcel lockers between a courier, who is the sender, and a customer, who is the receiver. The courier holds eight tokens, one for each locker. Scene for Proposition 5.1: a box goes into a locker together with the token of that locker; while the locker is full its token is away, so no second box goes in; the token returns after the customer has emptied the locker. Scene for Proposition 5.2: the door sends the arrival message as it closes on the box. Scene for Proposition 5.3: three boxes numbered 3, 1 and 2 arrive, each labeled with its order and its place in it, and the customer puts them in the order 1, 2, 3. Scene for Proposition 5.4: all eight lockers are full, the courier waits without a token, and the tokens return on the fast route. A legend maps a locker to a receive slot, a token to a credit, and a box to a chunk of a layer. The last caption reads: throughput is at most 8 lockers times the locker size divided by the time for a token to return.");
  note(s, "Illustration. The next slide states the four propositions.", { align: "center", y: 6.28 });
});

def("m09", () => {
  const s = newSlide("m09", "Title only", "What is proved about the channel",
    "Four properties are proved in the thesis. A slot is not overwritten while it is being read. A notification does not arrive before its data. Reassembly does not depend on the order of arrival. And the throughput is bounded by the window divided by the time a credit needs to come back.");
  tbl(s, ["Proposition", "Statement", "Why"], [
    [bold("5.1"), "A slot in use is not overwritten", "a write is posted to a slot only while the sender holds its credit"],
    [bold("5.2"), "A notification does not precede its data", "the chunk and its notification are one operation"],
    [bold("5.3"), "Reassembly does not depend on arrival order", "each chunk carries blob identifier, total length, offset and length"],
    [bold("5.4"), "The throughput is bounded", "two writes to one slot are separated by one round trip of its credit"],
  ], MX, 1.7, CW, [1.6, 4.7, 5.633], { size: 19, rowH: 0.8, name: "propositions" });
  more(s, [["Proofs", "b03"], ["Bound", "b04"]]);
});

def("m10", () => {
  const s = newSlide("m10", "Text and figure", "Why credits travel on the hot endpoint",
    "The bound explains a design choice. The window is 32 mebibytes, so the link remains the tighter limit as long as a credit returns quickly, which is why the credits are kept off the cold endpoint.");
  B(s, ["The window is 32 MiB in flight",
    "At 10 Gb/s the link is the tighter limit while a credit returns within about 27 ms; at 100 Gb/s, within about 2.7 ms",
    "Credits therefore need to come back quickly, so they are kept off the cold endpoint"]);
  eq(s, "bound", FX, 1.75, { size: 34 });
  eq(s, "window", FX, 3.25, { size: 22 });
  note(s, "X throughput, N slots, B slot size, t credit the time for a credit to return.", { x: FX, y: 3.85, w: FW, h: 0.7 });
});

// added in version 8, after the stall of blobs larger than one slot was traced and fixed (thesis section 5.3)
def("m15", () => {
  const s = newSlide("m15", "Text and figure", "A fourth choice: sending waits for completion",
    "The fourth choice was made after a test failed. Blobs larger than one slot stalled at times when the channel ran on the TCP provider.\n\n" +
    "An earlier version of sending returned as soon as its chunks were posted. A sender with nothing else to do then made no further call into the library, and in our tests queued data advanced only during such calls. The part of a write that the socket had not accepted stayed in the queue of the provider.\n\n" +
    "Sending now returns when every chunk has completed, and it serves both endpoints while it waits. The time we record for a blob therefore ends at completion. The tests pass with two versions of libfabric on the three software providers.\n\n" +
    "* Waiting for the same test on the verbs provider (run R5).");
  B(s, ["Blobs larger than one slot stalled at times on the TCP provider",
    "**The cause.** Sending returned once the chunks were posted, and queued data advanced only during calls into the library",
    "**The change.** Sending returns when every chunk has completed, and it serves both endpoints while it waits"], { gap: 14 });
  const h = 0.78, a = 1.45, r = 1.0;
  T(s, "Before", FX, 1.7, FW, 0.36, { fontSize: 17, color: GRAY, objectName: "label before" });
  node(s, FX, 2.1, a, h, "post the chunks", { size: 16, name: "before: post the chunks" });
  node(s, FX + a, 2.1, r, h, "return", { size: 16, bold: true, name: "before: return" });
  node(s, FX + a + r, 2.1, 1.5, h, "no further call", { size: 16, dash: "dash", color: GRAY, name: "before: no further call" });
  node(s, FX + a + r + 1.5, 2.1, FW - a - r - 1.5, h, "part of a write still queued", { size: 16, kind: "hot", color: ORANGE, name: "before: data still queued" });
  T(s, "Now", FX, 3.3, FW, 0.36, { fontSize: 17, color: GRAY, objectName: "label now" });
  node(s, FX, 3.7, a, h, "post the chunks", { size: 16, name: "now: post the chunks" });
  node(s, FX + a, 3.7, FW - a - r, h, "serve both endpoints until every chunk has completed", { size: 16, kind: "panel", name: "now: serve both endpoints" });
  node(s, FX + FW - r, 3.7, r, h, "return", { size: 16, bold: true, name: "now: return" });
  arrow(s, FX, 4.72, FX + FW, 4.72, { name: "time axis" });
  T(s, "time", FX + FW - 0.8, 4.76, 0.8, 0.3, { fontSize: 14, color: GRAY, align: "right", objectName: "label time" });
  note(s, "The tests pass with libfabric 1.17.0 and 2.7.0 on the TCP, RXM and shared-memory providers.", { x: FX, y: 5.05, w: FW, h: 0.62 });
  star(s, "Waiting for the same test on the verbs provider and on RXM over verbs (run R5).", MX, 5.85, CW, 0.5);
});

def("m11", () => {
  const s = newSlide("m11", "Title only", "Five ways to signal that data arrived",
    "The receiver has to learn that a write has landed. There are five mechanisms for that, and each rests on a different ordering fact. The default is the completion with immediate data.\n\n" +
    "Experiment E5 measures them, and we would replace the default if another mechanism lowers the 99th percentile. The fourth cannot be measured on our two pairs of servers, because the verbs provider has no counters.");
  const bottom = tbl(s, ["No.", "Signal", "What the receiver does", "Rests on", "Remark"], [
    ["1", bold("Completion with immediate data"), "reads its completion queue", "fact 3", "the default; one posted receive per write"],
    ["2", bold("Flag in the payload"), "polls a byte at the end of the buffer", "nothing, for a multi-packet message", "safe for single-packet messages"],
    ["3", bold("Sentinel write"), "polls a second, tiny write posted after the data", "fact 1, if the provider keeps write order", "the shared-memory provider does not"],
    ["4", bold("Remote-write counter"), "reads a counter the provider increments", "counts arrivals without identifying them", "TCP did not count; the verbs provider has no counters"],
    ["5", bold("Write, then read"), "the sender reads 8 bytes back and waits", "fact 1", "the signal goes to the sender"],
  ], MX, 1.62, CW, [0.65, 2.7, 3.2, 2.75, 2.633], { size: 17, rowH: 0.74, name: "completion signals" });
  note(s, "Fact 1: operations execute in order. Fact 2: placement within one message is not ordered. Fact 3: a completion follows placement.", { y: bottom + 0.08, h: 0.42 });
});

def("m12", () => {
  const s = newSlide("m12", "Two columns", "Into the serving engine",
    "The connector implements the connector interface of the vLLM engine on top of the blob channel. One request passes through these eight steps: the prefill instance runs with an output of one token, the connector sends one blob per layer, and the decode instance starts without recomputing the prompt.");
  B(s, [{ t: "The proxy assigns a transfer identifier", num: true },
    { t: "The prefill instance runs with an output length of one token", num: true },
    { t: "For each layer: gather the blocks from the GPU, copy them to host memory, encode", num: true },
    { t: "One blob per layer, keyed by transfer and layer", num: true }], { gap: 14 });
  B2(s, [{ t: "A done marker follows on the hot class", num: true },
    { t: "The proxy forwards the request to the decode instance", num: true },
    { t: "Its worker waits for each layer, decodes, and writes the block table on the GPU", num: true },
    { t: "Decoding starts and tokens stream", num: true }], { gap: 14, start: 5 });
  vline(s, 6.66, Y0 + 0.05, 3.9);
  more(s, [["Detail", "b18"]]);
});

def("m13", () => {
  const s = newSlide("m13", "Text above, tall", "When a layer is lost",
    "This slide covers what happens when a layer is lost. A layer that does not arrive within its timeout is reported as a failed load, and the engine recomputes it. One of the tests drops a layer on purpose.\n\n" +
    "There is one limit here, which is that the connector's sender still keeps one queue for both classes.");
  B(s, ["A layer that misses its timeout is reported as a failed load, and the engine recomputes it",
    "A test drops a layer on purpose",
    "If the RDMA channel cannot be opened, the connector falls back to TCP and records an event",
    "Limit: the connector's sender keeps one queue for both classes. A send queue per class is future work"], { gap: 12 });
  claim(s, "", "A lost layer costs time, because the engine recomputes it instead of using incomplete data.", MX, 5.15, CW, 0.95, { size: 22 });
});

def("m14", () => {
  const s = newSlide("m14", "Text and figure", "The cost of staging through host memory",
    "Because the network cards in the laboratory cannot reach the GPUs directly, each block is copied to host memory first. The cost of that copy relative to the wire time depends on the link rate and the copy rate.\n\n" +
    "For an assumed copy rate it is small at 10 gigabits and large at 100. E7 times the real copies.");
  B(s, ["The network cards cannot reach the GPUs directly, so blocks are copied to host memory first",
    "Relative to the wire time, the copy costs the link rate over eight times the copy rate",
    "Experiment E7 times the real copies"]);
  eq(s, "staging", FX, 1.75, { size: 26, maxW: FW });
  T(s, "Copy time as a share of the wire time", FX, 3.05, FW, 0.38, { fontSize: 18, color: GRAY, objectName: "label" });
  stat(s, "6 %", "at 10 Gb/s", FX, 3.45, 2.7, { size: 54, lh: 0.4 });
  stat(s, "62 %", "at 100 Gb/s", FX + 2.95, 3.45, 2.7, { size: 54, lh: 0.4 });
  note(s, "Computed for an assumed copy rate of 20 GB/s.", { x: FX, y: 5.05, w: FW, h: 0.45, size: 17 });
});

// ------------------------------------------------------------------ NUMA (added in version 9; thesis section 5.6)
def("m31", () => {
  const s = newSlide("m31", "Title only", "NUMA: two sorting halls and one corridor",
    "The last topic of this part is where the registered memory lies inside one server. A server with two processor sockets is like a sorting center with two halls and one corridor. A hall is a NUMA node, the corridor is the interconnect, and the loading bay is the network card, which is attached to one hall. The shelf is the registered memory of the pool, and the worker is the thread that copies.\n\n" +
    "With shelf and worker in the hall of the bay, no trip goes through the corridor. With the worker in the other hall, every copy does. With the shelf in the other hall, every delivery does. Today the shelf goes up in the hall where the worker first fills it.");
  gif(s, "x5_numa_halls", "Animation with three floor plans of two sorting halls, A and B, joined by one corridor, with a loading bay at hall A. First plan: the shelf and the worker are in hall A; parcels go from the bay to the shelf and from the shelf to the worker, and no trip goes through the corridor. Second plan: the shelf is in hall A and the worker in hall B; every copy goes through the corridor. Third plan: the shelf is in hall B; every delivery goes through the corridor, wherever the worker stands. A legend maps a hall to a NUMA node, the corridor to the interconnect, the loading bay to the network card, the shelf to the registered memory, and the worker to the thread that copies. The last caption reads: today the shelf goes up in the hall where the worker first fills it.");
  note(s, "Illustration. The network card is attached to one node, and the pool does not choose the node of its memory today.", { align: "center", y: 6.28 });
});

def("m32", () => {
  const s = newSlide("m32", "Text and figure", "NUMA: memory has a location",
    "On a server with more than one processor socket, each socket has its own memory and its own I/O buses, and Linux calls a socket with its memory a node. What an access costs depends on the distance between the node of the memory and the node of the processor or I/O bus that makes it. A network card is attached to the bus of one node, so the placement of memory matters for a device as it does for a thread.");
  B(s, ["With more than one processor socket, a server has non-uniform memory access (NUMA)",
    "Each socket has its own memory and I/O buses, and Linux calls a socket with its memory a node",
    "The cost of an access depends on the distance between the node of the memory and the node of the processor or I/O bus that makes it",
    "A network card or a GPU is attached to the bus of one node, so the placement of memory matters for a device as it does for a thread"], { size: 20, gap: 12 });
  const pw = 2.5, x1 = FX, x2 = FX + FW - pw, py = 1.98, ph = 2.62;
  T(s, "interconnect", FX, 1.62, FW, 0.3, { fontSize: 15, color: GRAY, align: "center", objectName: "label interconnect" });
  [[x1, "Node 0", "network card"], [x2, "Node 1", "GPU"]].forEach(([x, name, dev]) => {
    rect(s, x, py, pw, ph, { fill: { color: PANEL }, line: { color: PANEL, width: 0 }, name: "panel " + name });
    T(s, name, x + 0.18, py + 0.06, pw - 0.36, 0.36, { fontSize: 17, bold: true, color: NAVY, valign: "middle", objectName: "label " + name });
    ["processor cores", "memory", "I/O bus"].forEach((t, k) => node(s, x + 0.18, py + 0.48 + k * 0.69, pw - 0.36, 0.56, t, { size: 16, name: name + " " + t }));
    arrow(s, x + pw / 2, py + 0.48 + 2 * 0.69 + 0.56, x + pw / 2, 5.02, { head: false, color: INK, width: 1.5, name: "bus of " + name });
    node(s, x + 0.18, 5.02, pw - 0.36, 0.56, dev, { size: 16, bold: true, name: dev });
  });
  arrow(s, x1 + pw, py + ph / 2, x2, py + ph / 2, { both: true, color: NAVY, width: 2.5, name: "interconnect" });
  note(s, "After the Linux kernel documentation, \u201cWhat is NUMA?\u201d", { x: FX, y: 5.72, w: FW, h: 0.4, size: 15 });
});

def("m33", () => {
  const s = newSlide("m33", "Text and figure", "NUMA: where the arena lands today",
    "Where does the arena of the pool lie today? Linux allocates a page on the node of the processor on which the allocating thread runs, unless a policy says otherwise. The pool maps its arena and writes zeros to it in the thread that opens the pool, so the arena lies where that thread happened to run. Registration then pins the pages, and the scheduler remains free to move the thread.");
  B(s, ["Unless a policy says otherwise, Linux allocates a page on the node of the processor on which the allocating thread runs",
    "The pool maps its arena and writes zeros to all of it in the thread that opens the pool",
    "So the arena lies on the node where that thread happened to run",
    "Registration pins the pages, and the scheduler remains free to move the thread"], { size: 20, gap: 12 });
  const steps = [["1   The pool is opened", "The arena is mapped and filled with zeros, so its pages are allocated on the node of this thread"],
    ["2   The arena is registered", "The pages are pinned for as long as the pool exists"],
    ["3   Later, the scheduler moves the thread", "The memory stays on the node where it was placed"]];
  steps.forEach(([a, b], k) => {
    const y = 1.75 + k * 1.38;
    node(s, FX, y, FW, 1.05, two(a, b, 15), { size: 17, kind: "panel", align: "left", margin: 10, name: "step " + (k + 1) });
    if (k < 2) arrow(s, FX + FW / 2, y + 1.07, FX + FW / 2, y + 1.36, { color: NAVY, width: 2 });
  });
  note(s, "Read from the code of the pool and from the Linux kernel documentation on memory policy and on pinned pages.", { x: FX, y: 5.72, w: FW, h: 0.6, size: 15 });
});

def("m34", () => {
  const s = newSlide("m34", "Text below", "NUMA: three cases on a server with two nodes",
    "On a server with two nodes this leaves three cases, the three rows of the picture with the halls. With arena and thread on the node of the card, nothing crosses the interconnect. With the thread on the other node, every copy crosses it. With the arena on the other node, every transfer of the card crosses it.\n\n" +
    "The staging copy from the GPU follows the same rule, and if the GPU and the card are on different nodes, which of the two to favor has to be measured.");
  tbl(s, ["Arena of the pool", "Thread that copies", "What crosses the interconnect"], [
    ["on the node of the card", "on the node of the card", bold("nothing")],
    ["on the node of the card", "on the other node", bold("every copy")],
    ["on the other node", "on either node", bold("every transfer of the card")],
  ], MX, 1.68, CW, [3.7, 3.7, 4.533], { size: 20, rowH: 0.62, name: "three cases" });
  B(s, ["The staging copy between GPU memory and host memory follows the same rule, so the copy rate can depend on the placement",
    "If the GPU and the card are attached to different nodes, the arena is local to only one of the two, and which to favor is a matter for measurement"], { size: 20, gap: 10 });
});

def("m35", () => {
  const s = newSlide("m35", "Text and figure", "NUMA: what a NUMA-aware pool does",
    "A NUMA-aware pool removes the dependence on chance in four steps. It reads the node of the network card. It binds the arena to that node before the first write, which in the code belongs between mapping the arena and writing zeros to it. It registers the arena only then. And it keeps the copying threads on processors of that node.\n\n" +
    "This was planned at the start of the work and is not implemented.");
  B(s, [{ t: "**Read the node of the network card.** The kernel reports it for every PCI device, and reports \u22121 if the firmware does not supply it", num: true },
    { t: "**Bind the arena to that node before the first write.** A policy governs the pages that are allocated after it is installed", num: true },
    { t: "**Register the arena only then**", num: true },
    { t: "**Keep the threads that copy** into and out of the slots on processors of that node", num: true }], { size: 20, gap: 12 });
  T(s, "Order of the steps when the pool is opened", FX, 1.66, FW, 0.36, { fontSize: 17, color: GRAY, objectName: "label order" });
  const bw = 3.5, ys = [2.12, 2.98, 3.84, 4.7];
  [["map the arena", false], ["bind it to the node of the card", true], ["write zeros to all of it", false], ["register it", false]].forEach(([t, isNew], k) => {
    node(s, FX, ys[k], bw, 0.6, t, { size: 17, bold: isNew, color: isNew ? NAVY : INK, dash: isNew ? "dash" : "solid", name: "call " + (k + 1) });
    if (k < 3) arrow(s, FX + bw / 2, ys[k] + 0.62, FX + bw / 2, ys[k + 1] - 0.02, { color: NAVY, width: 2 });
  });
  T(s, "the step that is not in the code today", FX + bw + 0.2, ys[1], FW - bw - 0.2, 0.6, { fontSize: 15, color: GRAY, valign: "middle", objectName: "label new step" });
  claim(s, "", "Planned at the start of the work, and not implemented.", FX, 5.55, FW, 0.7, { size: 18 });
  note(s, "The benchmark already pins its two threads. The pool and the connector do not.", { x: MX, y: 5.72, w: 5.8, h: 0.6, size: 16 });
});

def("m36", () => {
  const s = newSlide("m36", "Text and figure", "NUMA: status on this testbed",
    "For our measurements this means the following. Servers 2, 3 and 4 have one processor socket each, which normally forms a single node, and for such a server the vendor of the cards states that no tuning of this kind is required. So we do not expect the results to depend on the placement, and the placement cannot be evaluated on this testbed.\n\n" +
    "On a server with two sockets the three cases can be compared without new code, by starting the benchmark with its memory bound to one node and its threads pinned to either.");
  B(s, ["Servers 2, 3 and 4 have one processor socket each, which normally forms a single node",
    "For a server with a single node, the vendor of the ConnectX cards states that no tuning of this kind is required",
    "So these measurements are not expected to depend on the placement, and the placement cannot be evaluated here",
    "On a server with two sockets the three cases can be compared without new code: the benchmark is started with its memory bound to one node and its two threads pinned to either"], { size: 20, gap: 12 });
  const bottom = tbl(s, ["Server", "Processor sockets", "Nodes that Linux reports"], [
    ["1", "", ""], ["2", "1", ""], ["3", "1", ""], ["4", "1", ""],
  ], FX, 1.72, FW, [1.2, 2.1, 2.383], { size: 18, rowH: 0.5, align: ["left", "center", "center"], name: "sockets and nodes" });
  star(s, "Waiting for the hardware record (run R0): the number of nodes on each server, and the board of server 1.", FX, bottom + 0.12, FW, 0.75);
  note(s, "Vendor statement: NVIDIA, performance tuning notes for ConnectX-4 and later adapter cards.", { x: FX, y: bottom + 1.0, w: FW, h: 0.6, size: 15 });
});
