// Part X: conclusions (related work, answers, limitations, future work, closing).
const { pres, A, STATIC, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, tbl, CH } = require("./lib");

const bold = (t) => ({ text: t, options: { bold: true } });
const head = (t) => ({ t, plain: true, bold: true, color: NAVY, size: 24 });

opener("z", "What remains is to place the work among others, to answer the three questions as far as today's evidence allows, and to say what is still open.");

def("z01", () => {
  const s = newSlide("z01", "Title only", "Related work: serving and transfer",
    "The systems for disaggregated inference separate prefill and decode and assume a data-center network. We take the split as given and study the mix of traffic on the link, without that network. Among the transfer libraries we looked at, we did not find one that separates traffic by urgency or one that targets software RoCE.");
  const bottom = tbl(s, ["Area", "Systems", "How this work differs"], [
    [bold("Disaggregated inference"), "DistServe, Splitwise, Mooncake, Dynamo, llm-d, LMCache", "We take the split as given and study the mix of traffic on the link, without a data-center network"],
    [bold("Libraries for cache transfer"), "NIXL, fabric-lib, UCCL", "We did not find one that separates traffic by urgency or one that targets software RoCE"],
    [bold("RDMA over Ethernet at scale"), "DCQCN, Slingshot", "Two machines and a cable, where the effects we study are inside one host"],
  ], MX, 1.7, CW, [3.3, 3.5, 5.133], { size: 19, rowH: 0.95, name: "related work, first part" });
  note(s, "Slingshot separates traffic classes inside the network: the in-network counterpart of what the middleware does at the endpoints.", { y: bottom + 0.15, h: 0.7, size: 17 });
});

def("z02", () => {
  const s = newSlide("z02", "Title only", "Related work: interfaces, scheduling, compression",
    "For the interfaces we measure one narrow quantity. Job-level scheduling is complementary to what we do. The quantizer is assembled from published methods, and we do not propose a new compression method.");
  tbl(s, ["Area", "Systems", "How this work differs"], [
    [bold("Transport interfaces"), "UCX, libfabric", "One narrow quantity: the cost of libfabric against raw verbs for small messages, with the rest of the setup kept the same"],
    [bold("Small messages, scheduling"), "NCCL, TACCL, Cassini", "A scheduler decides when jobs use the network; the middleware decides which message goes first"],
    [bold("Compression of the cache"), "KIVI, TurboQuant, QJL", "A packed format with measured sizes, applied per transfer and built from the published methods"],
  ], MX, 1.7, CW, [3.3, 3.5, 5.133], { size: 19, rowH: 0.95, name: "related work, second part" });
});

// one research question: the question, what is established, what is waiting, the limit
function answer(id, n, title, q, est, waiting, limit, notes) {
  def(id, () => {
    const s = newSlide(id, "Title only", title, notes);
    claim(s, "RQ" + n, q, MX, 1.62, CW, 1.2, { size: 20 });
    tbl(s, null, [
      [bold("Established"), est],
      [{ text: "* Waiting", options: { bold: true, italic: true, color: ORANGE } }, { text: waiting, options: { italic: true, color: ORANGE } }],
      [bold("Limit"), limit],
    ], MX, 3.1, CW, [2.3, 9.633], { size: 19, rowH: 0.95, name: "answer to question " + n });
  });
}
answer("z03", 1, "Research question 1: one endpoint per class",
  "Does giving each traffic class its own endpoint keep the tail latency of small messages flat while bulk transfers run, on software RoCE and on hardware RoCE?",
  "With one endpoint per class, the hot class has its own send queue, so cold messages do not queue ahead of hot ones there. This follows from the design.",
  "The p99 of a 64-byte round trip under 1 MiB writes: shared endpoint, separate endpoints and no stream, on both pairs of servers (E3, run R2).",
  "One pair, one cable and one sender, without a switch and without loss. The answer is for the pool, since the connector's sender still serializes both classes.",
  "For the first question the queue property is established and the latencies are waiting.\n\n* Fill this answer when run R2 is in.");
answer("z04", 2, "Research question 2: the portable interface",
  "What does a portable transport interface cost against the raw RDMA interface on the path small messages take?",
  "A controlled comparison is in place: two implementations behind one interface, measured by the same benchmark source.",
  "Medians and p99 on raw verbs and on libfabric, the bandwidth for 1 MB writes, and instructions per operation (E1, E2, E5, run R2).",
  "One version of the library and of its verbs provider, on these two pairs of servers.",
  "For the second question the controlled comparison is in place and its numbers are waiting.\n\n* Fill this answer when run R2 is in.");
answer("z05", 3, "Research question 3: the cost of the transfer",
  "How much of the time to first token is cache transfer, and do per-transfer routing, compression and spilling reduce it against a transport that treats every transfer alike?",
  "By arithmetic the transfer takes at least 134 ms for 2,048 tokens on the laboratory link. The quantizer halves the bytes at a measured cost in attention agreement.",
  "The measured transfer, and its share of the time to first token (E7 and E8, runs R6 and R7).",
  "One model and random prompts. On the serving path the class follows from the size, and the second half of the question is answered per component.",
  "For the third question the arithmetic bound and the quantizer results are established, and the share of the transfer in the time to first token is waiting.\n\n* Fill this answer when runs R6 and R7 are in.");

def("z06", () => {
  const s = newSlide("z06", "Two columns", "Limitations: the serving path and the testbed",
    "The limitations fall into four groups. On the serving path, the components that decide are not called by the connector, and its sender still serializes both classes. The testbed is one pair of machines and one cable.");
  B(s, [head("Serving path"), "The components that decide are not called by the connector", "The connector's sender serializes both classes in one queue"]);
  B2(s, [head("Testbed"), "One pair and one cable, without a switch, packet loss or many senders", "Results on Soft-RoCE are specific to Soft-RoCE", "The card of server 4 sits in an eight-lane slot"]);
  vline(s, 6.66, Y0 + 0.05, 3.7);
});

def("z07", () => {
  const s = newSlide("z07", "Two columns", "Limitations: the workload and the measurements",
    "The workload is one model and generated traffic. And the measurements are single runs, with half a round trip standing in for a one-way latency. Each of these limits what the answers can say.");
  B(s, [head("Workload"), "One model of two billion parameters", "Generated traffic for the classifier and the controller"]);
  B2(s, [head("Measurements"), "Half a round trip stands in for a one-way latency", "Single runs, without spread", "The NIXL libfabric baseline runs over TCP here"]);
  vline(s, 6.66, Y0 + 0.05, 3.7);
});

def("z08", () => {
  const s = newSlide("z08", "Two columns", "Future work: the nearest steps",
    "There are four directions, from the nearest to the furthest. First, complete the serving path, so that the decisions of the rule tree reach the sender and the storage tier. Second, repair and tune the components that decide.");
  B(s, [head("1   Complete the serving path"), "Pass the decision of the rule tree to the sender and the storage tier", "A send queue per class in the connector"]);
  B2(s, [head("2   Repair the deciding components"), "Replace the switching rule, then measure", "Retrain the classifier on logs labeled by measured latency", "Use the sketch at the receiver, or remove it"]);
  vline(s, 6.66, Y0 + 0.05, 3.7);
});

def("z09", () => {
  const s = newSlide("z09", "Two columns", "Future work: further out",
    "Third, the hardware: open the GPU-direct path on server 4 and test with a switch, several senders and packet loss. Fourth, the next transport, where the question is whether separate endpoints still help when packets are spread across paths.");
  B(s, [head("3   The hardware"), "Open the GPU-direct path on server 4, and measure staging by removing it", "A switch, several senders, packet loss"]);
  B2(s, [head("4   The next transport"), "libfabric 2, with memory registration per endpoint", "Ultra Ethernet: do separate endpoints still help when packets take many paths?"]);
  vline(s, 6.66, Y0 + 0.05, 3.7);
});

def("z10", () => {
  const s = newSlide("z10", "Title and text", "Conclusion: built in software",
    "The limit on computing has moved from arithmetic, to memory, to the path between machines. Large systems address that limit with dedicated hardware, and this work asked what can be done without that hardware.\n\n" +
    "What we built is in software: a transport with separate traffic classes, a flow-controlled channel, a connector into a serving engine, and a method for taking results.");
  B(s, [{ t: "The limit on computing has moved from arithmetic, to memory, to the path between machines. This work asked what can be done without the hardware that removes it.", plain: true, color: NAVY },
    "A transport with separate traffic classes, on two libraries behind one interface",
    "A flow-controlled channel with four proved properties",
    "A connector into a production serving engine",
    "A method that stores each result with the commands that produced it"], { gap: 16 });
});

def("z11", () => {
  const s = newSlide("z11", "Text above, tall", "Conclusion: issues found in two components",
    "The analysis also found issues in two components, and we count both findings as results.");
  B(s, [{ t: "The analysis also found issues in two components.", plain: true, color: NAVY, size: 24 },
    "The size-threshold classifier does not recognize decode traffic",
    "The switching rule of the controller does not match its derivation"], { size: 24, gap: 18 });
  note(s, "A proof covers the first, and a unit test pins the second as implemented. The reported results do not depend on either component.", { y: 5.2, h: 0.6, size: 18 });
});

def("z12", () => {
  const s = newSlide("z12", "Statement", "The main idea",
    "To close, the main idea is that a message of eight bytes should not have to wait behind a block of four megabytes.");
  B(s, [{ t: "A message of eight bytes should not wait behind a block of four megabytes.", plain: true, size: 34 }]);
  s.addImage({ path: A + "/clips/t0_title." + (STATIC ? "first.png" : "gif"), x: MX, y: 4.95, w: CW, h: CW / 8, objectName: "animation strip",
    altText: "Animated strip with two lanes. In the upper lane small orange squares, the short urgent messages, move quickly. In the lower lane large blue blocks, the bulk data, move slowly. The small squares pass without waiting behind the blocks." });
});

const BACKUPS = [["b01", "Proof: Proposition 2.1"], ["b02", "One chunk on the wire"], ["b03", "Proofs: slots and notification"], ["b04", "Proof: the throughput bound"],
  ["b05", "Proof: Proposition 6.1"], ["b06", "The learned classifier"], ["b07", "The controller in detail"], ["b08", "Rotation and sketch lemmas"],
  ["b09", "Packed sizes"], ["b10", "Storage tier properties"], ["b11", "The replacement ACPI table"], ["b12", "Capabilities of the servers"],
  ["b13", "Other model families"], ["b14", "Lower bounds in full"], ["b15", "libfabric providers"], ["b16", "Opening the pool"],
  ["b17", "Ultra Ethernet: four changes"], ["b18", "One request, eight steps"], ["b19", "Benchmark and definitions"]];

def("z13", () => {
  const s = newSlide("z13", "Title only", "Questions",
    "Thank you. I am glad to take questions.\n\nThe lines on this slide open the backup slides, and Back on a backup slide returns to where we were.");
  T(s, "Thank you.", MX, 1.55, 6, 0.6, { fontSize: 30, bold: true, color: NAVY, valign: "middle", objectName: "thanks" });
  T(s, [{ text: "Source, results files and the thesis:  " }, { text: "github.com/ndg8743/ScuffedRDMA", options: { bold: true, color: NAVY, hyperlink: { url: "https://github.com/ndg8743/ScuffedRDMA", tooltip: "Open the repository" } } }], MX, 2.2, CW, 0.45, { fontSize: 19, valign: "middle", objectName: "repository" });
  hline(s, MX, 2.88, CW);
  T(s, "Backup slides", MX, 3.0, 5, 0.42, { fontSize: 19, bold: true, color: NAVY, valign: "middle", objectName: "heading backup" });
  const per = 7, cw = CW / 3;
  BACKUPS.forEach(([id, label], k) => {
    const x = MX + Math.floor(k / per) * cw, y = 3.5 + (k % per) * 0.42;
    s.addText(label, { x, y, w: cw - 0.2, h: 0.38, fontSize: 17, color: NAVY, valign: "middle", align: "left", margin: 0,
      hyperlink: { slide: num(id), tooltip: "Backup slide: " + label }, objectName: "link " + label, isTextBox: true });
  });
});
module.exports = { BACKUPS };
