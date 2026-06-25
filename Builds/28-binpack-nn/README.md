# Bin-Packing: a tiny neural policy vs. classic heuristics

A small, dependency-free Python project that pits a **from-scratch neural
network** against the textbook 1D bin-packing heuristics (First-Fit, Best-Fit,
First-Fit-Decreasing). Everything is pure Python — `numpy` is detected if
present but is **not required**; the net trains in ~1.5 seconds either way.

```
python3 demo.py
```

## The problem & why it's hard

**1D bin-packing.** Given a list of item sizes `s_1 … s_n` (each ≤ the bin
capacity `C`), pack them into as few bins of capacity `C` as possible without
overfilling any bin.

The *decision* version — "can these items fit into `k` bins?" — is
**NP-complete** (it contains PARTITION as a special case with two bins). The
*optimization* version is therefore **NP-hard**: there is no known
polynomial-time algorithm that always finds the minimum number of bins, and
finding one would prove P = NP. Worse, unless P = NP no polynomial algorithm
can guarantee a solution within a factor better than 3/2 of optimal in the
worst case. So in practice we use fast **constructive heuristics** that come
with provable approximation ratios.

## The heuristics (`heuristics.py`)

| Heuristic | Rule | Worst-case guarantee |
|-----------|------|----------------------|
| **First-Fit (FF)** | Put each item in the *first* bin it fits in; open a new bin if none fit. | ≤ ⌈1.7·OPT⌉ bins |
| **Best-Fit (BF)** | Put each item in the bin that leaves the *least* leftover slack. | ≈ 1.7·OPT asymptotically |
| **First-Fit-Decreasing (FFD)** | Sort items largest-first, then run First-Fit. | ≤ (11/9)·OPT + 6/9 |
| **Best-Fit-Decreasing (BFD)** | Sort largest-first, then Best-Fit. | same (11/9) class |

Sorting items in *decreasing* order is the big win: it places the awkward
large items first and lets the small ones fill the gaps, which is why FFD/BFD
dominate the online (unsorted) variants.

A trivial **lower bound** on OPT is `L1 = ⌈(Σ sizes) / C⌉` — you can never use
fewer bins than the total volume requires. `demo.py` prints it for reference.

## The learning setup (`nn.py`)

We frame packing as a **sequential decision process** and learn a *placement
policy*:

1. Items arrive largest-first (FFD-style ordering).
2. For the current item we enumerate **candidate actions**: place it into any
   open bin that still fits, or open a brand-new bin.
3. Each action gets a 4-feature descriptor:
   `[item/C, remaining_room/C, slack_after_placing/C, is_new_bin]`.
4. A shared **MLP** `4 → tanh(8) → 1` scores every candidate; a softmax over
   the scores turns them into a probability distribution over actions. At
   inference we take the argmax feasible action.

**Training = behavioural cloning.** We roll out a **Best-Fit teacher** on 300
random instances, recording every (candidate-features, chosen-action) pair —
~7,500 decisions. The net is trained with cross-entropy to imitate the
teacher's choice. This is the stable, fast cousin of policy-gradient: it
"learns a policy" but with a dense supervised signal, so it converges to
~100% imitation accuracy in a handful of epochs and a couple of seconds.

The backprop (forward pass, tanh derivative, softmax-cross-entropy gradient,
SGD update) is all hand-written in `nn.py` — no autograd, no numpy needed.

## What you should see

The learned policy reproduces the Best-Fit-Decreasing strategy and therefore
**matches FFD/BFD** on held-out instances while clearly beating the online
First-Fit / Best-Fit heuristics. Representative run (200 fresh instances of 30
items, capacity 1.0, sizes ~ U(0.1, 0.7)):

```
method                      avg bins    avg fill %    vs FFD
------------------------------------------------------------
First-Fit                     13.635        87.29%    +0.905
Best-Fit                      13.515        88.06%    +0.785
First-Fit-Decreasing          12.730        93.30%     (ref)
Best-Fit-Decreasing           12.730        93.30%    +0.000
Neural policy (ours)          12.730        93.30%    +0.000
```

(L1 lower bound on OPT for those instances: ~12.39 bins, so FFD and the learned
policy are within ~0.34 bins of the theoretical floor.)

## Files

- `heuristics.py` — FF, BF, FFD, BFD, plus `fill_ratio` / `lower_bound` helpers.
- `nn.py` — tiny pure-Python MLP, feature engineering, Best-Fit teacher,
  dataset builder, training loop, and `pack_with_policy`.
- `demo.py` — generates instances, trains the net, prints the comparison table.

## Notes & extensions

- The policy currently *clones* Best-Fit, so it can't beat the teacher — it
  can only match it. To genuinely *surpass* FFD you'd switch the training
  signal from imitation to **reinforcement** (reward = −bins used) and let
  policy-gradient explore non-greedy placements. The action/feature scaffolding
  here is already set up for that.
- Increasing item sizes toward the capacity, or correlating sizes, widens the
  gap between online and decreasing heuristics.
