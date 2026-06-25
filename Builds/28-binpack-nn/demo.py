"""Demo: train the tiny policy net and compare it against classic heuristics.

Run:  python3 demo.py
"""
import random
import time

import heuristics as H
import nn


CAPACITY = 1.0
ITEM_RANGE = (0.1, 0.7)


def gen_instance(rng, n):
    return [rng.uniform(*ITEM_RANGE) for _ in range(n)]


def evaluate(method_fn, instances):
    """Return (avg_bins, avg_fill) over a list of instances."""
    total_bins = 0
    total_fill = 0.0
    for items in instances:
        bins = method_fn(items)
        total_bins += H.num_bins(bins)
        total_fill += H.fill_ratio(bins, CAPACITY)
    n = len(instances)
    return total_bins / n, total_fill / n


def main():
    print("=" * 64)
    print(" 1D BIN-PACKING:  tiny neural policy  vs.  classic heuristics")
    print("=" * 64)
    print(f" numpy available: {nn.HAVE_NUMPY}  "
          f"(net runs in pure Python either way)")
    print(f" bin capacity = {CAPACITY},  item sizes ~ U{ITEM_RANGE}")

    # ---- train the policy by imitating Best-Fit on random instances -------
    print("\n[1] Training policy net (behavioural cloning of Best-Fit)...")
    t0 = time.time()
    train_set = nn.make_dataset(num_instances=300, items_per=25,
                                capacity=CAPACITY, seed=1, item_range=ITEM_RANGE)
    net = nn.PolicyNet(in_dim=4, hidden=8, seed=7)
    nn.train(net, train_set, epochs=6, lr=0.3, batch=64, seed=3)
    print(f"    trained on {len(train_set)} decisions "
          f"in {time.time() - t0:.2f}s")

    # ---- build a fresh held-out test set ----------------------------------
    rng = random.Random(999)
    n_test = 200
    items_per = 30
    instances = [gen_instance(rng, items_per) for _ in range(n_test)]

    methods = [
        ("First-Fit",            lambda it: H.first_fit(it, CAPACITY)),
        ("Best-Fit",             lambda it: H.best_fit(it, CAPACITY)),
        ("First-Fit-Decreasing", lambda it: H.first_fit_decreasing(it, CAPACITY)),
        ("Best-Fit-Decreasing",  lambda it: H.best_fit_decreasing(it, CAPACITY)),
        ("Neural policy (ours)", lambda it: nn.pack_with_policy(net, it, CAPACITY)),
    ]

    # average L1 lower bound on OPT for reference
    avg_lb = sum(H.lower_bound(it, CAPACITY) for it in instances) / n_test

    print(f"\n[2] Evaluating on {n_test} fresh instances of "
          f"{items_per} items each.")
    print(f"    L1 lower bound on OPT (avg): {avg_lb:.2f} bins\n")

    header = f"{'method':<24}{'avg bins':>12}{'avg fill %':>14}{'vs FFD':>10}"
    print(header)
    print("-" * len(header))

    ffd_bins, _ = evaluate(lambda it: H.first_fit_decreasing(it, CAPACITY),
                           instances)
    for name, fn in methods:
        bins, fill = evaluate(fn, instances)
        delta = bins - ffd_bins
        vs = "  (ref)" if name == "First-Fit-Decreasing" else f"{delta:+.3f}"
        print(f"{name:<24}{bins:>12.3f}{fill * 100:>13.2f}%{vs:>10}")

    print("\nLower 'avg bins' is better; higher 'avg fill %' is better.")
    print("'vs FFD' = difference in avg bins relative to First-Fit-Decreasing.")


if __name__ == "__main__":
    main()
