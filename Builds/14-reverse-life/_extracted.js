
"use strict";

/* ============================== STATE ============================== */
const state = {
  N: 7,
  target: [],      // N×N Uint8 (0/1) — editable target board
  pred: null,      // N×N predecessor, or null
  predValid: false,
  stepped: false,  // whether forward-step preview is shown on target overlay
};

const $ = id => document.getElementById(id);

function makeBoard(n, fill = 0) {
  const b = [];
  for (let r = 0; r < n; r++) b.push(new Uint8Array(n).fill(fill));
  return b;
}

/* ============================== FORWARD STEP ======================= */
/* B3/S23 with dead (finite) border. */
function stepForward(board) {
  const n = board.length;
  const out = makeBoard(n);
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      let nb = 0;
      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          const rr = r + dr, cc = c + dc;
          if (rr >= 0 && rr < n && cc >= 0 && cc < n && board[rr][cc]) nb++;
        }
      }
      const alive = board[r][c];
      out[r][c] = (nb === 3 || (alive && nb === 2)) ? 1 : 0;
    }
  }
  return out;
}

function boardsEqual(a, b) {
  const n = a.length;
  for (let r = 0; r < n; r++)
    for (let c = 0; c < n; c++)
      if (a[r][c] !== b[r][c]) return false;
  return true;
}

/* ============================== REVERSE SOLVER =====================
 * Backtracking over predecessor row "profiles" (bitmasks of width N).
 * When predecessor rows r-2, r-1, r are fixed, target row r-1 is fully
 * determined and validated -> aggressive pruning. Failed (r, prevprev,
 * prev) profiles are memoised. Border cells are dead (finite board).
 * ================================================================== */
function solveReverse(target, opts) {
  const n = target.length;
  const cap = (opts && opts.cap) || 8_000_000;
  const W = n;

  // target rows as bitmask for quick compare not needed; keep as arrays.
  // Count of bits helper not needed.

  // Validate that predecessor rows (above, mid, below) produce target row t.
  // above/mid/below are integer bitmasks; bit c = column c.
  function bit(mask, c) {
    return (c >= 0 && c < W) ? ((mask >>> c) & 1) : 0;
  }
  function validateRow(t, above, mid, below) {
    const trow = target[t];
    for (let c = 0; c < W; c++) {
      const nb =
        bit(above, c - 1) + bit(above, c) + bit(above, c + 1) +
        bit(mid,   c - 1) +                 bit(mid,   c + 1) +
        bit(below, c - 1) + bit(below, c) + bit(below, c + 1);
      const alive = bit(mid, c);
      const next = (nb === 3 || (alive && nb === 2)) ? 1 : 0;
      if (next !== trow[c]) return false;
    }
    return true;
  }

  const numMasks = 1 << W;          // 2^N candidate profiles per row
  const rows = new Int32Array(n);   // chosen predecessor row masks
  const failed = new Set();         // memoised dead ends: key = r*BIG + pp*numMasks + p ... use string
  let nodes = 0;
  let capped = false;

  // dfs chooses predecessor row r given rows[r-1], rows[r-2] already set.
  function dfs(r) {
    if (capped) return false;
    if (nodes > cap) { capped = true; return false; }
    nodes++;

    if (r === n) {
      // all rows chosen; validate final target row (n-1) with below = 0.
      return validateRow(n - 1, n >= 2 ? rows[n - 2] : 0, rows[n - 1], 0);
    }

    const pp = r >= 2 ? rows[r - 2] : 0;
    const p  = r >= 1 ? rows[r - 1] : 0;
    const memoKey = r + ":" + pp + ":" + p;
    if (failed.has(memoKey)) return false;

    for (let m = 0; m < numMasks; m++) {
      // Choosing rows[r] = m completes target row (r-1) [if r>=1].
      if (r >= 1) {
        if (!validateRow(r - 1, pp, p, m)) continue;
      }
      rows[r] = m;
      if (dfs(r + 1)) return true;
      if (capped) return false;
    }
    failed.add(memoKey);
    return false;
  }

  const found = dfs(0);
  if (capped) return { status: "capped", nodes };
  if (!found) return { status: "none", nodes };

  // reconstruct board from row masks
  const pred = makeBoard(n);
  for (let r = 0; r < n; r++)
    for (let c = 0; c < n; c++)
      pred[r][c] = (rows[r] >>> c) & 1;
  return { status: "found", pred, nodes };
}

/* ============================== RENDERING ========================== */
const CELL = 30, GAP = 0;
function cellSize(n) {
  // keep total board roughly constant width ~ 330px
  const total = 330;
  return Math.max(16, Math.min(38, Math.floor(total / n)));
}

function buildGrid(svgEl, n) {
  const cs = cellSize(n);
  const dim = cs * n;
  svgEl.setAttribute("width", dim);
  svgEl.setAttribute("height", dim);
  svgEl.setAttribute("viewBox", `0 0 ${dim} ${dim}`);
  while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild);
  const SVGNS = "http://www.w3.org/2000/svg";
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const rect = document.createElementNS(SVGNS, "rect");
      rect.setAttribute("class", "cell");
      rect.setAttribute("x", c * cs);
      rect.setAttribute("y", r * cs);
      rect.setAttribute("width", cs);
      rect.setAttribute("height", cs);
      rect.setAttribute("rx", Math.max(2, cs * 0.12));
      rect.dataset.r = r;
      rect.dataset.c = c;
      svgEl.appendChild(rect);
    }
  }
  // grid lines
  for (let i = 1; i < n; i++) {
    const v = document.createElementNS(SVGNS, "line");
    v.setAttribute("class", "gl"); v.setAttribute("x1", i * cs); v.setAttribute("y1", 0);
    v.setAttribute("x2", i * cs); v.setAttribute("y2", dim);
    svgEl.appendChild(v);
    const h = document.createElementNS(SVGNS, "line");
    h.setAttribute("class", "gl"); h.setAttribute("x1", 0); h.setAttribute("y1", i * cs);
    h.setAttribute("x2", dim); h.setAttribute("y2", i * cs);
    svgEl.appendChild(h);
  }
}

function colorLive(kind) {
  // kind: 'target' (gold) or 'pred' (buy/teal)
  return kind === "pred" ? "var(--buy)" : "var(--gold)";
}
function colorDead() { return "var(--surface-2)"; }

function paintGrid(svgEl, board, kind, ghost) {
  // ghost: optional board of "expected" cells to outline (for step verification)
  const rects = svgEl.querySelectorAll("rect.cell");
  rects.forEach(rect => {
    const r = +rect.dataset.r, c = +rect.dataset.c;
    const live = board && board[r] ? board[r][c] : 0;
    rect.setAttribute("fill", live ? colorLive(kind) : colorDead());
    rect.setAttribute("stroke", "none");
    rect.setAttribute("stroke-width", "0");
    if (ghost && ghost[r]) {
      const want = ghost[r][c];
      if (want !== live) {
        // mismatch: red outline
        rect.setAttribute("stroke", "var(--sell)");
        rect.setAttribute("stroke-width", "2");
      }
    }
  });
}

function renderAll() {
  const n = state.N;
  $("dims-num").textContent = n + "×" + n;
  paintGrid($("target-grid"), state.target, "target",
            state.stepped && state.predValid ? state.predStepResult : null);
  paintGrid($("pred-grid"), state.predValid ? state.pred : null, "pred", null);
  if (!state.predValid) $("pred-sub").textContent = "— solver output —";
}

/* ============================== PAINTING =========================== */
let painting = false, paintVal = 1;
function setupPainting() {
  const svg = $("target-grid");
  function cellFromEvent(e) {
    const pt = (e.touches && e.touches[0]) || e;
    const target = document.elementFromPoint(pt.clientX, pt.clientY);
    if (target && target.classList.contains("cell")) return target;
    return null;
  }
  function applyTo(rect) {
    if (!rect) return;
    const r = +rect.dataset.r, c = +rect.dataset.c;
    if (state.target[r][c] === paintVal) return;
    state.target[r][c] = paintVal;
    invalidatePred();
    rect.setAttribute("fill", paintVal ? colorLive("target") : colorDead());
  }
  svg.addEventListener("pointerdown", e => {
    const rect = e.target.closest("rect.cell");
    if (!rect) return;
    e.preventDefault();
    const r = +rect.dataset.r, c = +rect.dataset.c;
    paintVal = state.target[r][c] ? 0 : 1;
    painting = true;
    applyTo(rect);
    svg.setPointerCapture(e.pointerId);
  });
  svg.addEventListener("pointermove", e => {
    if (!painting) return;
    applyTo(cellFromEvent(e));
  });
  window.addEventListener("pointerup", () => { painting = false; });
}

function invalidatePred() {
  state.predValid = false;
  state.pred = null;
  state.stepped = false;
  $("step").disabled = true;
  paintGrid($("pred-grid"), null, "pred", null);
  $("pred-sub").textContent = "— solver output —";
}

/* ============================== ACTIONS ============================ */
function doSolve() {
  invalidatePred();
  const n = state.N;
  $("status").innerHTML = "Searching for a predecessor…";
  // let the UI paint before the (possibly heavy) synchronous solve
  setTimeout(() => {
    const t0 = performance.now();
    const res = solveReverse(state.target, { cap: 8_000_000 });
    const t1 = performance.now();
    const ms = t1 - t0;

    $("st-space").textContent = formatSpace(n);
    $("st-nodes").textContent = res.nodes.toLocaleString();
    $("st-time").textContent = ms < 1 ? "<1 ms" : (ms < 1000 ? Math.round(ms) + " ms" : (ms / 1000).toFixed(2) + " s");

    if (res.status === "found") {
      // verify
      const ok = boardsEqual(stepForward(res.pred), state.target);
      state.pred = res.pred;
      state.predValid = true;
      state.stepped = false;
      $("step").disabled = false;
      const live = countLive(res.pred);
      $("pred-sub").textContent = live + " live cell" + (live === 1 ? "" : "s");
      paintGrid($("pred-grid"), res.pred, "pred", null);
      $("status").innerHTML = '<span class="ok">✓ Predecessor found.</span> ' +
        (ok ? 'Verified: it evolves into the target in one step. ' : '<span class="bad">(internal verify mismatch!)</span> ') +
        'Press <span class="hl">Step Forward</span> to watch it run.';
    } else if (res.status === "none") {
      $("status").innerHTML = '<span class="bad">✗ No predecessor exists.</span> ' +
        'This target is a <span class="hl">Garden of Eden</span> state (under the finite, dead-border convention) — it can never be produced by a previous generation.';
    } else {
      $("status").innerHTML = '<span class="bad">Search capped</span> after ' + res.nodes.toLocaleString() +
        ' nodes. Try a smaller grid or a sparser target.';
    }
  }, 20);
}

function doStep() {
  if (!state.predValid) return;
  const nextOfPred = stepForward(state.pred);
  state.predStepResult = nextOfPred;
  state.stepped = true;
  const ok = boardsEqual(nextOfPred, state.target);
  // briefly flash the predecessor as the target it produces
  paintGrid($("target-grid"), nextOfPred, "target", state.target);
  if (ok) {
    $("status").innerHTML = '<span class="ok">✓ Step confirmed.</span> stepForward(predecessor) reproduces the target exactly. ' +
      'Live cells: predecessor <b>' + countLive(state.pred) + '</b> → target <b>' + countLive(state.target) + '</b>.';
  } else {
    $("status").innerHTML = '<span class="bad">Mismatch</span> — cells outlined in red differ from the painted target.';
  }
  // restore display of the painted target after a beat (keep mismatch outlines briefly)
  setTimeout(() => {
    state.stepped = false;
    paintGrid($("target-grid"), state.target, "target", null);
  }, 1400);
}

function doClear() {
  state.target = makeBoard(state.N);
  invalidatePred();
  renderAll();
  $("status").innerHTML = "Cleared. Paint a target board, then press <span class='hl'>Find Predecessor</span>.";
}

function doRandom() {
  const n = state.N;
  state.target = makeBoard(n);
  for (let r = 0; r < n; r++)
    for (let c = 0; c < n; c++)
      state.target[r][c] = Math.random() < 0.32 ? 1 : 0;
  invalidatePred();
  renderAll();
  $("status").innerHTML = "Random target loaded. Press <span class='hl'>Find Predecessor</span>.";
}

function countLive(board) {
  let k = 0;
  for (let r = 0; r < board.length; r++)
    for (let c = 0; c < board.length; c++) k += board[r][c];
  return k;
}
function formatSpace(n) {
  // 2^(n*n) candidate boards
  const bits = n * n;
  if (bits <= 30) return (Math.pow(2, bits)).toLocaleString();
  return "2^" + bits;
}

/* ============================== PRESETS ============================ */
/* Patterns are placed centered. Each is a list of [r,c] live offsets. */
const PRESETS = [
  { name: "Block", cells: [[0,0],[0,1],[1,0],[1,1]] },
  { name: "Blinker", cells: [[0,0],[0,1],[0,2]] },
  { name: "Glider", cells: [[0,1],[1,2],[2,0],[2,1],[2,2]] },
  { name: "Beehive", cells: [[0,1],[0,2],[1,0],[1,3],[2,1],[2,2]] },
  { name: "Toad", cells: [[0,1],[0,2],[0,3],[1,0],[1,1],[1,2]] },
  { name: "Tub", cells: [[0,1],[1,0],[1,2],[2,1]] },
];
function loadPreset(p) {
  const n = state.N;
  state.target = makeBoard(n);
  let maxr = 0, maxc = 0;
  p.cells.forEach(([r, c]) => { maxr = Math.max(maxr, r); maxc = Math.max(maxc, c); });
  const offR = Math.floor((n - 1 - maxr) / 2);
  const offC = Math.floor((n - 1 - maxc) / 2);
  p.cells.forEach(([r, c]) => {
    const rr = r + offR, cc = c + offC;
    if (rr >= 0 && rr < n && cc >= 0 && cc < n) state.target[rr][cc] = 1;
  });
  invalidatePred();
  renderAll();
  $("status").innerHTML = "Loaded <b>" + p.name + "</b> as target. Press <span class='hl'>Find Predecessor</span>.";
}
function buildPresets() {
  const box = $("presets");
  box.innerHTML = "";
  PRESETS.forEach(p => {
    const b = document.createElement("button");
    b.className = "preset";
    b.textContent = p.name;
    b.addEventListener("click", () => loadPreset(p));
    box.appendChild(b);
  });
}

/* ============================== SIZE =============================== */
function setSize(n) {
  state.N = n;
  $("size-val").textContent = n + " × " + n;
  state.target = makeBoard(n);
  state.pred = null; state.predValid = false; state.stepped = false;
  $("step").disabled = true;
  buildGrid($("target-grid"), n);
  buildGrid($("pred-grid"), n);
  renderAll();
  $("st-space").textContent = "—"; $("st-nodes").textContent = "—"; $("st-time").textContent = "—";
}

/* ============================== THEME ============================== */
function applyTheme(val) {
  document.documentElement.setAttribute("data-theme", val);
  document.querySelectorAll("#theme-toggle button").forEach(b =>
    b.classList.toggle("active", b.dataset.themeVal === val));
  try { localStorage.setItem("rl-theme", val); } catch (e) {}
}

/* ============================== WIRING ============================= */
function bindControls() {
  $("size").addEventListener("input", e => {
    setSize(+e.target.value);
    $("status").innerHTML = "Grid resized to " + state.N + "×" + state.N + ". Paint a target, then <span class='hl'>Find Predecessor</span>.";
  });
  $("solve").addEventListener("click", doSolve);
  $("step").addEventListener("click", doStep);
  $("clear").addEventListener("click", doClear);
  $("random").addEventListener("click", doRandom);
  $("theme-toggle").addEventListener("click", e => {
    const b = e.target.closest("button");
    if (b) applyTheme(b.dataset.themeVal);
  });
}

/* ============================== INIT ============================== */
let savedTheme = "dark";
try { savedTheme = localStorage.getItem("rl-theme") || "dark"; } catch (e) {}

buildPresets();
bindControls();
applyTheme(savedTheme);
setSize(7);
setupPainting();
// seed with a glider so the page is alive on load
loadPreset(PRESETS[2]);
