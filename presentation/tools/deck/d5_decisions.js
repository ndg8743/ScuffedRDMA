// Part VI: decisions per transfer (classifier, rule tree, controller).
const { pres, H, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT, W, MX, CW, Y0, Y1, FX, FW, num, def,
  newSlide, opener, B, B2, T, L, note, take, star, claim, stat, more, node, arrow, hline, vline, rect, eq, gif, tbl, CH } = require("./lib");

const bold = (t) => ({ text: t, options: { bold: true } });
const hot = (t) => ({ text: t, options: { bold: true, color: ORANGE } });
const cold = (t) => ({ text: t, options: { bold: true, color: BLUE } });

opener("d", "Above the transport, five components decide what happens to each transfer or act on that decision. The analysis found issues in two of them.");

def("d01", () => {
  const s = newSlide("d01", "Title only", "Three components decide, two act",
    "Three components decide: the classifier says hot or cold, the rule tree turns labels and the state of the system into a decision, and the controller was intended to balance the two queues. Two act: the quantizer and the storage tier.\n\n" +
    "Of the five, the static classifier and the quantizer run on the serving path.");
  const items = [["Classifier", "Is this transfer hot or cold?", "static version on the serving path", true],
    ["Rule tree", "Labels and the state of the system become a decision", "evaluated on its own", false],
    ["Controller", "Meant to balance the two queues; its switching rule has an issue", "evaluated on its own", false],
    ["Quantizer", "Packs cache vectors into fewer bytes, for the wire and for disk", "on the serving path", true],
    ["Storage tier", "Moves cache blocks to an NVMe drive when GPU memory is short", "evaluated on its own", false]];
  const w = 2.2, xs = [MX, MX + 2.33, MX + 4.66, MX + 7.4, MX + 9.733];
  T(s, "Decide", xs[0], 1.5, 3, 0.4, { fontSize: 19, bold: true, color: NAVY, objectName: "heading decide" });
  T(s, "Act", xs[3], 1.5, 3, 0.4, { fontSize: 19, bold: true, color: NAVY, objectName: "heading act" });
  items.forEach(([name, what, status, on], k) => {
    rect(s, xs[k], 1.98, w, 2.5, { name: "box " + name });
    T(s, name, xs[k] + 0.14, 2.06, w - 0.28, 0.42, { fontSize: 20, bold: true, valign: "middle", objectName: name });
    T(s, what, xs[k] + 0.14, 2.52, w - 0.28, 1.2, { fontSize: 16, objectName: name + " text" });
    T(s, status, xs[k] + 0.14, 3.75, w - 0.28, 0.65, { fontSize: 15, bold: on, color: on ? NAVY : GRAY, valign: "bottom", objectName: name + " status" });
  });
  arrow(s, xs[2] + w + 0.08, 3.23, xs[3] - 0.08, 3.23, { color: NAVY, width: 2 });
  T(s, [{ text: "Input:  ", options: { bold: true } }, { text: "one record per transfer, taken at the sender: size, access count, queue depth, phase, sequence length, time since the previous transfer, control flag." }], MX, 4.7, CW, 0.75, { fontSize: 18, valign: "middle", objectName: "input record" });
  claim(s, "", "The cache that the model computes with stays in 16-bit on the GPU. The quantizer and the storage tier work on data in transit and at rest.", MX, 5.52, CW, 0.98, { size: 20 });
});

def("d02", () => {
  const s = newSlide("d02", "Text and figure", "The static classifier: three states",
    "The classifier keeps one small automaton per tensor with three states. A tensor that is used often or is small moves toward hot, one that is idle or large moves toward cold, and transfers in the hot state use the hot endpoint.");
  B(s, ["One small automaton per tensor, with three states",
    "Used often, or small: toward hot",
    "Idle, or large: toward cold",
    "Transfers in the hot state use the hot endpoint"]);
  const st = [["Cold", BLUE, BLUE, 86], ["Warm", RULE, INK, 100], ["Hot", ORANGE, ORANGE, 82]], d = 1.35, y = 2.75;
  const xs = [FX + 0.1, FX + FW / 2 - d / 2, FX + FW - d - 0.1];
  st.forEach(([n, lc, tc, tr], k) => {
    s.addShape(pres.ShapeType.ellipse, { x: xs[k], y, w: d, h: d, fill: { color: k === 1 ? WHITE : (k === 0 ? BLUE : BRIGHT), transparency: k === 1 ? 0 : tr }, line: { color: lc, width: 2 }, objectName: "state " + n });
    T(s, n, xs[k], y, d, d, { fontSize: 21, bold: true, color: tc, align: "center", valign: "middle", objectName: "state name " + n });
  });
  [0, 1].forEach((k) => {
    arrow(s, xs[k] + d + 0.06, y + 0.45, xs[k + 1] - 0.06, y + 0.45, { color: ORANGE, width: 2 });
    arrow(s, xs[k + 1] - 0.06, y + 0.9, xs[k] + d + 0.06, y + 0.9, { color: BLUE, width: 2 });
  });
  T(s, "used often, or small", FX, y - 0.75, FW, 0.4, { fontSize: 17, bold: true, color: ORANGE, align: "center", objectName: "label toward hot" });
  T(s, "idle, or large", FX, y + d + 0.35, FW, 0.4, { fontSize: 17, bold: true, color: BLUE, align: "center", objectName: "label toward cold" });
});

def("d03", () => {
  const s = newSlide("d03", "Two columns", "Thresholds and the phase detector",
    "The static version uses fixed thresholds on the size, and a phase detector that looks at the last eight layer numbers. The next slide shows what this detector reports during decoding.");
  B(s, [{ t: "Size thresholds", plain: true, bold: true, color: NAVY, size: 24 },
    "Under 4 KiB: hot", "Over 256 KiB: cold", "In between: hot once the tensor has been accessed ten times"]);
  B2(s, [{ t: "Phase detector", plain: true, bold: true, color: NAVY, size: 24 },
    "Looks at the last eight layer numbers", "Prefill if each is one more than the one before", "Decode if the last three are equal", "Unknown otherwise"]);
  vline(s, 6.66, Y0 + 0.05, 3.9);
});

def("d04", () => {
  const s = newSlide("d04", "Title only", "What the detector reports during decoding",
    "During decoding each new token updates the layers in order, from 0 up to 39 and then 0 again. The detector asks for three equal layer numbers in a row before it says decode. Consecutive transfers have different layer numbers, so that condition is not met.\n\n" +
    "With 40 layers the detector answers prefill 82.5 percent of the time and unknown at the wrap, and it does not answer decode.");
  gif(s, "m8_phase_detector", "Animation. A tape of layer numbers 0 to 39 repeating slides under a window of the last 8 numbers. While the numbers rise by one the detector answers prefill; when the window contains the wrap from 39 to 0 it answers unknown. After 40 steps the counts are prefill 33, unknown 7, decode 0: 82.5 percent, 17.5 percent and 0 percent. The last three numbers in the window are not equal at any step.");
  note(s, "With 40 layers, 7 of every 40 windows contain the wrap from layer 39 to layer 0.", { align: "center", y: 6.28 });
});

def("d05", () => {
  const s = newSlide("d05", "Text below, tall", "Proposition 6.1 and two checks",
    "We prove this as Proposition 6.1, and two checks agree with it. A synthetic stream of 8,000 decode transfers gave zero decode labels, and one recorded run on a real device gave none as well.\n\n" +
    "As a consequence, cache updates of a running request, which are small and urgent, are treated as bulk.");
  claim(s, "Proposition 6.1", "On a stream of layer numbers 0, 1, ..., L − 1 repeating, with L at least 2, the static phase detector does not report decode.", MX, 1.62, CW, 1.25, { size: 21 });
  B(s, ["The detector needs three equal layer numbers in a row, and consecutive transfers have different ones",
    "Checked on 8,000 synthetic decode transfers: 6,605 prefill, 1,395 unknown, 0 decode",
    "Consequence: cache updates of a running request, small and urgent, are treated as bulk"]);
  more(s, [["Proof", "b05"]]);
});

def("d06", () => {
  const s = newSlide("d06", "Title only", "A learned classifier",
    "The replacement keeps the three states and learns the weights. Each possible next state has a weight vector, and the probability of moving there is a softmax over the three scores.\n\nThe features include the phase and its product with the logarithm of the size, so the model can hold a different size cut-off in each phase.");
  gif(s, "m7_classifier", "Animation. A weight matrix with one row for each next state, Cold, Warm and Hot, is multiplied by the feature vector phi of x of one transfer. Each row gives one score, drawn as a bar. A softmax turns the three scores into probabilities that sum to 1, and the most probable state, Hot, selects the hot endpoint. The weights shown are illustrative.");
  note(s, "The features include the phase and its product with the logarithm of the size. The weights shown are illustrative.", { align: "center", y: 6.28 });
});

def("d07", () => {
  const s = newSlide("d07", "Text and figure", "What is proved, and what the evaluation shows",
    "Two things are proved. The training objective has a unique minimizer, and a size cut-off per phase can be represented.\n\n" +
    "The table is on synthetic traffic with a synthetic oracle, so the learned score is partly by construction. It shows that the model can represent the intended policy and that training finds it.");
  B(s, ["**Proposition 6.2:** training has a unique minimizer",
    "**Proposition 6.3:** a size cut-off per phase is representable",
    "The table shows that the model can represent the intended policy and that training finds it",
    "Real traces, labeled by measured latency, are future work"]);
  const bottom = tbl(s, ["Traffic mix", "Static", "Learned"], [
    ["Balanced", "0.261", "0.999"], ["Decode-heavy", "0.171", "0.999"], ["Prefill-heavy", "1.000", "0.999"], ["Bursty", "0.489", "0.999"],
  ], FX, 1.7, FW, [2.68, 1.5, 1.5], { size: 19, rowH: 0.56, align: ["left", "right", "right"], name: "routing accuracy" });
  note(s, "Routing accuracy on synthetic traffic with a synthetic oracle: 4,000 held-out events per mix.", { x: FX, y: bottom + 0.1, w: FW, h: 0.7 });
  more(s, [["Detail", "b06"]]);
});

def("d08", () => {
  const s = newSlide("d08", "Text and figure", "The rule tree",
    "The policy is a list of rules with priorities. A decision has two fields, the route and whether to compress. The rules are tried from the highest priority down, a rule sets the fields that are still unset, and evaluation stops when both are set.");
  B(s, ["A decision has two fields: the route, and whether to compress",
    "Rules are tried from the highest priority down",
    "A rule sets the fields that are still unset",
    "Defaults: route cold, no compression"]);
  const cx = FX + FW / 2, w = 5.2, x = cx - w / 2;
  node(s, x, 1.75, w, 0.9, [{ text: "One transfer", options: { bold: true, breakLine: true } }, { text: "its record, its label, the state of the system", options: { fontSize: 15 } }], { size: 18, name: "input" });
  arrow(s, cx, 2.67, cx, 3.08);
  node(s, x, 3.1, w, 0.9, [{ text: "Rules, by priority", options: { bold: true, breakLine: true } }, { text: "a condition, and an action that sets one or both fields", options: { fontSize: 15 } }], { size: 18, kind: "panel", name: "rules" });
  arrow(s, cx, 4.02, cx, 4.43);
  node(s, x, 4.45, w, 1.2, [{ text: "Decision", options: { bold: true, breakLine: true } }, { text: "route: hot, cold, or spill to storage", options: { fontSize: 16, breakLine: true } }, { text: "compress: yes or no", options: { fontSize: 16 } }], { size: 18, name: "decision" });
});

def("d09", () => {
  const s = newSlide("d09", "Title only", "The default policy",
    "This is the default policy. Control messages go to the hot route. Large transfers go to storage when GPU memory is nearly full, and they are compressed when the link is busy.\n\n" +
    "Its thresholds are initial values, and the results we report do not depend on them.");
  const bottom = tbl(s, ["Priority", "Condition", "Action"], [
    ["100", "control message", hot("route hot")],
    ["90", "GPU memory at least 90 % full, size over 256 KiB, not decode", bold("route to storage")],
    ["80", "decode phase and a small cache update", hot("route hot")],
    ["70", "prefill phase and size over 64 KiB", cold("route cold")],
    ["60", "link at least 80 % busy, route cold or storage, size at least 256 KiB", bold("compress")],
    ["30", "classifier says hot and size at most 256 KiB", hot("route hot")],
    ["20", "size under 4 KiB", hot("route hot")],
  ], MX, 1.62, CW, [1.4, 8.0, 2.533], { size: 18, rowH: 0.52, name: "default policy" });
  note(s, "The thresholds are initial values, and the reported results do not depend on them.", { y: bottom + 0.1, h: 0.42, size: 17 });
});

def("d10", () => {
  const s = newSlide("d10", "Text and figure", "The controller: a model of two queues",
    "The controller comes from an optimal control model of two queues that share one link. In that model the best control is all or nothing, and a switching function S decides which: positive S means serve the hot queue.");
  B(s, ["Two queues share one link, and u is the share of the link that serves the hot queue",
    "The cost is the weighted backlog, with more weight on the hot queue",
    "The best control is all or nothing",
    "The switching function S decides: positive S means serve the hot queue"]);
  T(s, "The two queues", FX, 1.72, FW, 0.38, { fontSize: 18, color: GRAY, objectName: "label" });
  eq(s, "queues", FX, 2.2, { size: 20, maxW: FW });
  T(s, "The switching function", FX, 3.45, FW, 0.38, { fontSize: 18, color: GRAY, objectName: "label" });
  eq(s, "switching", FX, 3.95, { size: 26 });
  note(s, "q backlog, λ arrival rate, μ service rate, C link rate, p the cost of one more unit of backlog; H hot, C cold.", { x: FX, y: 4.75, w: FW, h: 0.8 });
  more(s, [["Detail", "b07"]]);
});

def("d11", () => {
  const s = newSlide("d11", "Title only", "The issue in the switching rule",
    "The implementation routes a new transfer instead of allocating service. It sends new work to the cold path once the hot backlog exceeds a tenth of the cold backlog. The rule that follows from the model does so above two and a half times the cold backlog.\n\n" +
    "So the implemented rule leaves the hot path at 25 times less hot backlog.");
  gif(s, "m10_controller", "Animation of the plane of hot backlog and cold backlog. The implemented rule sends a new transfer to the cold path once the hot backlog exceeds one tenth of the cold backlog, which colours almost the whole plane cold. The rule that follows from the model sends cold when the hot backlog exceeds two and a half times the cold backlog. In the wedge between the two lines the rules disagree. The factor between them is 25.");
  note(s, "In the wedge between the two lines, the implemented rule and the rule that follows from the model disagree.", { align: "center", y: 6.28 });
});

def("d12", () => {
  const s = newSlide("d12", "Two columns", "Two parts of the issue, and the evidence",
    "The issue has two parts, the sign and the form. A unit test pins the rule as implemented, and the reported results do not depend on it.\n\n* Decide before submission which of the two repairs to make.");
  B(s, [{ t: "The issue", plain: true, bold: true, color: NAVY, size: 24 },
    "**The sign:** positive S says serve the hot queue, yet the code sends new work to the cold path",
    "**The form:** for joining a queue the expected wait is the backlog divided by the rate, and the code multiplies by the rate"]);
  B2(s, [{ t: "The evidence", plain: true, bold: true, color: NAVY, size: 24 },
    "One recorded run: 1,000 decisions, all of them cold",
    "A synthetic grid of queue lengths: hot in 6 % of cases, against 79 % with the consistent rule",
    "A unit test pins the rule as implemented, and the reported results do not depend on it"]);
  vline(s, 6.66, Y0 + 0.05, 3.7);
  star(s, "Decide before submission: keep it a router and use the consistent rule, or make it allocate service and correct the sign.", MX, 5.75, CW, 0.7);
});
