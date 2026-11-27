// Builds the defense deck:  node build.js [out.pptx]   then   python3 ../post.py out.pptx final.pptx theme.json
// DECK_STATIC=1 builds the handout variant (last frame of each animation instead of the GIF).
// DECK_LOOSE=1 lets a partial build through while slide modules are missing: a link to a slide that is not built
// points at slide 1.
const fs = require("fs");
const path = require("path");
const lib = require("./lib");
const { pres, ROOT, SL, defineLayouts, finish } = lib;

const out = process.argv[2] || path.join(ROOT, "out", "deck_raw.pptx");
// slide modules, in deck order
const MODULES = ["d1_front", "d2_problem", "d3_rdma", "d4_middleware", "d5_decisions", "d6_compression", "d7_method", "d8_results", "d9_closing", "d10_backup"];
for (const m of MODULES) if (fs.existsSync(path.join(__dirname, m + ".js"))) require("./" + m);

// The theme colors and fonts are written by tools/post.py, which runs on the file this script writes.

(async () => {
  defineLayouts();
  for (const { id, fn } of SL) {
    try { fn(); finish(); } catch (e) { console.error("slide " + id + ": " + e.message); throw e; }
  }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await pres.writeFile({ fileName: out });
  const trunk = SL.filter((x) => x.id[0] !== "b").length;
  console.log("wrote", out, "| slides", SL.length, "(" + trunk + " in the talk, " + (SL.length - trunk) + " backup)", "| spoken words in the notes of the talk:", lib.wordCount(),
    "| next: post.py");
})().catch((e) => { console.error(e); process.exit(1); });
