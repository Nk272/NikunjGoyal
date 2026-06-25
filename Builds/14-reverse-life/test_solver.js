// Pure-logic copy of the reverse-life solver for verification (no DOM).
function makeBoard(n, fill = 0) {
  const b = [];
  for (let r = 0; r < n; r++) b.push(new Uint8Array(n).fill(fill));
  return b;
}
function stepForward(board) {
  const n = board.length;
  const out = makeBoard(n);
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
    let nb = 0;
    for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
      if (dr === 0 && dc === 0) continue;
      const rr = r + dr, cc = c + dc;
      if (rr >= 0 && rr < n && cc >= 0 && cc < n && board[rr][cc]) nb++;
    }
    const alive = board[r][c];
    out[r][c] = (nb === 3 || (alive && nb === 2)) ? 1 : 0;
  }
  return out;
}
function boardsEqual(a, b) {
  const n = a.length;
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (a[r][c] !== b[r][c]) return false;
  return true;
}
function solveReverse(target, opts) {
  const n = target.length;
  const cap = (opts && opts.cap) || 8000000;
  const W = n;
  function bit(mask, c) { return (c >= 0 && c < W) ? ((mask >>> c) & 1) : 0; }
  function validateRow(t, above, mid, below) {
    const trow = target[t];
    for (let c = 0; c < W; c++) {
      const nb = bit(above,c-1)+bit(above,c)+bit(above,c+1)+bit(mid,c-1)+bit(mid,c+1)+bit(below,c-1)+bit(below,c)+bit(below,c+1);
      const alive = bit(mid, c);
      const next = (nb === 3 || (alive && nb === 2)) ? 1 : 0;
      if (next !== trow[c]) return false;
    }
    return true;
  }
  const numMasks = 1 << W;
  const rows = new Int32Array(n);
  const failed = new Set();
  let nodes = 0, capped = false;
  function dfs(r) {
    if (capped) return false;
    if (nodes > cap) { capped = true; return false; }
    nodes++;
    if (r === n) return validateRow(n-1, n>=2?rows[n-2]:0, rows[n-1], 0);
    const pp = r>=2?rows[r-2]:0, p = r>=1?rows[r-1]:0;
    const memoKey = r+":"+pp+":"+p;
    if (failed.has(memoKey)) return false;
    for (let m = 0; m < numMasks; m++) {
      if (r >= 1) { if (!validateRow(r-1, pp, p, m)) continue; }
      rows[r] = m;
      if (dfs(r+1)) return true;
      if (capped) return false;
    }
    failed.add(memoKey);
    return false;
  }
  const found = dfs(0);
  if (capped) return { status: "capped", nodes };
  if (!found) return { status: "none", nodes };
  const pred = makeBoard(n);
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) pred[r][c] = (rows[r] >>> c) & 1;
  return { status: "found", pred, nodes };
}

// ---- TESTS ----
let pass = 0, fail = 0;
function check(name, cond) { if (cond) { pass++; } else { fail++; console.log("FAIL:", name); } }

// 1. Round-trip: random boards -> step forward -> solve reverse -> must find a predecessor that steps to same target
for (let n = 3; n <= 9; n++) {
  for (let t = 0; t < 12; t++) {
    const b = makeBoard(n);
    for (let r=0;r<n;r++) for (let c=0;c<n;c++) b[r][c] = Math.random()<0.4?1:0;
    const tgt = stepForward(b);
    const res = solveReverse(tgt, {cap: 5000000});
    if (res.status === "found") {
      check(`roundtrip n=${n} verifies`, boardsEqual(stepForward(res.pred), tgt));
    } else if (res.status === "none") {
      // impossible: we constructed a real predecessor b
      check(`roundtrip n=${n} should find (had real pred)`, false);
    } // capped allowed for large
  }
}

// 2. Known Garden of Eden cannot happen easily; instead test a known no-predecessor small case:
//    A single live cell isolated -> next step it dies (0 neighbors). Target = single live cell:
//    does a 1-cell-alive target have a predecessor? Born needs exactly 3 neighbors.
const t3 = makeBoard(5); t3[2][2]=1;
const r3 = solveReverse(t3,{cap:5000000});
check("single-cell target solved (found or none, not error)", r3.status==="found"||r3.status==="none");
if (r3.status==="found") check("single-cell pred verifies", boardsEqual(stepForward(r3.pred), t3));

// 3. Empty target always has predecessor (empty board)
const te = makeBoard(6);
const re = solveReverse(te,{cap:5000000});
check("empty target found", re.status==="found");
check("empty target pred verifies", re.status==="found" && boardsEqual(stepForward(re.pred), te));

// 4. Blinker target (3 in a row) should have predecessor
const tb = makeBoard(7); tb[3][2]=tb[3][3]=tb[3][4]=1;
const rb = solveReverse(tb,{cap:5000000});
check("blinker found", rb.status==="found");
if (rb.status==="found") check("blinker pred verifies", boardsEqual(stepForward(rb.pred), tb));

// 5. 12x12 performance (sparse)
const big = makeBoard(12); big[5][5]=big[5][6]=big[6][5]=big[6][6]=1; // block
const t0=Date.now();
const rbig = solveReverse(big,{cap:8000000});
const dt=Date.now()-t0;
check("12x12 block solved within cap", rbig.status==="found"||rbig.status==="none");
console.log(`12x12 block: status=${rbig.status} nodes=${rbig.nodes} time=${dt}ms`);
if(rbig.status==="found") check("12x12 block verifies", boardsEqual(stepForward(rbig.pred), big));

console.log(`\nPASS=${pass} FAIL=${fail}`);
process.exit(fail===0?0:1);
