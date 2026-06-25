"""A tiny from-scratch neural network that learns a bin-packing *placement
policy*, trained by imitation of a Best-Fit teacher.

Design
------
We treat packing as a sequential decision process. Items arrive one at a time
(in decreasing order, like FFD). For the current item we enumerate candidate
ACTIONS:

    * place it into open bin i  (one action per bin that still fits), or
    * open a brand-new bin.

Each action is described by a small feature vector. A shared MLP scores every
candidate action; a softmax over those scores gives a probability per action.
At decision time we pick the highest-scoring feasible action.

Teacher / labels
----------------
The supervision signal is the Best-Fit rule: among feasible open bins, choose
the one leaving the least slack; otherwise open a new bin. The network is
trained with cross-entropy to imitate that choice across thousands of states
sampled from random instances. (This is behavioural cloning -- a simple,
stable stand-in for full policy-gradient that still "learns a policy" and
trains in well under a second.)

Backend
-------
Pure-Python lists with hand-written backprop. We probe for numpy and report
whether it is present, but the math below deliberately uses no third-party
deps so it runs anywhere.
"""
import math
import random

try:
    import numpy as _np  # noqa: F401
    HAVE_NUMPY = True
except Exception:
    HAVE_NUMPY = False


# ---------------------------------------------------------------------------
# Feature engineering: describe one candidate action for the current item.
# ---------------------------------------------------------------------------
def action_features(item, bin_load, capacity, is_new_bin):
    """4-dim feature vector for placing `item` into a bin with `bin_load`."""
    remaining = capacity - bin_load
    slack_after = remaining - item            # >= 0 for feasible actions
    return [
        item / capacity,                      # how big is the item
        remaining / capacity,                 # how much room this bin has
        slack_after / capacity,               # waste left if we place here
        1.0 if is_new_bin else 0.0,           # opening a fresh bin?
    ]


# ---------------------------------------------------------------------------
# Tiny MLP: input(4) -> tanh hidden(H) -> linear scalar score.
# ---------------------------------------------------------------------------
class PolicyNet:
    def __init__(self, in_dim=4, hidden=8, seed=0):
        rng = random.Random(seed)
        self.in_dim = in_dim
        self.hidden = hidden

        def rand(scale):
            return rng.uniform(-scale, scale)

        s1 = math.sqrt(1.0 / in_dim)
        s2 = math.sqrt(1.0 / hidden)
        self.W1 = [[rand(s1) for _ in range(in_dim)] for _ in range(hidden)]
        self.b1 = [0.0 for _ in range(hidden)]
        self.W2 = [rand(s2) for _ in range(hidden)]
        self.b2 = 0.0

    def score(self, feats):
        """Forward pass for one feature vector -> (score, cache)."""
        z = [0.0] * self.hidden
        for j in range(self.hidden):
            acc = self.b1[j]
            wj = self.W1[j]
            for k in range(self.in_dim):
                acc += wj[k] * feats[k]
            z[j] = acc
        h = [math.tanh(v) for v in z]
        s = self.b2
        for j in range(self.hidden):
            s += self.W2[j] * h[j]
        return s, (feats, h)

    def backward_accumulate(self, cache, dscore, grads):
        """Backprop dLoss/dscore into accumulated `grads` for one action."""
        feats, h = cache
        gW1, gb1, gW2, gb2 = grads
        gb2[0] += dscore
        for j in range(self.hidden):
            gW2[j] += dscore * h[j]
            dh = dscore * self.W2[j]
            dz = dh * (1.0 - h[j] * h[j])      # tanh'
            gb1[j] += dz
            wj = gW1[j]
            for k in range(self.in_dim):
                wj[k] += dz * feats[k]

    def new_grads(self):
        gW1 = [[0.0] * self.in_dim for _ in range(self.hidden)]
        gb1 = [0.0] * self.hidden
        gW2 = [0.0] * self.hidden
        gb2 = [0.0]
        return gW1, gb1, gW2, gb2

    def apply_grads(self, grads, lr):
        gW1, gb1, gW2, gb2 = grads
        for j in range(self.hidden):
            wj, gwj = self.W1[j], gW1[j]
            for k in range(self.in_dim):
                wj[k] -= lr * gwj[k]
            self.b1[j] -= lr * gb1[j]
            self.W2[j] -= lr * gW2[j]
        self.b2 -= lr * gb2[0]


def _softmax(scores):
    m = max(scores)
    exps = [math.exp(s - m) for s in scores]
    z = sum(exps)
    return [e / z for e in exps]


# ---------------------------------------------------------------------------
# Build (state -> candidate actions, teacher label) training examples.
# ---------------------------------------------------------------------------
def _candidates(item, loads, capacity):
    """Return (feature_list, action_meta) for the current item.

    action_meta[j] = bin index to place in, or -1 to open a new bin.
    """
    feats = []
    meta = []
    for i, load in enumerate(loads):
        if load + item <= capacity + 1e-9:
            feats.append(action_features(item, load, capacity, False))
            meta.append(i)
    # always allow opening a new bin
    feats.append(action_features(item, 0.0, capacity, True))
    meta.append(-1)
    return feats, meta


def _best_fit_label(item, loads, capacity, meta):
    """Index (into meta) of the Best-Fit teacher's chosen action."""
    best_j, best_slack = None, None
    for j, b in enumerate(meta):
        if b == -1:
            continue
        slack = capacity - loads[b] - item
        if best_slack is None or slack < best_slack:
            best_slack, best_j = slack, j
    if best_j is None:                         # nothing fits -> open new bin
        return meta.index(-1)
    return best_j


def make_dataset(num_instances, items_per, capacity, seed, item_range=(0.1, 0.7)):
    """Roll out the Best-Fit teacher on random instances, recording every
    (candidate features, chosen action) decision."""
    rng = random.Random(seed)
    examples = []
    for _ in range(num_instances):
        items = [rng.uniform(*item_range) for _ in range(items_per)]
        items.sort(reverse=True)               # decreasing order, FFD-style
        loads = []
        for item in items:
            feats, meta = _candidates(item, loads, capacity)
            label = _best_fit_label(item, loads, capacity, meta)
            examples.append((feats, label))
            # follow the teacher to generate the next state
            choice = meta[label]
            if choice == -1:
                loads.append(item)
            else:
                loads[choice] += item
    return examples


def train(net, examples, epochs=6, lr=0.2, batch=64, seed=0, verbose=True):
    rng = random.Random(seed)
    for ep in range(epochs):
        rng.shuffle(examples)
        total_loss, correct, n = 0.0, 0, 0
        for start in range(0, len(examples), batch):
            chunk = examples[start:start + batch]
            grads = net.new_grads()
            for feats, label in chunk:
                caches, scores = [], []
                for f in feats:
                    s, c = net.score(f)
                    scores.append(s)
                    caches.append(c)
                probs = _softmax(scores)
                total_loss += -math.log(max(probs[label], 1e-12))
                if max(range(len(probs)), key=lambda j: probs[j]) == label:
                    correct += 1
                n += 1
                # dLoss/dscore_j = prob_j - 1[j == label]
                for j, c in enumerate(caches):
                    dscore = probs[j] - (1.0 if j == label else 0.0)
                    net.backward_accumulate(c, dscore / len(chunk), grads)
            net.apply_grads(grads, lr)
        if verbose:
            print(f"  epoch {ep + 1}/{epochs}  "
                  f"loss={total_loss / n:.4f}  imitation_acc={correct / n:.3f}")
    return net


# ---------------------------------------------------------------------------
# Use the trained policy to actually pack an instance (greedy argmax).
# ---------------------------------------------------------------------------
def pack_with_policy(net, items, capacity, decreasing=True):
    order = sorted(items, reverse=True) if decreasing else list(items)
    bins = []
    loads = []
    for item in order:
        feats, meta = _candidates(item, loads, capacity)
        scores = [net.score(f)[0] for f in feats]
        j = max(range(len(scores)), key=lambda k: scores[k])
        choice = meta[j]
        if choice == -1:
            bins.append([item])
            loads.append(item)
        else:
            bins[choice].append(item)
            loads[choice] += item
    return bins
