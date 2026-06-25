# The Playground — Build Session, June 22 2026

Everything you brainstormed, built locally overnight. **Nothing committed, nothing posted** —
per your instruction. Open `index.html` in this folder to browse it all in your design language.

## How to review
- **Web demos** — just open the `index.html` inside each folder in a browser. No server, no build.
  (WebGPU demo needs Chrome/Edge 113+.)
- **Python projects** — `cd` into the folder and run `python3 demo.py` (and `python3 tests.py`).
  All stdlib-only; nothing to install.

## What got built
| № | Project | Type | Entry |
|---|---------|------|-------|
| 00 | **The Playground** (this index) | web | `index.html` |
| 01 | DP, Played Out (LeetCode series — themed) | web | `01-leetcode-series/index.html` |
| 02 | Mini DB Engine | python | `02-mini-db/demo.py` |
| 03 | Distributed Cache | python | `03-distributed-cache/demo.py` |
| 04 | Concurrency Playground | web | `04-concurrency/index.html` |
| 05 | SQL Optimizer Visualizer | web | `05-sql-optimizer/index.html` |
| 07 | Curves Under the Pixels (Bézier / vectorize / trace) | web | `07-bezier-vectorize/index.html` |
| 09 | How GPUs Run a Neural Net | web | `09-gpu-explainer/index.html` |
| 10 | WebGPU Playground | web | `10-webgpu-wasm/index.html` |
| 13 | 3D Convolutions, Visualized | web | `13-conv3d/index.html` |
| 14 | Reverse Game of Life | web | `14-reverse-life/index.html` |
| 15 | Julia Generics & Dispatch | notes | `15-julia-generics/NOTES.md` |
| 16 | Continued Fractions & Padé | web | `16-continued-fractions/index.html` |
| 22 | Referral Outreach Assistant | n8n | `22-linkedin-referral/README.md` |
| 28 | Bin-Packing: Heuristics vs a Net | python | `28-binpack-nn/demo.py` |

## Mapping to your brainstorm list
- Built as **single interactive pages** where that's the truest form: 01, 04, 05, 07, 09, 10, 13, 14, 16.
- Built as **full runnable projects**: 02 (mini DB), 03 (distributed cache), 28 (bin-packing NN).
- Built as **tool / notes**: 22 (n8n referral workflow), 15 (Julia generics).
- **Deferred** (your call, lower priority for the brand): 01-Arduino-GPT (different lane — hardware),
  17/18 LeetCode-WASM-LLD (folded into the DP series 01 for now; WASM needs emscripten installed).

## Caveats / honest notes
- This is an **Adobe machine** — these are built here for review only. Copy `~/Desktop/Builds/`
  to your personal machine before you hand the laptop back.
- WASM-specific items couldn't be compiled here (emscripten not installed); the WebGPU demo uses
  the browser GPU API directly, which is the more useful version anyway.
- Design language matches your Optimal Trader page (Space Grotesk / IBM Plex, gold accent,
  dark-default + light/system toggle) so the whole set reads as one body of work.
- Next step when you're ready: pick the 3–4 strongest, drop them under your portfolio site's
  Craft section, one post each. Don't ship all 14 at once — sequence them.

— built overnight, ready for your morning pass.
