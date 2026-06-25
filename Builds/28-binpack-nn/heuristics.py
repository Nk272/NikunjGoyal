"""Classic 1D bin-packing heuristics, pure Python.

A "bin" has a fixed capacity. We pack a list of item sizes (each <= capacity)
into as few bins as possible. The decision version of bin-packing is NP-complete
and the optimization version is NP-hard, so in practice we lean on fast
constructive heuristics with known approximation guarantees.
"""
from typing import List, Tuple


def first_fit(items: List[float], capacity: float = 1.0) -> List[List[float]]:
    """First-Fit: place each item into the first bin that can hold it.

    Guarantee: uses at most ceil(1.7 * OPT) bins.
    """
    bins: List[List[float]] = []
    loads: List[float] = []
    for x in items:
        placed = False
        for i in range(len(bins)):
            if loads[i] + x <= capacity + 1e-9:
                bins[i].append(x)
                loads[i] += x
                placed = True
                break
        if not placed:
            bins.append([x])
            loads.append(x)
    return bins


def best_fit(items: List[float], capacity: float = 1.0) -> List[List[float]]:
    """Best-Fit: place each item into the bin that leaves the least slack.

    Same 1.7*OPT asymptotic guarantee as First-Fit, usually a touch tighter
    in practice.
    """
    bins: List[List[float]] = []
    loads: List[float] = []
    for x in items:
        best_i = -1
        best_slack = None
        for i in range(len(bins)):
            slack = capacity - loads[i] - x
            if slack >= -1e-9 and (best_slack is None or slack < best_slack):
                best_slack = slack
                best_i = i
        if best_i == -1:
            bins.append([x])
            loads.append(x)
        else:
            bins[best_i].append(x)
            loads[best_i] += x
    return bins


def first_fit_decreasing(items: List[float], capacity: float = 1.0) -> List[List[float]]:
    """First-Fit-Decreasing: sort items largest-first, then First-Fit.

    The classic workhorse. Guarantee: uses at most (11/9)*OPT + 6/9 bins.
    """
    return first_fit(sorted(items, reverse=True), capacity)


def best_fit_decreasing(items: List[float], capacity: float = 1.0) -> List[List[float]]:
    return best_fit(sorted(items, reverse=True), capacity)


def num_bins(bins: List[List[float]]) -> int:
    return len(bins)


def fill_ratio(bins: List[List[float]], capacity: float = 1.0) -> float:
    """Average fraction of each used bin's capacity that is actually filled."""
    if not bins:
        return 0.0
    return sum(sum(b) for b in bins) / (len(bins) * capacity)


def lower_bound(items: List[float], capacity: float = 1.0) -> int:
    """Trivial L1 lower bound on OPT: ceil(total_size / capacity)."""
    import math
    return int(math.ceil(sum(items) / capacity - 1e-9))
