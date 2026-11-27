// Part IV: RDMA at a low level.
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, tbl, CH } = require("./lib");

const two = (a, b, size) => [{ text: a, options: { bold: true, breakLine: true } }, { text: b, options: { fontSize: size || 15 } }];
const bold = (t) => ({ text: t, options: { bold: true } });
const mono = (t) => ({ text: t, options: { fontFace: "Courier New", fontSize: 16 } });

opener("n", "The history ended with a programming model that stayed the same across fabrics. The design decisions in the middleware depend on what that model allows, so we look at it from the bottom up.");

def("n01", () => {
  const s = newSlide("n01", "Text and figure", "The cost of a socket",
    "A program that sends through a socket hands a buffer to the kernel, which copies the bytes and adds headers. On the other machine the kernel checks, reorders and copies again, and wakes the program.\n\nFor a block of 4 mebibytes these costs are small next to the wire time. For a credit of 8 bytes they are nearly all of the cost.");
  B(s, ["Each message costs two transitions into the kernel",
    "At least two copies of the data",
    "A wake-up through the scheduler on the receiving side",
    "For a 4 MiB block these costs are small next to the wire time. For an 8-byte credit they are nearly all of the cost"]);
  const w = 2.5, xs = FX + 0.1, xr = FX + FW - w - 0.1;
  T(s, "sender", xs, 1.6, w, 0.32, { fontSize: 16, color: GRAY, align: "center", objectName: "label sender" });
  T(s, "receiver", xr, 1.6, w, 0.32, { fontSize: 16, color: GRAY, align: "center", objectName: "label receiver" });
  node(s, xs, 1.98, w, 0.6, "application", { size: 18, bold: true });
  node(s, xr, 1.98, w, 0.6, "application", { size: 18, bold: true });
  node(s, xs, 3.0, w, 1.2, two("kernel", "copies, cuts into segments, adds headers"), { size: 18, kind: "panel", name: "sender kernel" });
  node(s, xr, 3.0, w, 1.2, two("kernel", "checks, reorders, copies, wakes the program"), { size: 18, kind: "panel", name: "receiver kernel" });
  node(s, xs, 4.62, w, 0.6, "network card", { size: 18 });
  node(s, xr, 4.62, w, 0.6, "network card", { size: 18 });
  arrow(s, xs + w / 2, 2.6, xs + w / 2, 2.98); arrow(s, xs + w / 2, 4.22, xs + w / 2, 4.6);
  arrow(s, xr + w / 2, 4.6, xr + w / 2, 4.22); arrow(s, xr + w / 2, 2.98, xr + w / 2, 2.6);
  arrow(s, xs + w + 0.03, 4.92, xr - 0.03, 4.92, { width: 2, name: "wire" });
  T(s, "system call", xs + w / 2 + 0.1, 2.62, 1.3, 0.34, { fontSize: 14, color: GRAY, objectName: "label system call" });
  T(s, "interrupt", xr + w / 2 + 0.1, 4.24, 1.2, 0.34, { fontSize: 14, color: GRAY, objectName: "label interrupt" });
});

def("n02", () => {
  const s = newSlide("n02", "Text and figure", "Remote direct memory access",
    "RDMA avoids those costs by moving the work to the network cards. The application registers a region of its memory with the network card and receives a key. A peer that holds the key and the address asks its own card to write into that region.\n\nThe two cards carry out the transfer, without a system call, without an extra copy, and without running the receiving application.");
  B(s, ["The application registers a region of its memory with the network card and receives a key",
    "A peer that holds the key and the address asks its own card to write into that region, or to read from it",
    "The two cards carry out the transfer",
    "This is kernel bypass and zero copy, and the receiving application does not have to run"]);
  const w = 2.5, xs = FX + 0.1, xr = FX + FW - w - 0.1;
  T(s, "sender", xs, 1.6, w, 0.32, { fontSize: 16, color: GRAY, align: "center", objectName: "label sender" });
  T(s, "receiver", xr, 1.6, w, 0.32, { fontSize: 16, color: GRAY, align: "center", objectName: "label receiver" });
  node(s, xs, 1.98, w, 0.9, two("application", "asks its card to write"), { size: 18 });
  node(s, xr, 1.98, w, 0.9, two("application", "does not run"), { size: 18 });
  node(s, xs + 0.75, 3.2, w - 0.75, 0.9, "kernel: not on the data path", { size: 15, color: GRAY, dash: "dash", name: "sender kernel" });
  node(s, xr, 3.2, w - 0.75, 0.9, "kernel: not on the data path", { size: 15, color: GRAY, dash: "dash", name: "receiver kernel" });
  node(s, xs, 4.62, w, 0.6, "network card", { size: 18, kind: "panel", bold: true });
  node(s, xr, 4.62, w, 0.6, "network card", { size: 18, kind: "panel", bold: true });
  arrow(s, xs + 0.36, 2.9, xs + 0.36, 4.6, { color: NAVY, width: 2 });
  arrow(s, xr + w - 0.36, 4.6, xr + w - 0.36, 2.9, { color: NAVY, width: 2 });
  arrow(s, xs + w + 0.03, 4.92, xr - 0.03, 4.92, { color: NAVY, width: 2, name: "wire" });
  note(s, "The receiving card checks the key and places the bytes in the registered memory.", { x: FX, y: 5.4, w: FW, h: 0.7, align: "center" });
});

def("n03", () => {
  const s = newSlide("n03", "Text below", "RDMA over Ethernet",
    "RoCE carries the InfiniBand transport over Ethernet, and its second version wraps each packet in UDP.\n\nSoft-RoCE implements that transport in the kernel, on any Ethernet card. It keeps the interface and the semantics, without the hardware offload.");
  tbl(s, ["Name", "What it is"], [
    [bold("InfiniBand"), "remote direct memory access as a service of the network adapter"],
    [bold("RoCE"), "the InfiniBand transport carried over Ethernet"],
    [bold("RoCEv2"), "each packet wrapped in UDP, so that it can be routed like any other traffic"],
    [bold("Soft-RoCE"), "RoCEv2 implemented in the kernel, on top of any Ethernet card"],
  ], MX, 1.68, CW, [2.4, 9.533], { size: 20, rowH: 0.58, name: "RDMA over Ethernet" });
  B(s, ["Soft-RoCE keeps the interface and the semantics without the hardware offload, so the kernel builds and parses the packets",
    "Laboratory pair: Soft-RoCE. Home pair: RoCEv2 in hardware"], { gap: 10 });
});

def("n04", () => {
  const s = newSlide("n04", "Title only", "Five objects of the verbs interface",
    "The programming interface to RDMA on Linux is the verbs interface. A program creates five kinds of object before it can send data.\n\n" +
    "The two that matter most later are the queue pair, which is the endpoint of a connection, and the completion queue, where the card reports the outcome of each operation.");
  const bottom = tbl(s, ["Object", "What it is"], [
    [bold("Device context"), "an open handle on one RDMA device"],
    [bold("Protection domain"), "ties memory regions and queue pairs together: a key from one domain does not work in another"],
    [bold("Memory region"), "a registered range of memory: registering pins the pages and returns a local key and a remote key"],
    [bold("Queue pair"), "the endpoint of a connection: a send queue and a receive queue"],
    [bold("Completion queue"), "where the card reports that a work request finished, with a status"],
  ], MX, 1.68, CW, [3.0, 8.933], { size: 19, rowH: 0.7, name: "verbs objects" });
  note(s, "We use reliable connected queue pairs, which retransmit lost packets and deliver in order.", { y: bottom + 0.12, h: 0.45, size: 17 });
});

def("n05", () => {
  const s = newSlide("n05", "Text below", "Bringing up a queue pair",
    "A queue pair has to be walked through three transitions before it can send, and the two sides need each other's numbers to make them.\n\nRDMA cannot exchange those before the connection exists, so they travel over an ordinary TCP connection first: here a fixed record of 64 bytes.");
  const names = ["Reset", "Initialized", "Ready to receive", "Ready to send"], labs = ["port, access rights", "the peer's numbers", "timeouts, retries"];
  const w = 2.3, gap = (CW - 4 * w) / 3, y = 2.35;
  names.forEach((n, k) => {
    const x = MX + k * (w + gap);
    node(s, x, y, w, 0.75, n, { size: 19, bold: true, kind: k === 3 ? "panel" : "plain", name: "state " + n });
    if (k < 3) {
      arrow(s, x + w + 0.04, y + 0.375, x + w + gap - 0.04, y + 0.375, { color: NAVY, width: 2 });
      T(s, labs[k], x + w - 0.6, y - 0.55, gap + 1.2, 0.4, { fontSize: 16, color: GRAY, align: "center", valign: "bottom", objectName: "label " + labs[k] });
    }
  });
  const xe = MX + 3 * (w + gap);
  node(s, xe, 3.75, w, 0.6, "Error", { size: 18, name: "state Error" });
  arrow(s, xe + w / 2, y + 0.77, xe + w / 2, 3.73, { dash: "dash" });
  T(s, "failed operation", xe - 2.1, 3.2, 2.0 + w / 2 - 0.02, 0.4, { fontSize: 16, color: GRAY, align: "right", valign: "middle", objectName: "label failure" });
  s.addShape(pres.ShapeType.line, { x: MX + w / 2, y: 4.05, w: xe - MX - w / 2, h: 0, line: { color: GRAY, width: 1.5, dashType: "dash" }, objectName: "recovery" });
  arrow(s, MX + w / 2, 4.05, MX + w / 2, y + 0.77, { dash: "dash", name: "recovery" });
  T(s, "recovery", MX + w / 2 + 0.12, 3.62, 2, 0.4, { fontSize: 16, color: GRAY, valign: "middle", objectName: "label recovery" });
  B(s, ["The two sides need each other's queue pair number, address and starting sequence number",
    "RDMA cannot exchange them before the connection exists, so they travel over an ordinary TCP connection first: here a fixed record of 64 bytes"], { gap: 10 });
});

def("n06", () => {
  const s = newSlide("n06", "Title only", "Four operations",
    "Four operations matter here. An RDMA write is one-sided: the data lands at the address the sender names, and the receiving program is not informed.\n\nA write with immediate data also carries 32 bits, and the target receives a completion with those bits. The blob channel is built on this operation.");
  const bottom = tbl(s, ["Operation", "Kind", "What the target learns"], [
    ["Send and receive", "two-sided", "a completion; a receive was posted in advance"],
    ["RDMA write", "one-sided", "nothing: the program is not informed"],
    [bold("RDMA write with immediate data"), bold("one-sided, plus 32 bits"), bold("a completion that carries the 32 bits")],
    ["RDMA read", "one-sided, a pull", "nothing"],
  ], MX, 1.68, CW, [4.1, 2.9, 4.933], { size: 19, rowH: 0.62, name: "operations" });
  claim(s, "", "The blob channel is built on the write with immediate data: the data goes directly to its slot, and the 32 bits identify the slot.", MX, bottom + 0.3, CW, 0.95, { size: 21 });
  note(s, "Write and read need connected, reliable queue pairs, which is why both traffic classes use reliable connections.", { y: bottom + 1.38, h: 0.45, size: 17 });
});

def("n07", () => {
  const s = newSlide("n07", "Title only", "One write with immediate data",
    "This is one write with immediate data, step by step. The sending application posts the write, the two devices move the data, and the target device checks the key and places the bytes.\n\nThe sender gets a completion with a status, and the target gets a completion with the immediate value. The target application is not involved until that last step.");
  const xs = [1.95, 5.0, 8.33, 11.38], names = ["Sender application", "Sender device", "Target device", "Target application"];
  names.forEach((n, k) => {
    node(s, xs[k] - 1.25, 1.6, 2.5, 0.55, n, { size: 17, bold: true, kind: k === 1 || k === 2 ? "panel" : "plain", name: n });
    s.addShape(pres.ShapeType.line, { x: xs[k], y: 2.15, w: 0, h: 3.9, line: { color: RULE, width: 1, dashType: "dash" }, objectName: "lifeline " + n });
  });
  const msg = (n, text, a, b, y, o = {}) => {
    arrow(s, xs[a] + (b > a ? 0.03 : -0.03), y, xs[b] + (b > a ? -0.03 : 0.03), y, { color: o.color || NAVY, width: o.width || 2, name: "step " + n });
    const x0 = Math.min(xs[a], xs[b]), x1 = Math.max(xs[a], xs[b]);
    T(s, [{ text: n + "  ", options: { bold: true, color: NAVY } }, { text }], x0 + 0.1, y - 0.42, x1 - x0 - 0.2, 0.38, { fontSize: 17, align: "center", valign: "bottom", objectName: "label step " + n });
  };
  msg("1", "post write + immediate", 0, 1, 2.85);
  msg("2", "data packets", 1, 2, 3.45, { color: BLUE, width: 3.5 });
  T(s, [{ text: "3  ", options: { bold: true, color: NAVY } }, { text: "check key, place bytes, consume one receive" }], xs[2] + 0.15, 3.58, 2.85, 0.66, { fontSize: 16, valign: "middle", objectName: "label step 3" });
  msg("4", "acknowledgment", 2, 1, 4.75);
  msg("5", "completion, status", 1, 0, 5.3);
  msg("6", "completion, immediate", 2, 3, 5.85);
  take(s, "The target application is not involved until step 6.", { y: 6.2 });
});

def("n08", () => {
  const s = newSlide("n08", "Text above, tall", "Three facts about ordering",
    "Three facts about ordering follow from the specification, and the rest of the talk refers to them by number.\n\nFact 2 is easy to overlook. The specification does not promise that the bytes of a large write are placed front to back, so the receiver needs a signal that comes after the data.");
  B(s, [{ t: "**Operations execute in order.** Work requests posted to one send queue are carried out at the target in the order they were posted", num: true },
    { t: "**Placement within one message is not ordered.** A reader can see the end of a message before the middle", num: true },
    { t: "**A completion follows placement.** When the completion of a write with immediate data arrives, all bytes of that write are in place", num: true }], { gap: 14 });
  claim(s, "", "Fact 2 is easy to overlook. Looking at a block is not a safe way for the receiver to decide that the block has arrived.", MX, 5.15, CW, 1.05, { size: 21 });
});

def("n09", () => {
  const s = newSlide("n09", "Two columns", "What goes wrong in production",
    "RDMA leaves some of the difficult parts of networking to the application. IBM Storage Scale uses RDMA on its data path, and its published issues include a race that returned incorrect data to a client.\n\nWe take three rules from this, and the middleware applies them.");
  B(s, [{ t: "A production reference", plain: true, bold: true, color: NAVY, size: 24 },
    "IBM Storage Scale, the file system that began as GPFS, uses RDMA on its data path",
    "A race between the RDMA layer and the file system returned incorrect data to a client",
    "A fault in reconnecting after a failure"]);
  B2(s, [{ t: "Three rules the middleware applies", plain: true, bold: true, color: NAVY, size: 24 },
    "The status of each completion is checked",
    "A connection that enters the error state is treated as lost and reported",
    "The arrival of data is taken from a signal that the transport orders after the data"]);
  vline(s, 6.66, Y0 + 0.05, 4.3);
});

def("n10", () => {
  const s = newSlide("n10", "Narrow text and figure", "libfabric: a portable interface",
    "The verbs interface is specific to RDMA devices, so the middleware is written against libfabric, where applications state what they need and providers state what they can do.\n\nWe keep a second implementation on raw verbs, so that the cost of the portable layer can be measured.");
  B(s, ["Verbs is specific to RDMA devices",
    "libfabric: applications state what they need, providers state what they can do",
    "Three reasons to build on it",
    ["development without RDMA hardware", "a like-for-like baseline with NIXL", "published comparisons to stand on"]]);
  const NXX = 5.75, NWW = W - MX - NXX;
  const bottom = tbl(s, ["Purpose", "Verbs", "libfabric"], [
    ["Group resources", "protection domain", "domain"],
    ["Connection endpoint", "queue pair", "endpoint"],
    ["Report completions", "completion queue", "completion queue"],
    ["Count completions", "none", "counter"],
    ["One-sided write", "post send, write opcode", mono("fi_write, fi_writedata")],
  ], NXX, 1.68, NWW, [2.2, 2.3, 2.383], { size: 17, rowH: 0.6, name: "verbs and libfabric" });
  note(s, "The pool is also implemented on raw verbs, so that the cost of the portable layer can be measured.", { x: NXX, y: bottom + 0.15, w: NWW, h: 0.7, size: 17 });
  more(s, [["Detail", "b15"]]);
});

def("n11", () => {
  const s = newSlide("n11", "Text and figure", "The same interface reaches the next transport",
    "Ultra Ethernet is the transport designed to follow RoCE. It is connectionless, it uses many paths at once, and it adopts libfabric as its interface.\n\nOur software has not run on it yet. What would have to change is on a backup slide.");
  B(s, ["Ultra Ethernet Specification 1.0, June 2025: a transport designed to follow RoCE",
    "Connectionless, many paths at once, four kinds of delivery",
    "It adopts libfabric as its interface",
    "This software has not run on Ultra Ethernet yet. A port needs four changes"]);
  const cx = FX + FW / 2;
  node(s, cx - 1.6, 1.75, 3.2, 0.6, "the middleware", { size: 18, bold: true });
  arrow(s, cx, 2.37, cx, 2.75);
  node(s, cx - 1.6, 2.77, 3.2, 0.6, "libfabric", { size: 18, bold: true, kind: "panel" });
  const pw = 1.78, px = [FX, FX + 1.95, FX + 3.9];
  const prov = [["verbs provider", "RoCE: both pairs of servers"], ["tcp and shm providers", "development and tests"], ["an Ultra Ethernet provider", "not available yet"]];
  prov.forEach(([a, b], k) => {
    arrow(s, cx + (k - 1) * 0.9, 3.39, px[k] + pw / 2, 3.98, { dash: k === 2 ? "dash" : "solid" });
    node(s, px[k], 4.0, pw, 1.25, two(a, b, 15), { size: 16, dash: k === 2 ? "dash" : "solid", color: k === 2 ? GRAY : INK, name: a });
  });
  more(s, [["Detail", "b17"]]);
});
