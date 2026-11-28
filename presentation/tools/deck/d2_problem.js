// Part III: the problem, the research questions, the contributions and the scope.
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, tbl, CH } = require("./lib");

const cold = (t) => ({ text: t, options: { bold: true, color: BLUE } });
const hot = (t) => ({ text: t, options: { bold: true, color: ORANGE } });

opener("p", "Now we turn to the problem: how large the cache is, what else crosses the link with it, and why the order in which things are sent matters.");

def("p01", () => {
  const s = newSlide("p01", "Title only", "How large the cache is",
    "The size follows from the shape of the model. For Granite 3.3 2B a token costs 80 kibibytes over the 40 layers, and a prompt of 2,048 tokens is 160 mebibytes.\n\nOn the laboratory link those bytes need 134.2 milliseconds. This number is arithmetic, and it is a lower bound for the transfer on that link.");
  gif(s, "m2b_cache_size", "Animation. One token in one layer takes 2 times 8 times 64 times 2 bytes, which is 2 kibibytes. Forty layers stack to 80 kibibytes per token. A prompt of 2,048 tokens stretches the stack to 160 mebibytes. A bar then fills to 134.2 milliseconds, the time the bytes need on a 10 gigabit link.");
  note(s, "Computed from the shape of the model and the link rate.", { align: "center", y: 6.28 });
});

def("p02", () => {
  const s = newSlide("p02", "Text and figure", "The size in symbols",
    "A layer keeps one key and one value for each head and each token, which is where the factor two comes from. With the numbers of Granite 3.3 2B, one token is 2,048 bytes in a layer. A prompt of 2,048 tokens is 4 mebibytes per layer and 160 mebibytes in total.");
  B(s, ["A layer keeps one key and one value for each head and each token",
    "One token: 2 KiB per layer, 80 KiB over the 40 layers",
    "A prompt of 2,048 tokens: 4 MiB per layer, 160 MiB in total"]);
  eq(s, "cache_layer", FX, 1.78, { size: 26 });
  eq(s, "cache_total", FX + 3.2, 1.78, { size: 26 });
  tbl(s, ["Symbol", "Meaning", "Granite 3.3 2B"], [
    [{ text: "h", options: { italic: true } }, "key-value heads", "8"],
    [{ text: "d", options: { italic: true } }, "dimensions per head", "64"],
    [{ text: "w", options: { italic: true } }, "bytes per value", "2"],
    [{ text: "T", options: { italic: true } }, "tokens in the prompt", "2,048"],
    [{ text: "L", options: { italic: true } }, "layers", "40"],
  ], FX, 2.75, FW, [1.15, 2.6, 1.93], { size: 18, rowH: 0.5, align: ["left", "left", "right"], name: "symbols" });
});

def("p03", () => {
  const s = newSlide("p03", "Text and figure", "What the bytes cost on the wire",
    "At 10 gigabits per second the 160 mebibytes need 134.2 milliseconds, before any header. With the headers of RoCE version 2 it is about 137 milliseconds with packets of 4,096 bytes and 145 with packets of 1,024 bytes.\n\n" +
    "These are lower bounds from arithmetic, so a measured transfer will take longer.");
  B(s, ["On the laboratory link the bytes alone need 134.2 ms",
    "With packet headers: about 137 ms with 4,096-byte packets, 145 ms with 1,024-byte packets",
    "These are lower bounds from arithmetic, so a measured transfer will take longer"]);
  eq(s, "wire_num", FX, 1.8, { size: 22, maxW: FW });
  stat(s, "134.2 ms", "160 MiB at 10 Gb/s, before headers", FX, 3.3, FW, { size: 60 });
  more(s, [["Detail", "b14"]]);
});

def("p04", () => {
  const s = newSlide("p04", "Title only", "Two kinds of traffic share the link",
    "The traffic between the two servers is mixed. The cache is megabytes, and a single block of it is not urgent.\n\nThe other rows are a few bytes each, and something is waiting for each of them: the decode server, the sender's next block, or the next token.");
  const bottom = tbl(s, ["Traffic", "Size", "What waits on it", "Class"], [
    ["Prefill cache, one layer", "4 MiB for 2,048 tokens", "nothing, until the whole request has arrived", cold("cold")],
    ["End-of-request marker", "under 100 bytes", "the decode server", hot("hot")],
    ["Flow-control credit", "8 bytes", "the sender's next block", hot("hot")],
    ["Token identifiers, request metadata", "tens of bytes", "the request itself", hot("hot")],
    ["Decode-side cache update", "2 KiB per token per layer", "the next token of a running request", hot("hot")],
  ], MX, 1.7, CW, [3.9, 2.9, 4.1, 1.033], { size: 19, rowH: 0.66, name: "traffic classes" });
  note(s, "Sizes for Granite 3.3 2B.", { y: bottom + 0.12, h: 0.4 });
});

def("p05", () => {
  const s = newSlide("p05", "Two columns", "Cold and hot",
    "We call the first kind cold and the second hot. The ratio between one cache block and one credit is about half a million to one. In one queue, the small one waits for the large one.");
  B(s, [{ t: "Cold: bulk", plain: true, bold: true, color: BLUE, size: 26 }, "Megabytes", "A single block is not urgent", "Example: one layer of the cache, 4 MiB"], { size: 24 });
  B2(s, [{ t: "Hot: urgent", plain: true, bold: true, color: ORANGE, size: 26 }, "Bytes", "Something waits for each one", "Example: a flow-control credit, 8 bytes"], { size: 24 });
  vline(s, 6.66, Y0 + 0.05, 2.75);
  hline(s, MX, 4.72, CW);
  T(s, "524,288 to 1", MX, 4.95, 5.2, 1.0, { fontSize: 54, bold: true, color: NAVY, valign: "middle", objectName: "ratio" });
  T(s, "One 4 MiB block of the cache against one 8-byte credit. In one queue they stand in the same line.", 6.98, 4.95, 5.65, 1.0, { fontSize: 22, valign: "middle", objectName: "ratio explained" });
});

def("p06", () => {
  const s = newSlide("p06", "Title only", "Head-of-line blocking",
    "This is the problem in its simplest form. A message of 64 bytes arrives behind four blocks of one mebibyte and waits 3.36 milliseconds, although its own transmission takes a few microseconds.\n\nWith one endpoint per class the message has its own send queue, so the blocks are not in front of it there. Below the endpoints the packets still meet, and experiment E3 measures whether that matters.");
  gif(s, "m3_head_of_line", "Animation in two parts. First, one send queue: a 64-byte message waits behind four 1 mebibyte blocks while a clock counts to 3.36 milliseconds. Second, one endpoint per class: the small message travels on the hot endpoint, where it has its own send queue; this is marked follows from the design. Both endpoints lead into one device and one cable, marked measured by E3.");
  note(s, "The link carries one block at a time: 0.84 ms for each block of 1 MiB at 10 Gb/s.", { align: "center", y: 6.28 });
});

def("p07", () => {
  const s = newSlide("p07", "Text and figure", "The wait, and what the design changes",
    "The wait is the time the link needs for what is ahead in the queue.\n\nThere are two separate statements here. With one endpoint per class the hot message has its own send queue, which follows from the design. Below the endpoints the packets still meet, and that part has to be measured.");
  B(s, ["The message itself needs a few microseconds on the wire",
    "**From the design:** with one endpoint per class, the message has its own send queue, so blocks do not queue ahead of it there",
    "**Measured by experiment E3:** below the endpoints, the packets of both classes still meet on one device and one cable"]);
  eq(s, "hol_num", FX, 1.8, { size: 22, maxW: FW });
  stat(s, "3.36 ms", "behind four blocks of 1 MiB, at 10 Gb/s", FX, 3.5, FW, { size: 60 });
});

def("p08", () => {
  const s = newSlide("p08", "Text and figure", "What a queueing model predicts",
    "A queueing model says how large the effect can be. In the formula of Pollaczek and Khinchine the mean wait grows with the second moment of the service time. So a few very large messages raise the wait of the small ones as well.");
  B(s, ["The mean wait grows with the second moment of the service time",
    "A few very large messages raise the mean wait for all messages",
    "So the small messages wait longer because of the large ones"]);
  T(s, "Mean wait in one queue (Pollaczek and Khinchine)", FX, 1.75, FW, 0.4, { fontSize: 18, color: GRAY, objectName: "label" });
  eq(s, "pk", FX, 2.3, { size: 32 });
  eq(s, "pk_defs", FX, 3.9, { size: 24 });
  note(s, "S is the time one message of s bytes holds the link, λ the arrival rate, ρ the load, C the link rate.", { x: FX, y: 4.85, w: FW, h: 0.8 });
});

// added in version 9: the three rows of the next slide as a picture
def("p21", () => {
  const s = newSlide("p21", "Title only", "Sharing one link: a post office",
    "This picture shows where the three numbers on the next slide come from. One customer has a single letter, and every customer ahead of him brings forty parcels. The letter is a small urgent message, forty parcels are one large message, and the window is the link.\n\n" +
    "With one line for everyone, the letter waits for every parcel ahead of it. With a line for letters, it waits for the rest of one customer. If the clerk takes the letter between two parcels, it waits for one parcel.\n\n" +
    "A line for letters follows from the design. When the clerk switches is decided below our software, and experiment E3 measures it.");
  gif(s, "x2_post_office", "Animation in three rows at a post office window. A customer with one letter waits while three customers ahead bring 40 parcels each. Row one, one line for everyone: the letter waits for 120 parcels, everyone ahead. Row two, a line for letters, and the clerk first finishes the customer at the window: the letter waits for up to 40 parcels, the rest of one customer. Row three, a line for letters, and the clerk takes the letter between two parcels: it waits for 1 parcel. A legend maps the letter to a small urgent message, 40 parcels to one large message, and the window to the link. The last caption reads: a line for letters is the design; when the clerk switches is what E3 measures.");
  note(s, "Illustration with made-up numbers of customers and parcels. The next slide gives the three waits from the model.", { align: "center", y: 6.28 });
});

def("p09", () => {
  const s = newSlide("p09", "Text below", "Three ways to share the link",
    "For an assumed load the model gives three numbers. The step from the first row to the second comes from giving each class its own queue pair.\n\nThe step to the third depends on what sits below the queue pairs, because a hardware card arbitrates packet by packet and the software driver may not. These three numbers come from the model.");
  const bottom = tbl(s, ["Arrangement of the queues", "Mean wait of a hot message"], [
    ["One queue for both classes", "0.69 ms"],
    ["Two queues, hot served first, cold not interrupted", "0.26 ms"],
    ["Two queues, hot packets interleaved between cold packets", { text: "1.07 µs", options: { bold: true } }],
  ], MX, 1.68, CW, [8.4, 3.533], { size: 20, rowH: 0.6, align: ["left", "right"], name: "three arrangements" });
  B(s, ["From the first row to the second: this comes from a queue pair per class",
    "From the second to the third: depends on what sits below the queue pairs, which experiment E3 measures"], { gap: 10 });
  note(s, "Model output for an assumed load: link of 10 Gb/s, cold messages of 1 MiB at 60 % load, hot messages of 4 KiB at 10,000 per second.", { y: bottom + 0.1, h: 0.5 });
});

def("p10", () => {
  const s = newSlide("p10", "Title and text", "Existing systems split the phases",
    "The split itself is established. DistServe and Splitwise showed that the two phases have different bottlenecks. Mooncake builds its architecture around the cache. The vLLM engine offers a connector interface, and NVIDIA's NIXL is the usual transport under it.\n\n" +
    "These systems assume a data-center network.");
  B(s, ["**DistServe, Splitwise:** separate prefill and decode, and treat the cache transfer as one bulk copy",
    "**Mooncake:** an architecture built around the cache",
    "**vLLM:** a connector interface for split serving, with NVIDIA NIXL as the usual transport",
    "**LMCache, llm-d, Dynamo:** a cache layer for the same engine, and the pattern packaged for clusters",
    "They assume a data-center network, and the mix of traffic on the link is not their subject"]);
});

def("p11", () => {
  const s = newSlide("p11", "Title only", "Five gaps",
    "Five gaps motivate the design. The first is the one this thesis is about: the transports we studied are built for bulk and do not distinguish an 8-byte credit from a 4 mebibyte block when they choose a queue.\n\n" +
    "The other four are reasons why we did not reuse an existing transport on this hardware.");
  tbl(s, ["No.", "Gap", "What we found"], [
    ["1", { text: "Built for bulk", options: { bold: true } }, "The transports we studied do not distinguish an 8-byte credit from a 4 MiB block when they choose a queue"],
    ["2", { text: "One kind of adapter", options: { bold: true } }, "The libfabric back end of NIXL looks for Slingshot, then a cloud adapter, then TCP"],
    ["3", { text: "Side effects", options: { bold: true } }, "A leak of hundreds of megabytes per minute, traced to memory hooks of a transport library"],
    ["4", { text: "Quiet failures", options: { bold: true } }, "In a production file system: a race that returned incorrect data, and a reconnection fault"],
    ["5", { text: "Unchecked completions", options: { bold: true } }, "A benchmark that does not read the status counts a failed operation as a very fast one"],
  ], MX, 1.7, CW, [0.8, 3.0, 8.133], { size: 19, rowH: 0.74, name: "five gaps" });
});

def("p12", () => {
  const s = newSlide("p12", "Statement", "The gap",
    "This is the gap that the thesis addresses. Our contribution is the classification and scheduling of mixed traffic, and we do not propose a faster bulk path.");
  B(s, [{ t: "In the systems studied here, the traffic between the two halves of a split inference server is not treated as mixed. We do that on commodity Ethernet, with software RoCE and with the cache staged through host memory.", plain: true, size: 28 }]);
  T(s, "The contribution is the classification and scheduling of that mixed traffic.", 1.3, 5.25, 10.73, 0.7, { fontSize: 20, color: GRAY, objectName: "gloss" });
});

def("p13", () => {
  const s = newSlide("p13", "Title only", "Research questions",
    "There are three research questions. The first asks whether the separation works, on the software path and on the hardware path. The second asks what the portable interface costs, which is why the pool is implemented twice. The third asks how much of the time to first token the transfer is, and whether deciding per transfer reduces it.");
  tbl(s, ["No.", "Question", "Experiments"], [
    [{ text: "RQ1", options: { bold: true, color: NAVY } }, "Does giving each traffic class its own endpoint keep the tail latency of small messages flat while bulk transfers run, on software RoCE and on hardware RoCE?", "E3, E4"],
    [{ text: "RQ2", options: { bold: true, color: NAVY } }, "What does a portable transport interface cost against the raw RDMA interface on the path small messages take?", "E1, E2, E5"],
    [{ text: "RQ3", options: { bold: true, color: NAVY } }, "How much of the time to first token is cache transfer, and do per-transfer routing, compression and spilling reduce it against a transport that treats every transfer alike?", "E6, E7, E8"],
  ], MX, 1.7, CW, [1.0, 9.0, 1.933], { size: 19, rowH: 1.15, name: "research questions" });
  note(s, "The first half of RQ3 is measured on the serving path. The decisions in its second half are made by components that are evaluated separately.", { y: 5.82, h: 0.6 });
});

def("p14", () => {
  const s = newSlide("p14", "Title and text", "Contributions: the transport",
    "There are six contributions, in two groups. The first three are the transport. The pool exists twice behind one interface so that the cost of the portable interface can be measured. The channel comes with proofs. The connector puts the middleware under a production serving engine.");
  B(s, [{ t: "**A dual-endpoint pool.** One endpoint per traffic class, implemented twice behind one interface: on libfabric and on raw RDMA verbs", num: true },
    { t: "**A blob channel.** Credit-based flow control, with proofs that a slot in use is not overwritten, that a notification follows its data, and that the throughput is bounded", num: true },
    { t: "**A connector.** The channel attached to the vLLM serving engine for split serving", num: true }], { gap: 20 });
});

def("p15", () => {
  const s = newSlide("p15", "Title and text", "Contributions: decisions, bytes and method",
    "These are the other three. The analysis of the classifier and the controller produced two negative results, which we count as contributions. The quantizer and the storage tier reduce the bytes and move them. And the method stores each result with the commands that produced it and a record of the hardware.");
  B(s, [{ t: "**A classifier and a rule-tree policy.** With a proof that size thresholds do not recognize decode traffic, and an analysis of the controller's switching rule", num: true },
    { t: "**A quantizer and a storage tier.** A packed wire format, and an NVMe tier with a model of its batching", num: true },
    { t: "**A measurement method.** Results are stored with the commands that produced them and a record of the hardware", num: true }], { gap: 20, start: 4 });
});

def("p16", () => {
  const s = newSlide("p16", "Text above", "Scope",
    "The scope is narrow. The work covers inference on two machines joined by one link, and training and clusters with a switch are outside it. The cache is staged through host memory, because the network cards in the laboratory cannot reach the GPUs directly.\n\n" +
    "We also do not claim a faster way of moving bulk data.");
  B(s, ["In scope: inference, on two machines joined by one link",
    "Outside the scope: training, and clusters with a switch",
    "The cache is staged through host memory, because the network cards in the laboratory cannot reach the GPUs directly"], { gap: 10 });
  claim(s, "", "The subject is the order in which data is sent, the number of bytes sent, and the place where they wait. A faster way of moving bulk data is outside the scope.", MX, 4.2, CW, 1.4, { size: 23 });
});
