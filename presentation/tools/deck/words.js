// node words.js : spoken words in the speaker notes by part, and for the shorter path named in the Outline notes.
const fs = require("fs"), path = require("path");
const lib = require("./lib");
for (const m of ["d1_front", "d2_problem", "d3_rdma", "d4_middleware", "d5_decisions", "d6_compression", "d7_method", "d8_results", "d9_closing", "d10_backup"]) require("./" + m);
lib.defineLayouts();
for (const { fn } of lib.SL) { fn(); lib.finish(); }
const WPM = 130, by = lib.wordsBy;
const talk = lib.SL.map((x) => x.id).filter((id) => id[0] !== "b");
const sum = (ids) => ids.reduce((a, id) => a + (by[id] || 0), 0);
for (const p of lib.PARTS.filter((p) => p.key !== "b")) {
  const ids = talk.filter((id) => id[0] === p.key);
  console.log((p.n || "-").padEnd(5), p.title.padEnd(32), String(ids.length).padStart(3), "slides", String(sum(ids)).padStart(5), "words", (sum(ids) / WPM).toFixed(1).padStart(5), "min");
}
const skip = (id) => id[0] === "h" || id[0] === "n" || ["m11", "m32", "m33", "m34", "m35", "d08", "d09", "c09", "c10", "z01", "z02"].includes(id);
const short = talk.filter((id) => !skip(id));
console.log("whole talk:", talk.length, "slides,", sum(talk), "words,", (sum(talk) / WPM).toFixed(1), "min at", WPM, "words a minute");
console.log("shorter path:", short.length, "slides,", sum(short), "words,", (sum(short) / WPM).toFixed(1), "min");
