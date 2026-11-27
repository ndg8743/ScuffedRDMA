// Shared setup for the defense deck (formal style).
// White background, serif titles, navy and gray. Orange and blue appear only for the two traffic classes.
// Bullets are real paragraphs in body placeholders; tables have rules and no fills.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const ROOT = process.env.DECK_ROOT || path.resolve(__dirname, "..", "..");
const A = ROOT + "/assets";
const STATIC = !!process.env.DECK_STATIC;      // handout build: the last frame of each animation instead of the GIF
const MATH = JSON.parse(fs.readFileSync(A + "/math/manifest.json", "utf8"));
// length of one pass of each animation, for the presenter notes (written by tools/durations.py; optional)
const DUR = fs.existsSync(A + "/clips/durations.json") ? JSON.parse(fs.readFileSync(A + "/clips/durations.json", "utf8")) : {};
// photographs and screenshots prepared by tools/photos.py (sizes in pixels)
const PHOTOS = fs.existsSync(A + "/photos/manifest.json") ? JSON.parse(fs.readFileSync(A + "/photos/manifest.json", "utf8")) : {};
const THEME = JSON.parse(fs.readFileSync(path.join(__dirname, "theme.json"), "utf8"));
const H = THEME.colors;                        // hex values, for the options that do not take theme colors
// advance widths of the body font, in em (measured on Carlito, which has the metrics of Calibri)
const METRICS = JSON.parse(fs.readFileSync(path.join(__dirname, "metrics.json"), "utf8"));
function textW(str, size, isBold) {
  const m = METRICS[isBold ? "bold" : "regular"]; let w = 0;
  for (const ch of String(str)) w += m[ch] === undefined ? 0.5 : m[ch];
  return (w * size) / 72;                      // inches
}
// lines a paragraph takes in a box of the given width, with the word wrap of a text box
function linesOf(str, size, widthIn, isBold) {
  const sp = textW(" ", size, isBold); let lines = 1, cur = 0;
  for (const word of String(str).split(/\s+/).filter(Boolean)) {
    const ww = textW(word, size, isBold);
    if (cur === 0) cur = ww; else if (cur + sp + ww <= widthIn) cur += sp + ww; else { lines++; cur = ww; }
  }
  return lines;
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                   // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Adaptive RDMA Middleware for Disaggregated LLM Inference over Commodity Ethernet";
pres.author = "Nathan Gopee";
pres.subject = "M.S. thesis defense, State University of New York at New Paltz";
const C = pres.SchemeColor;
// text1 ink, text2 navy, accent1 blue (bulk class), accent2 dark orange (urgent class, star notes),
// accent3 rule gray, accent4 hairline gray, accent5 text gray, accent6 bright orange (fills of the urgent class)
const INK = C.text1, NAVY = C.text2, WHITE = C.background1, PANEL = C.background2;
const BLUE = C.accent1, ORANGE = C.accent2, RULE = C.accent3, HAIR = C.accent4, GRAY = C.accent5, BRIGHT = C.accent6;

// ---------------------------------------------------------------- geometry (inches)
const W = 13.333, MX = 0.7, CW = W - 2 * MX;   // content width 11.933
const Y0 = 1.62, Y1 = 6.52;                    // content area, top and bottom
const FX = 6.95, FW = W - MX - FX;             // figure column beside a text column ("Text and figure")
const NX = 5.75, NW = W - MX - NX;             // figure column beside a narrow text column

// ---------------------------------------------------------------- slides and parts
const SL = [];                                 // {id, fn} in deck order, filled by def()
function def(id, fn) { if (SL.some((x) => x.id === id)) throw new Error("slide id used twice: " + id); SL.push({ id, fn }); }
const LOOSE = !!process.env.DECK_LOOSE;       // partial builds: a link to a slide that is not built points at slide 1
const num = (id) => { const k = SL.findIndex((x) => x.id === id); if (k < 0) { if (LOOSE) return 1; throw new Error("unknown slide id " + id); } return k + 1; };
const PARTS = [
  { key: "a", n: "", title: "Opening", nav: "Outline", first: "a05" },
  { key: "h", n: "I", title: "The moving bottleneck", nav: "History", line: "Arithmetic, then memory, then the path between machines" },
  { key: "k", n: "II", title: "A language model and its cache", nav: "Model", line: "What attention computes, and what is kept between tokens" },
  { key: "p", n: "III", title: "The problem", nav: "Problem", line: "Megabytes and bytes on one link, and the research questions" },
  { key: "n", n: "IV", title: "RDMA at a low level", nav: "RDMA", line: "What the network card does, and in which order" },
  { key: "m", n: "V", title: "The middleware", nav: "Middleware", line: "One endpoint per class, a channel with credits, a connector" },
  { key: "d", n: "VI", title: "Decisions per transfer", nav: "Decisions", line: "A classifier, a rule tree, a controller, and what is proved" },
  { key: "c", n: "VII", title: "Compression and storage", nav: "Compression", line: "Fewer bytes on the wire, and a place for them to wait" },
  { key: "e", n: "VIII", title: "Testbed and method", nav: "Method", line: "Four servers, the firmware work, and how a result is taken" },
  { key: "r", n: "IX", title: "Results", nav: "Results", line: "What is measured, what is arithmetic, what is pending" },
  { key: "z", n: "X", title: "Conclusions", nav: "Conclusions", line: "Related work, answers, limitations, future work" },
  { key: "b", n: "", title: "Backup slides", nav: "Backup", first: "z13" },
];
PARTS.forEach((p) => { p.first = p.first || p.key + "00"; p.section = p.n ? p.n + ". " + p.title : p.title; });
const partOf = (id) => PARTS.find((p) => p.key === id[0]);

// ---------------------------------------------------------------- layouts
const LAYOUTS = {
  // name: body placeholder (null = none)
  "Title and text": { x: MX, y: Y0, w: CW, h: Y1 - Y0, fontSize: 24 },
  "Text and figure": { x: MX, y: Y0, w: 5.8, h: Y1 - Y0, fontSize: 22 },
  "Narrow text and figure": { x: MX, y: Y0, w: 4.6, h: Y1 - Y0, fontSize: 20 },
  "Text above": { x: MX, y: Y0, w: CW, h: 1.95, fontSize: 22 },
  "Text above, tall": { x: MX, y: Y0, w: CW, h: 3.3, fontSize: 22 },
  "Text below": { x: MX, y: 4.72, w: CW, h: 1.8, fontSize: 22 },
  "Text below, tall": { x: MX, y: 3.25, w: CW, h: 3.27, fontSize: 22 },
  "Two columns": { x: MX, y: Y0, w: 5.65, h: Y1 - Y0, fontSize: 22, second: { x: 6.98, y: Y0, w: 5.65, h: Y1 - Y0, fontSize: 22 } },
  "Title only": null,
  "Statement": { x: 1.3, y: 1.95, w: 10.73, h: 2.7, fontSize: 30, color: NAVY, valign: "middle" },
};
const TITLE_BOX = { x: MX, y: 0.42, w: 10.55, h: 0.95 };
function footer() {
  return [
    { line: { x: MX, y: 6.84, w: CW, h: 0, line: { color: HAIR, width: 0.75 } } },
    { image: { path: A + "/img/logo_small.png", x: MX, y: 6.97, w: 1.14, h: 0.32, altText: "Logo of SUNY New Paltz" } },
  ];
}
const SLIDE_NO = { x: 12.03, y: 6.98, w: 0.6, h: 0.3, fontSize: 11, color: GRAY, align: "right" };
function defineLayouts() {
  pres.defineSlideMaster({
    title: "Title slide", background: { color: WHITE },
    objects: [
      { image: { path: A + "/img/logo.png", x: MX, y: 0.55, w: 3.0, h: 3.0 / 3.5573, altText: "Logo of SUNY New Paltz, State University of New York" } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 1.8, w: CW, h: 1.55, fontSize: 38, bold: true, color: NAVY, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "Part opener", background: { color: WHITE },
    objects: footer().concat([
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.6, w: 6.7, h: 1.5, fontSize: 40, bold: true, color: NAVY, align: "left", valign: "top", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: MX, y: 4.2, w: 6.4, h: 1.5, fontSize: 22, color: GRAY, align: "left", valign: "top", margin: 0 }, text: "" } },
      { line: { x: 7.85, y: 1.45, w: 0, h: 4.75, line: { color: HAIR, width: 0.75 } } },
    ]),
    slideNumber: Object.assign({}, SLIDE_NO),
  });
  for (const backup of [false, true]) {
    for (const [name, body] of Object.entries(LAYOUTS)) {
      if (backup && name === "Statement") continue;
      const objects = footer();
      objects.push({ placeholder: { options: Object.assign({ name: "title", type: "title", fontSize: 32, bold: true, color: NAVY, align: "left", valign: "middle", margin: 0 }, TITLE_BOX), text: "" } });
      if (body) {
        const b1 = Object.assign({ name: "body", type: "body", color: INK, align: "left", valign: "top", margin: 0 }, body); delete b1.second;
        objects.push({ placeholder: { options: b1, text: "" } });
        if (body.second) objects.push({ placeholder: { options: Object.assign({ name: "body2", type: "body", color: INK, align: "left", valign: "top", margin: 0 }, body.second), text: "" } });
      }
      if (backup) objects.push({ text: { text: "BACKUP", options: { x: MX, y: 0.2, w: 2, h: 0.24, fontSize: 11, bold: true, color: GRAY, margin: 0, charSpacing: 2 } } });
      pres.defineSlideMaster({ title: (backup ? "Backup: " : "") + name, background: { color: WHITE }, objects, slideNumber: Object.assign({}, SLIDE_NO) });
    }
  }
}

// ---------------------------------------------------------------- slide, footer tracker, notes
const declared = new Set();
const open_ = [];                              // slides whose footer and notes are still to be written
let words = 0;
const wordsBy = {};                            // spoken words in the notes, by slide id
function newSlide(id, layout, title, notes) {
  const part = partOf(id);
  if (!declared.has(part.section)) { pres.addSection({ title: part.section }); declared.add(part.section); }
  const master = id[0] === "b" ? "Backup: " + layout : layout;
  const s = pres.addSlide({ masterName: master, sectionTitle: part.section });
  s._id = id; s._layout = layout; s._notes = notes || ""; s._part = part;
  s.addText(title, { placeholder: "title" });
  open_.push(s);
  return s;
}
// Called after the content of a slide is in place: the footer links come last in the reading order, and the notes
// get one line for the presenter when the slide shows an animation.
function finish() {
  while (open_.length) {
    const s = open_.shift();
    if (s._layout !== "Title slide") tracker(s, s._part);
    let notes = s._notes;
    const spoken = notes.split(/\n+/).filter((p) => !/^(\*|Timing:)/.test(p.trim())).join(" ").split(/\s+/).filter(Boolean).length;
    wordsBy[s._id] = spoken;
    if (s._id[0] !== "b") words += spoken;
    if (s._anim && DUR[s._anim]) notes += "\n\nAnimation: one pass takes about " + Math.round(DUR[s._anim]) + " seconds, then it repeats.";
    if (notes) s.addNotes(notes);
  }
}
// the part names as plain text in the footer; the current part is bold navy; every name is a link
function tracker(s, part) {
  const cw = 0.074, pad = 0.06;
  const widths = PARTS.map((p) => p.nav.length * cw + 2 * pad);
  const x0 = 2.2, x1 = 11.95, gap = (x1 - x0 - widths.reduce((a, b) => a + b, 0)) / (PARTS.length - 1);
  let x = x0;
  PARTS.forEach((p, k) => {
    const cur = p.key === part.key;
    s.addText(p.nav, { x, y: 6.98, w: widths[k], h: 0.3, fontSize: 11, align: "center", valign: "middle", margin: 0, bold: cur, color: cur ? NAVY : GRAY,
      hyperlink: { slide: num(p.first), tooltip: "Go to: " + (p.n ? "Part " + p.n + ", " : "") + p.title }, objectName: "nav " + p.nav, isTextBox: true });
    x += widths[k] + gap;
  });
}

// ---------------------------------------------------------------- text
// check that a list fits its box, from the measured widths of the words
function fits(id, paras, w, h) {
  let pts = 0;
  for (const p of paras) pts += linesOf(p.text, p.size, w - p.indent / 72, p.bold) * p.size * 1.2 + p.gap;
  if (pts > h * 72 * 1.01) console.warn(`  ! ${id}: text about ${(pts / 72).toFixed(2)} in tall in a box of ${h.toFixed(2)} in`);
}
// "**term** rest" -> runs with the marked part in bold.
// The slide library takes the paragraph properties from the first run and starts a new paragraph at every run
// that has a bullet, so only the first run of a paragraph carries them and only the last one carries breakLine.
function runs(text, o) {
  const parts = String(text).split("**");
  if (parts.length === 1) return [{ text: String(text), options: o }];
  const segs = [];
  parts.forEach((t, k) => { if (t) segs.push({ t, bold: k % 2 === 1 }); });
  return segs.map((sg, k) => {
    const ro = {};
    ["fontSize", "color", "italic"].forEach((key) => { if (o[key] !== undefined) ro[key] = o[key]; });
    if (sg.bold || o.bold) ro.bold = true;
    if (k === 0) ["bullet", "indentLevel", "paraSpaceAfter"].forEach((key) => { if (o[key] !== undefined) ro[key] = o[key]; });
    if (k === segs.length - 1 && o.breakLine) ro.breakLine = true;
    return { text: sg.t, options: ro };
  });
}
// Paragraph runs for a list. items: "text" | ["sub", "sub"] | {t, plain, num, size, color, italic, bold}
function listRuns(items, o = {}) {
  const size = o.size, sub = o.sub || ((size || o.base || 22) - 3), gap = o.gap === undefined ? 14 : o.gap;
  const flat = [];
  items.forEach((it) => {
    if (Array.isArray(it)) it.forEach((t) => flat.push({ t, lvl: 1 }));
    else if (typeof it === "string") flat.push({ t: it, lvl: 0 });
    else flat.push(Object.assign({ lvl: 0 }, it));
  });
  const out = [], meas = [];
  flat.forEach((p, k) => {
    const last = k === flat.length - 1;
    const next = flat[k + 1];
    const ro = { breakLine: !last, paraSpaceAfter: last ? 0 : (next && next.lvl === 1 ? Math.round(gap * 0.5) : (p.lvl === 1 ? Math.round(gap * 0.75) : gap)) };
    if (p.lvl === 1) { ro.bullet = { indent: 20, characterCode: "25E6" }; ro.indentLevel = 1; if (sub) ro.fontSize = sub; ro.color = p.color || INK; }
    else if (p.plain) { ro.bullet = false; }
    else if (p.num || o.num) { ro.bullet = { type: "number", indent: 32 }; if (o.start) ro.bullet.numberStartAt = o.start; }
    else ro.bullet = { indent: 22 };
    if (p.lvl === 0 && (p.size || size)) ro.fontSize = p.size || size;
    if (p.color) ro.color = p.color;
    if (p.italic) ro.italic = true;
    if (p.bold) ro.bold = true;
    runs(p.t, ro).forEach((r) => out.push(r));
    meas.push({ text: String(p.t).replace(/\*\*/g, ""), size: ro.fontSize || o.base || 22, bold: !!p.bold, gap: ro.paraSpaceAfter, indent: p.plain ? 0 : (p.lvl === 1 ? 42 : (p.num || o.num ? 32 : 22)) });
  });
  return { out, meas };
}
// fill the body placeholder of the slide's layout with a list
function B(s, items, o = {}) {
  const box = s._layout === "Part opener" ? { w: 6.4, h: 1.5, fontSize: 22 } : LAYOUTS[s._layout];
  if (!box) throw new Error(s._id + ": layout has no body placeholder");
  const { out, meas } = listRuns(items, Object.assign({ base: box.fontSize }, o));
  fits(s._id, meas, box.w, box.h);
  s.addText(out, { placeholder: "body" });
}
// the second column of the "Two columns" layout
function B2(s, items, o = {}) {
  const box = LAYOUTS[s._layout] && LAYOUTS[s._layout].second;
  if (!box) throw new Error(s._id + ": layout has no second body placeholder");
  const { out, meas } = listRuns(items, Object.assign({ base: box.fontSize }, o));
  fits(s._id, meas, box.w, box.h);
  s.addText(out, { placeholder: "body2" });
}
// the opener of a part: its number, title and one line, and the list of all parts with this one marked
function opener(key, notes) {
  const p = PARTS.find((x) => x.key === key);
  def(key + "00", () => {
    const s = newSlide(key + "00", "Part opener", p.title, notes);
    T(s, "PART " + p.n, MX, 2.1, 4, 0.36, { fontSize: 16, bold: true, color: GRAY, charSpacing: 3, objectName: "part number" });
    B(s, [{ t: p.line, plain: true }]);
    PARTS.filter((x) => x.n).forEach((q, k) => {
      const y = 1.5 + k * 0.47, cur = q.key === key;
      T(s, q.n, 8.2, y, 0.75, 0.4, { fontSize: 17, bold: cur, color: cur ? NAVY : GRAY, valign: "middle", align: "right", objectName: "numeral " + q.n });
      s.addText(q.title, { x: 9.15, y, w: 3.48, h: 0.4, fontSize: 17, bold: cur, color: cur ? NAVY : GRAY, valign: "middle", align: "left", margin: 0,
        hyperlink: { slide: num(q.first), tooltip: "Go to part " + q.n + ": " + q.title }, objectName: "part " + q.n, isTextBox: true });
    });
  });
}
// free text box
function T(s, text, x, y, w, h, o = {}) {
  s.addText(text, Object.assign({ x, y, w, h, fontSize: 20, color: INK, margin: 0, valign: "top", align: "left", isTextBox: true }, o));
}
// a list in a free text box (second column, text beside a table)
function L(s, items, x, y, w, h, o = {}) {
  const { out, meas } = listRuns(items, Object.assign({ base: o.size || 20, size: o.size || 20 }, o));
  fits(s._id, meas, w, h);
  T(s, out, x, y, w, h, { fontSize: o.size || 20, objectName: o.name || "list" });
}
// small gray line: the source or the conditions of what the slide shows
function note(s, text, o = {}) {
  T(s, text, o.x === undefined ? MX : o.x, o.y === undefined ? 6.22 : o.y, o.w || CW, o.h || 0.5, { fontSize: o.size || 16, color: GRAY, valign: "middle", align: o.align || "left", objectName: "note" });
}
// the one line to take away from a figure
function take(s, text, o = {}) {
  T(s, text, o.x === undefined ? MX : o.x, o.y === undefined ? 6.26 : o.y, o.w || CW, o.h || 0.48, { fontSize: o.size || 20, color: NAVY, valign: "middle", align: o.align || "center", objectName: "takeaway" });
}
// note for something still to be measured or fixed: always starts with a star
function star(s, text, x, y, w, h, o = {}) {
  T(s, "* " + text, x, y, w, h || 0.5, Object.assign({ fontSize: 17, color: ORANGE, italic: true, valign: "middle", objectName: "star note" }, o));
}
// a proposition or a key statement on the neutral panel
function claim(s, label, text, x, y, w, h, o = {}) {
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: PANEL }, line: { color: PANEL, width: 0 }, objectName: "panel" });
  const r = label ? [{ text: label + "  ", options: { bold: true, color: NAVY } }, { text }] : text;
  T(s, r, x + 0.25, y + 0.08, w - 0.5, h - 0.16, { fontSize: o.size || 20, valign: "middle", italic: !!o.italic, color: o.color || INK, objectName: "statement" });
}
// big number with a label under it
function stat(s, value, label, x, y, w, o = {}) {
  T(s, value, x, y, w, 0.95, { fontSize: o.size || 54, bold: true, color: o.color || NAVY, valign: "middle", objectName: "figure " + value });
  T(s, label, x, y + 0.98, w, o.lh || 0.8, { fontSize: o.ls || 18, color: GRAY, objectName: "label" });
}

// ---------------------------------------------------------------- links to backup slides
function linkBox(s, label, k, target, tip, name) {
  s.addText(label, { x: 11.45, y: 0.5 + k * 0.42, w: 1.18, h: 0.34, shape: pres.ShapeType.rect, fill: { color: WHITE }, line: { color: NAVY, width: 0.75 },
    fontSize: 13, bold: true, color: NAVY, align: "center", valign: "middle", margin: 0, hyperlink: { slide: num(target), tooltip: tip }, objectName: name, isTextBox: true });
}
function more(s, list) { list.forEach(([label, target], k) => linkBox(s, label + " ›", k, target, label + " (backup slide)", "link " + label)); }
function back(s, origin) { linkBox(s, "‹ Back", 0, origin, "Back to the slide you came from", "back-button"); }

// ---------------------------------------------------------------- drawing
// node of a diagram: a rectangle with centered label; kind: "plain" | "hot" | "cold" | "panel" | "navy" | "none"
function node(s, x, y, w, h, text, o = {}) {
  const kind = o.kind || "plain";
  const fill = kind === "hot" ? { color: BRIGHT, transparency: 82 } : kind === "cold" ? { color: BLUE, transparency: 86 } : kind === "panel" ? { color: PANEL } : kind === "navy" ? { color: NAVY } : { color: WHITE };
  const line = kind === "hot" ? { color: ORANGE, width: 1.25 } : kind === "cold" ? { color: BLUE, width: 1.25 } : kind === "none" ? { color: WHITE, width: 0 } : kind === "navy" ? { color: NAVY, width: 1 } : { color: RULE, width: 1, dashType: o.dash || "solid" };
  s.addText(text, { x, y, w, h, shape: pres.ShapeType.rect, fill, line, fontSize: o.size || 17, color: o.color || (kind === "navy" ? WHITE : INK), bold: !!o.bold, italic: !!o.italic,
    align: o.align || "center", valign: o.valign || "middle", margin: o.margin === undefined ? 5 : o.margin, objectName: o.name || "box", isTextBox: true });   // margin in points
}
function arrow(s, x1, y1, x2, y2, o = {}) {
  s.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1,
    line: { color: o.color || GRAY, width: o.width || 1.5, endArrowType: o.head === false ? "none" : "triangle", beginArrowType: o.both ? "triangle" : "none", dashType: o.dash || "solid" }, objectName: o.name || "arrow" });
}
function hline(s, x, y, w, o = {}) { s.addShape(pres.ShapeType.line, { x, y, w, h: 0, line: { color: o.color || HAIR, width: o.width || 0.75, dashType: o.dash || "solid" }, objectName: "rule" }); }
function vline(s, x, y, h, o = {}) { s.addShape(pres.ShapeType.line, { x, y, w: 0, h, line: { color: o.color || HAIR, width: o.width || 0.75, dashType: o.dash || "solid" }, objectName: "rule" }); }
function rect(s, x, y, w, h, o = {}) { s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: o.fill || { color: WHITE }, line: o.line || { color: RULE, width: 1 }, objectName: o.name || "rectangle" }); }

// formula picture; size = equivalent font size in points (the pictures are rendered at 10 pt)
function eq(s, name, x, y, o = {}) {
  const m = MATH[name]; if (!m) throw new Error("no formula " + name);
  const k = (o.size || 26) / 10;
  let w = (m.w * k) / 72, h = (m.h * k) / 72;
  if (o.maxW && w > o.maxW) { h *= o.maxW / w; w = o.maxW; }
  const xx = o.center ? x - w / 2 : x;
  s.addImage({ path: `${A}/math/${name}${o.navy ? "_navy" : ""}.png`, x: xx, y, w, h, altText: m.alt, objectName: "formula " + name });
  return { w, h };
}
// one large animation, centered under the title
function gif(s, name, alt, o = {}) {
  const w = o.w || 8.6, h = w * 9 / 16, x = o.x === undefined ? (W - w) / 2 : o.x, y = o.y === undefined ? 1.4 : o.y;
  s.addImage({ path: `${A}/clips/${name}.${STATIC ? "last.png" : "gif"}`, x, y, w, h, altText: alt, objectName: "animation " + name });
  s._anim = name;
}

// A photograph or screenshot. Give a width, a height, or both (the picture is then fitted into that box).
// o.cx centers it on a vertical line, o.frame draws a thin border (for pictures with a white background).
// Returns the placed rectangle, so that a caption can follow it.
function pic(s, name, alt, o = {}) {
  const m = PHOTOS[name]; if (!m) throw new Error("no picture " + name);
  const ar = m.w / m.h;
  let w, h;
  if (o.w && o.h) { if (o.w / o.h > ar) { h = o.h; w = h * ar; } else { w = o.w; h = w / ar; } }
  else if (o.h) { h = o.h; w = h * ar; }
  else { w = o.w || 8.6; h = w / ar; }
  const x = o.cx !== undefined ? o.cx - w / 2 : (o.x === undefined ? (W - w) / 2 : o.x), y = o.y === undefined ? 1.5 : o.y;
  s.addImage({ path: `${A}/photos/${m.file}`, x, y, w, h, altText: alt, objectName: "picture " + name });
  if (o.frame) s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: WHITE, transparency: 100 }, line: { color: RULE, width: 0.75 }, objectName: "frame" });
  return { x, y, w, h };
}
// the line under a picture: what it shows
function caption(s, text, r, o = {}) {
  T(s, text, r.x, r.y + r.h + 0.06, r.w, o.h || 0.34, { fontSize: o.size || 16, color: GRAY, valign: "top", align: o.align || "left", objectName: "caption" });
}
// source text in a fixed-width font on the neutral panel; lines is an array of strings
function code(s, lines, x, y, w, o = {}) {
  const size = o.size || 15, lh = (size * 1.25) / 72, h = o.h || lines.length * lh + 0.3;
  const longest = Math.max(...lines.map((l) => l.length));
  if (longest * size * 0.6 / 72 > w - 0.36) console.warn(`  ! ${s._id}: a code line of ${longest} characters does not fit ${w.toFixed(2)} in at ${size} pt`);
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: PANEL }, line: { color: PANEL, width: 0 }, objectName: "panel" });
  // leading spaces as no-break spaces, so that the indentation survives every program
  s.addText(lines.map((t, k) => ({ text: t === "" ? " " : t.replace(/^ +/, (m) => "\u00A0".repeat(m.length)), options: { breakLine: k < lines.length - 1 } })), { x: x + 0.18, y: y + 0.15, w: w - 0.36, h: h - 0.3,
    fontFace: "Courier New", fontSize: size, color: INK, margin: 0, valign: "top", align: "left", paraSpaceAfter: 0, objectName: o.name || "source text", isTextBox: true });
  return { x, y, w, h };
}

// ---------------------------------------------------------------- tables with rules only
const HEAVY = { type: "solid", pt: 1.5, color: H.dk1 }, MID = { type: "solid", pt: 0.75, color: H.dk1 }, FINE = { type: "solid", pt: 0.5, color: H.accent4 }, NONE = { type: "none" };
// head: array of strings; rows: arrays of strings or {text, options}; o.align: per column "left" | "right" | "center"
function tbl(s, head, rows, x, y, w, colW, o = {}) {
  const fs_ = o.size || 18, al = o.align || [];
  const cell = (c, k, base) => {
    const obj = typeof c === "string" ? { text: c, options: {} } : { text: c.text, options: Object.assign({}, c.options || {}) };
    obj.options = Object.assign({ fontSize: fs_, color: INK, valign: "middle", align: al[k] || "left" }, base, obj.options);
    if (typeof obj.text === "string" && obj.text.includes("**")) obj.text = runs(obj.text, { fontSize: obj.options.fontSize, color: obj.options.color });
    return obj;
  };
  const all = [];
  if (head) all.push(head.map((c, k) => cell(c, k, { bold: true, color: NAVY, border: [HEAVY, NONE, MID, NONE] })));
  rows.forEach((r, i) => {
    const lastRow = i === rows.length - 1;
    const top = i === 0 ? (head ? NONE : HEAVY) : (o.lines === false ? NONE : FINE);
    all.push(r.map((c, k) => cell(c, k, { border: [top, NONE, lastRow ? HEAVY : NONE, NONE] })));
  });
  // row heights: the wanted height, or what the wrapped text needs (estimated), whichever is larger
  const rh = o.rowH || 0.5, hh = o.headH || 0.5;
  const plain = (c) => { const t = typeof c === "string" ? c : c.text; return (Array.isArray(t) ? t.map((r) => r.text).join("") : String(t)).replace(/\*\*/g, ""); };
  const need = (r) => Math.max(...r.map((c, k) => {
    const size = (typeof c === "object" && c.options && c.options.fontSize) || fs_, isBold = !!(typeof c === "object" && c.options && c.options.bold);
    return (linesOf(plain(c), size, colW[k] - 0.26, isBold) * size * 1.2) / 72 + 0.14;
  }));
  const heights = (head ? [Math.max(hh, need(head.map((c) => ({ text: plain(c), options: { bold: true } }))))] : []).concat(rows.map((r, i) => Math.max((o.rowHs && o.rowHs[i]) || rh, need(r))));
  const total = heights.reduce((a, b) => a + b, 0);
  s.addTable(all, { x, y, w, h: total, colW, rowH: heights, margin: o.margin || [0.05, 0.12, 0.05, 0.12], autoPage: false, objectName: o.name || "table" });
  return y + total;                                 // the bottom edge, as laid out
}

// one look for every chart: navy first, gray second
const CH = {
  catAxisLabelColor: H.dk1, valAxisLabelColor: H.dk1, catAxisLabelFontSize: 14, valAxisLabelFontSize: 14,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt", legendFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  valGridLine: { color: "D9DDE2", size: 0.75 }, catGridLine: { style: "none" },
  showTitle: true, titleFontSize: 16, titleColor: H.dk1, dataLabelFontSize: 14, dataLabelColor: H.dk1,
  catAxisTitleFontFace: "+mn-lt", valAxisTitleFontFace: "+mn-lt", catAxisTitleFontSize: 14, valAxisTitleFontSize: 14, catAxisTitleColor: H.accent5, valAxisTitleColor: H.accent5,
  legendFontSize: 14, legendColor: H.dk1,
};

module.exports = { pres, THEME, H, ROOT, STATIC, A, C, MATH, INK, NAVY, WHITE, PANEL, BLUE, ORANGE, RULE, HAIR, GRAY, BRIGHT,
  W, MX, CW, Y0, Y1, FX, FW, NX, NW, SL, def, num, PARTS, partOf, defineLayouts, newSlide, finish, opener, B, B2, T, L, note, take, star, claim, stat, more, back,
  node, arrow, hline, vline, rect, eq, gif, pic, caption, code, tbl, CH, runs, textW, linesOf, wordCount: () => words, wordsBy };
