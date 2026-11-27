// Part VIII: testbed and method.
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, pic, caption, code, tbl, CH } = require("./lib");

const two = (a, b, size) => [{ text: a, options: { bold: true, breakLine: true } }, { text: b, options: { fontSize: size || 15 } }];
const three = (a, b, c) => [{ text: a, options: { bold: true, breakLine: true } }, { text: b, options: { fontSize: 15, breakLine: true } }, { text: c, options: { fontSize: 15 } }];
const bold = (t) => ({ text: t, options: { bold: true } });
const mono = (t) => ({ text: t, options: { fontFace: "Courier New", bold: true } });

opener("e", "The numbers come from a small laboratory, so before any result we describe the machines and how a result is taken.");

def("e01", () => {
  const s = newSlide("e01", "Title only", "Four servers, two sites",
    "There are four servers on two sites. Servers 1 and 2 are in the university laboratory, with the GPUs that run the model and commodity Ethernet. The research question is asked on this pair.\n\nServers 3 and 4 have RoCE in hardware, which lets us separate the cost of our software from the cost of the software network card.\n\n* The hardware record of server 1 is still to be taken (run R0).");
  const pair = (x, title, a, b, link, lines) => {
    const w = 5.6, bw = 2.35;
    T(s, title, x, 1.55, w, 0.42, { fontSize: 20, bold: true, color: NAVY, valign: "middle", objectName: "heading " + title });
    node(s, x, 2.1, bw, 1.3, three(...a), { size: 18, name: a[0] });
    node(s, x + w - bw, 2.1, bw, 1.3, three(...b), { size: 18, name: b[0] });
    arrow(s, x + bw + 0.04, 2.75, x + w - bw - 0.04, 2.75, { color: NAVY, width: 2.5, both: true, name: "link" });
    T(s, link, x, 3.5, w, 0.38, { fontSize: 16, color: GRAY, align: "center", valign: "middle", objectName: "link label" });
    L(s, lines, x, 4.1, w, 1.5, { size: 19, gap: 8 });
  };
  pair(MX, "Laboratory pair: servers 1 and 2", ["Server 1", "2 × RTX 5090", "Intel X710, 10 GbE"], ["Server 2", "3 × RTX 3090", "Aquantia AQC107, 10 GbE"], "direct cable, commodity Ethernet at 10 Gb/s",
    ["RDMA in software (Soft-RoCE)", "The research question is asked on this pair"]);
  pair(W - MX - 5.6, "Home pair: servers 3 and 4", ["Server 3", "RTX 5070 Ti", "ConnectX-4, 100 GbE"], ["Server 4", "2 × Tesla V100", "ConnectX-4, 100 GbE"], "direct-attach copper cable, 100 Gb/s",
    ["RoCEv2 in hardware", "Lets us separate the cost of our software from the cost of the software network card"]);
  vline(s, W / 2, 1.6, 4.0);
  note(s, "Server 1 is the prefill side and benchmark client, server 2 the decode side and benchmark target.", { y: 5.82, h: 0.4 });
  star(s, "Waiting for the hardware record of server 1 (run R0).", MX, 6.24, CW, 0.4, { fontSize: 16 });
  more(s, [["Limits", "b12"]]);
});

def("e02", () => {
  const s = newSlide("e02", "Title only", "The hardware",
    "This table lists the four machines. The laboratory pair has the newer GPUs and ordinary network cards. The home pair has older or smaller GPUs and network cards with RDMA in hardware.");
  const bottom = tbl(s, ["Server", "Site", "Processor and board", "Memory", "GPUs", "Network card"], [
    [bold("1"), "Laboratory", { text: "* waiting for run R0", options: { italic: true, color: ORANGE } }, "128 GB", "2 × RTX 5090, 64 GB in total", "Intel X710-DA2, 10 GbE"],
    [bold("2"), "Laboratory", "Threadripper 3960X, ASRock TRX40 Creator", "64 GB", "3 × RTX 3090, 72 GB in total", "Aquantia AQC107, 10 GbE"],
    [bold("3"), "Home", "Ryzen 9 7950X", "192 GB", "RTX 5070 Ti, 16 GB", "Mellanox ConnectX-4, 100 GbE"],
    [bold("4"), "Home", "Xeon E5-2697A v4, Gigabyte GA-X99-UD4P", "128 GB", "2 × Tesla V100, 32 GB each", "Mellanox ConnectX-4, 100 GbE"],
  ], MX, 1.7, CW, [0.95, 1.5, 3.2, 1.25, 2.6, 2.433], { size: 17, rowH: 0.82, name: "hardware" });
  star(s, "Waiting for the hardware record of server 1 (run R0).", MX, bottom + 0.2, CW, 0.45);
});

// ------------------------------------------------------------------ the home pair and the firmware work on server 4
// (pictures from the first update report, January 2026)
def("e21", () => {
  const s = newSlide("e21", "Text below", "The home pair: servers 3 and 4",
    "This is the home pair in January 2026, with server 3 on the left, server 4 on the right, and the two Tesla V100 cards inside server 4.\n\nOne direct cable joins the two ConnectX-4 cards. These two machines are the part of the testbed that has RDMA in hardware.");
  const w = 5.85;
  const a = pic(s, "towers", "Photograph of two tower computers with their side panels removed, standing side by side on a wooden floor. The left one, server 3, holds one large graphics card. The right one, server 4, is a larger case with several expansion cards.", { x: MX, y: 1.55, w });
  caption(s, "Server 3 (left) and server 4 (right), January 2026.", a);
  const b = pic(s, "v100_installed", "Photograph of the inside of server 4 from above: two long black Tesla V100 cards sit in neighboring slots below the processor cooler, with their power cables on the right.", { x: W - MX - w, y: 1.55, w });
  caption(s, "The two Tesla V100 cards installed in server 4.", b);
  B(s, ["Two tower computers, joined by one direct 100 gigabit cable between two ConnectX-4 cards",
    "These two machines are the part of the testbed with RDMA in hardware"]);
});

def("e20", () => {
  const s = newSlide("e20", "Text and figure", "Six layers were changed on server 4",
    "Each of the four servers needed some work before it could run an experiment. Server 4 needed the most, on six layers from the firmware of the board, which is the BIOS, up to the RDMA device.\n\nWe go through them from the bottom, because this work explains several limits of the testbed.");
  B(s, ["Each of the four servers needed some work before it could run an experiment",
    "Server 4 needed the most, on six layers from the firmware of the board (the BIOS) up to the RDMA device",
    "Servers 1 and 2 did not need firmware work, since their network cards have no RDMA function to configure"]);
  const layers = [["6", "RDMA device", "RoCEv2 ports active"],
    ["5", "Drivers and kernel", "legacy GPU driver, CUDA, a rebuilt kernel"],
    ["4", "Network card firmware", "from InfiniBand to Ethernet (mstconfig)"],
    ["3", "Kernel command line", "PCI reallocation options"],
    ["2", "ACPI table", "a 64-bit window on the PCI root, loaded at boot"],
    ["1", "Board firmware (BIOS)", "an image with a Resizable BAR driver added"]];
  const x = FX + 0.62, w = FW - 0.62, h = 0.66, pitch = 0.75, y0 = 1.68;
  layers.forEach(([n, name, what], k) => {
    node(s, x, y0 + k * pitch, w, h, [{ text: n + "   ", options: { bold: true, color: NAVY } }, { text: name, options: { bold: true, breakLine: true } }, { text: "      " + what, options: { fontSize: 14 } }],
      { size: 17, align: "left", margin: 8, kind: k >= 4 ? "panel" : "plain", name: "layer " + n });
  });
  arrow(s, FX + 0.3, y0 + 5 * pitch + h, FX + 0.3, y0, { color: NAVY, width: 2, name: "order of work" });
  T(s, "order of work", FX - 0.02, y0 + 1.2, 0.3, 2.2, { fontSize: 15, color: GRAY, align: "center", valign: "middle", vert: "vert270", objectName: "label order of work" });
});

def("e22", () => {
  const s = newSlide("e22", "Text and figure", "Server 4 did not start with its GPUs",
    "With either V100 installed, the board did not complete its power-on self test, although the same cards worked in server 3.\n\nThe cause is address space. A V100 asks the firmware for one very large 64-bit memory region above the 4 gigabyte line, and the firmware options of this board for such regions did not work.");
  B(s, ["With either V100 installed, the board did not complete its power-on self test",
    "It started normally with a small display card, and the same V100 cards worked in server 3",
    "The cause is address space: a V100 asks for one very large 64-bit memory region, which has to be placed above the 4 GB line",
    "The firmware options of the board for such regions did not work"]);
  const r = pic(s, "staging", "Photograph of two Tesla V100 cards and a green network card lying on foam beside the open case of server 4, before installation.", { cx: FX + FW / 2, y: 1.62, h: 4.2 });
  caption(s, "The V100 cards and the network card before installation.", r);
});

def("e23", () => {
  const s = newSlide("e23", "Title only", "The vendor's firmware ends in 2018",
    "This is the vendor's support page for the board. It lists five firmware versions, from the first in February 2015 to the last one, F23c, in June 2018.\n\nSo the change had to be made on our side.");
  const r = pic(s, "vendor_firmware_list", "Screenshot of the vendor's support page for the GA-X99-UD4P board. A table lists five firmware versions: F23c, Update CPU Microcode, June 14, 2018; F22, June 21, 2017; F20, January 11, 2016; the beta version F2b, August 6, 2015; and F1, first release, February 3, 2015.", { x: MX, y: 1.5, w: 8.2, frame: true });
  caption(s, "Vendor support page for the Gigabyte GA-X99-UD4P (screenshot, January 2026).", r);
  // marks on the last and the first version, with the same facts as text beside the picture
  const cx = r.x + r.w + 0.35, cw = W - MX - cx;
  const mark = (top, hh, label, value, strong) => {
    const y = r.y + r.h * top, h = r.h * hh, mid = y + h / 2;
    s.addShape(pres.ShapeType.rect, { x: r.x + 0.03, y, w: r.w - 0.06, h, fill: { color: WHITE, transparency: 100 }, line: { color: strong ? NAVY : RULE, width: strong ? 2 : 1.25 }, objectName: "mark: " + label });
    hline(s, r.x + r.w, mid, 0.3, { color: strong ? NAVY : RULE, width: 1.25 });
    T(s, label, cx, mid - 0.52, cw, 0.34, { fontSize: 16, color: GRAY, valign: "bottom", objectName: "label " + label });
    T(s, value, cx, mid - 0.16, cw, 0.8, { fontSize: 22, bold: strong, color: strong ? NAVY : INK, objectName: "value " + label });
  };
  mark(0.165, 0.142, "Last version", "F23c, June 14, 2018", true);
  mark(0.842, 0.138, "First version", "F1, February 3, 2015", false);
});

def("e24", () => {
  const s = newSlide("e24", "Text and figure", "Change 1: a replacement ACPI table",
    "The first change leaves the firmware as it is. The operating system learns from an ACPI table which address ranges the PCI root may hand out, and we replace that table at boot with one that opens a 64-bit window above the installed memory.\n\nIt was used together with a kernel parameter that tells Linux to ignore those ranges, so we do not claim which of the two lets the regions fit.");
  B(s, ["The operating system learns from an ACPI table which address ranges the PCI root may hand out",
    "A replacement table, loaded by the boot loader, opens a 64-bit window for the large regions",
    "The firmware stays as it is",
    "It was used together with a kernel parameter that tells Linux to ignore the ranges ACPI reports, so we do not claim which of the two lets the regions fit"], { gap: 12 });
  T(s, "Excerpt of the replacement table", FX, 1.66, FW, 0.36, { fontSize: 17, color: GRAY, objectName: "label" });
  const r = code(s, ["Method (_CRS, 0, Serialized)", "{", "    ...", "    M2MN = 0x0000002100000000", "    M2MX = 0x00003FFFFFFFFFFF", "    M2LN = (M2MX - M2MN) + One", "    Return (P0RS)", "}"], FX, 2.08, FW, { size: 16, name: "excerpt of the replacement table" });
  tbl(s, null, [
    [{ text: "0x2100000000", options: { fontFace: "Courier New", fontSize: 16 } }, "the window starts at 132 GiB, above the 128 GB of memory"],
    [{ text: "0x3FFFFFFFFFFF", options: { fontFace: "Courier New", fontSize: 16 } }, "it ends at the 46-bit limit of the processor, 64 TiB"],
  ], FX, r.y + r.h + 0.2, FW, [2.25, 3.433], { size: 16, rowH: 0.5, name: "the two addresses" });
  more(s, [["Detail", "b11"]]);
});

def("e25", () => {
  const s = newSlide("e25", "Text below", "Change 2: a Resizable BAR driver in the firmware",
    "The second change is to the firmware itself. ReBarUEFI, an open-source driver that adds Resizable BAR support, is inserted into the firmware image with UEFITool.\n\n" +
    "The picture is the setup screen of server 4 afterwards. It reports version F24, dated January 13, 2026, where the vendor's list ended at F23c.\n\n" +
    "* Waiting for the hardware record of server 4 (run R0): which of the two changes is active, and that the board starts with both V100 cards.");
  const r = pic(s, "firmware_f24", "Detail of a photograph of the firmware setup screen of server 4, on its System page. System Information lists Model Name X99-UD4, BIOS Version F24 and BIOS Date 01/13/2026.", { y: 1.5, w: CW });
  caption(s, "Setup screen of server 4, System page, January 2026 (detail of the photograph).", r);
  B(s, ["ReBarUEFI, an open-source driver for Resizable BAR, is inserted into the firmware image with UEFITool",
    "The setup screen then reports version F24, dated January 13, 2026"], { gap: 8 });
  star(s, "Waiting for the hardware record of server 4 (run R0): which of the two changes is active, and that the board starts with both V100 cards.", MX, 6.1, CW, 0.62, { fontSize: 16 });
});

def("e26", () => {
  const s = newSlide("e26", "Text and figure", "Above the firmware: drivers and the network card",
    "The picture is a status report from January 2026: the operating system sees the card, and the driver is not yet installed. The V100 is of the Volta generation, so server 4 runs a legacy driver branch.\n\nThe ConnectX-4 cards arrived configured for InfiniBand. RoCE version 2 needs Ethernet mode, a firmware setting of the card.");
  B(s, ["January 2026: the operating system of server 4 reports a Tesla V100",
    "The V100 is of the Volta generation, which current driver branches no longer support: server 4 runs a legacy branch with a matching CUDA toolkit",
    "The ConnectX-4 cards arrived configured for InfiniBand. RoCEv2 needs Ethernet mode, a firmware setting changed with mstconfig",
    "After a restart, the cabled port is active at 100 gigabits with RoCEv2 addresses"], { gap: 10, size: 21 });
  const r = pic(s, "server4_status", "Detail of a photograph of a status report on the screen of server 4. GPU Status, V100: hardware detected, Tesla V100 SXM2 32GB at PCI address 03:00.0; NVIDIA driver not installed; nvidia-smi not found; kernel modules not loaded; device files missing.", { x: FX, y: 1.9, w: FW });
  caption(s, "Status report on server 4, January 2026: the card is detected, the driver is not yet installed.", r, { h: 0.6 });
});

def("e27", () => {
  const s = newSlide("e27", "Text above, tall", "GPUDirect RDMA on server 4",
    "One more layer is prepared and is not in use yet. GPUDirect RDMA would let the network card read and write GPU memory directly, but it needs a kernel option that the stock kernel of server 4 does not have.\n\nWe rebuilt the kernel with the option and have not installed it yet, so the transfers we measure stage data through host memory.");
  B(s, ["GPUDirect RDMA lets a network card read and write GPU memory without a copy through host memory",
    "It needs a kernel module, which needs a kernel option for registering peer memory",
    "The stock kernel of the hypervisor on server 4 is built without that option, so the module does not load",
    "We rebuilt the kernel with the option enabled, and it is not installed yet"], { gap: 12 });
  claim(s, "", "GPUDirect is preparation for later work. The transfers we measure stage data through host memory.", MX, 5.15, CW, 1.05, { size: 21 });
});

def("e03", () => {
  const s = newSlide("e03", "Title only", "Hardware limits and what we decided",
    "Each limit of the hardware led to one decision. The first row matters most. Soft-RoCE keeps the semantics of RDMA without its speed, because the kernel builds and parses the packets, so we report latencies per stack and per pair.\n\nThe last row belongs to server 4, where the slot is slower than the cable and so the slot bounds the numbers.");
  tbl(s, ["Limit of the hardware", "Decision"], [
    ["No RDMA hardware in the laboratory pair", "Soft-RoCE: the semantics of RDMA without its speed. Latencies are reported per stack and per pair"],
    ["No RDMA hardware on development machines", "Software providers (TCP, shared memory). Such runs are used as smoke tests"],
    ["The network cards cannot reach the GPUs directly", "The cache is staged through host memory"],
    ["Two GPU generations", "A neutral byte format on the wire"],
    ["Write and read need connected reliable queue pairs", "Both classes use reliable connections"],
    ["The network card of server 4 sits in a slot with eight PCI Express lanes", "About 63 Gb/s before overhead, so the slot bounds the numbers from the home pair"],
  ], MX, 1.66, CW, [5.2, 6.733], { size: 17, rowH: 0.66, name: "limits and decisions" });
});

def("e04", () => {
  const s = newSlide("e04", "Title and text", "What we count as a result",
    "We use four rules for what we call a result. A number has a results file written by the program that measured it. A transfer is counted when its completion was checked for success. A run on a development machine is treated as a smoke test. And numbers from models are labeled and kept in their own tables.");
  B(s, [{ t: "A number has a results file in the repository, written by the program that measured it, together with the commands that were run", num: true },
    { t: "A transfer is counted when its completion was checked for success", num: true },
    { t: "A run on a development machine without the real link is treated as a smoke test", num: true },
    { t: "Models and arithmetic are labeled as such and kept apart from the tables of measurements", num: true }], { gap: 18 });
});

def("e05", () => {
  const s = newSlide("e05", "Text above, tall", "Why the second rule exists",
    "The second rule comes from arithmetic. At 10 gigabits a transfer of 4 mebibytes needs at least 3.4 milliseconds on the wire. So a reported time of a few microseconds means that the completions had failed.");
  B(s, ["At 10 Gb/s a transfer of 4 MiB needs at least 3.4 ms on the wire",
    "So a reported time of a few microseconds points to error completions",
    "A benchmark that counts completions without reading their status records a failed operation as a very fast one"], { gap: 14 });
  claim(s, "", "A completion with an error status is counted as a failed transfer.", MX, 5.15, CW, 0.95, { size: 24 });
});

def("e07", () => {
  const s = newSlide("e07", "Narrow text and figure", "The benchmark",
    "The benchmark is one C program linked against the pool, with three modes. The hol mode is the head-of-line experiment: a cold stream runs while a hot ping-pong is timed, and a switch makes both classes share one endpoint as the baseline.");
  B(s, ["One C program, linked against the pool",
    "The same source runs against raw verbs",
    "1,000 warm-up iterations, then 20,000",
    "Median, 99th and 99.9th percentile, with pinned threads"]);
  const NXX = 5.75, NWW = W - MX - NXX;
  tbl(s, ["Mode", "What it does"], [
    [mono("sig"), "a hot ping-pong with each of the five signals: latency by message size"],
    [mono("bw"), "one class streams: megabytes per second by message size"],
    [mono("hol"), "cold streams while hot ping-pongs; a switch makes both classes share one endpoint, the baseline"],
  ], NXX, 1.7, NWW, [1.1, 5.783], { size: 18, rowH: 0.8, name: "benchmark modes" });
  more(s, [["Detail", "b19"]]);
});

def("e08", () => {
  const s = newSlide("e08", "Title only", "Eight experiments",
    "Eight experiments answer the three questions. E1, E2 and E5 compare the two implementations of the pool and the five signals. E3 and E4 are the head-of-line experiments. E6 to E8 move up the stack: the blob channel, the split engine on one GPU, and the split engine across two machines.");
  tbl(s, ["No.", "What it measures", "Where", "For"], [
    ["E1", "Hot-path latency of each stack: 8 B to 64 KB", "both pairs", "RQ2"],
    ["E2", "Cold bandwidth: 4 KB to 16 MB, 16 writes in flight", "both pairs", "RQ2"],
    [bold("E3"), bold("Does a second endpoint remove head-of-line blocking?"), bold("both pairs"), bold("RQ1")],
    ["E4", "Which libfabric configuration: the E3 load over six combinations", "both pairs", "RQ1"],
    ["E5", "Which completion signal: the five mechanisms", "both pairs", "RQ2"],
    ["E6", "The blob channel against TCP: blobs of 4 KB to 32 MB", "laboratory pair", "RQ3"],
    ["E7", "The split engine on one GPU: agreement token for token", "one GPU machine", "RQ3"],
    ["E8", "The split engine across machines: prompts of 128 to 4,096 tokens", "laboratory pair", "RQ3"],
  ], MX, 1.62, CW, [1.0, 7.4, 2.4, 1.133], { size: 18, rowH: 0.5, name: "experiments" });
});

def("e09", () => {
  const s = newSlide("e09", "Text above, tall", "The criterion for E3, set before the runs",
    "We wrote down the criterion for the central experiment before running it. If the hot latency with two endpoints stays near its unloaded value while the one-endpoint value grows, the claim holds on that stack. If both grow on the hardware pair as well, the design does not work and a different mechanism is needed.");
  B(s, ["The claim holds on a stack if the hot p99 with two endpoints stays near its unloaded value, while the one-endpoint value grows with the size of the cold writes",
    "If both grow, the contention is below the queue pair",
    "If both grow on the hardware pair as well, the design does not work and a different mechanism is needed"], { gap: 14 });
  eq(s, "penalty", MX, 5.15, { size: 20 });
  T(s, "Near one: the small messages did not notice the bulk stream.", MX + 5.4, 5.15, CW - 5.4, 0.75, { fontSize: 18, color: GRAY, valign: "middle", objectName: "penalty explained" });
});
