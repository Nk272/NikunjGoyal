const fs = require("fs");
const h = fs.readFileSync(__dirname + "/index.html", "utf8");
const m = h.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.log("NO SCRIPT FOUND"); process.exit(1); }
fs.writeFileSync(__dirname + "/_extracted.js", m[1]);
console.log("extracted", m[1].length, "chars");
