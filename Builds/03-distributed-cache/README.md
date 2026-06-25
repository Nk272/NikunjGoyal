# Distributed Cache (stdlib-only, Python)

A working distributed key/value cache built with **only the Python standard
library** (`threading`, `http.server`, `socketserver`, `urllib`, `hashlib`).
It demonstrates the core building blocks of systems like Amazon Dynamo,
Cassandra, and Riak:

- **Consistent hashing** with **virtual nodes** for key placement
- **In-memory LRU cache nodes** with **TTL expiry**, served over HTTP
- A **coordinator/client** that enforces a **replication factor N** and
  tunable **read/write quorums (R / W)**
- Live demonstration of **node failure tolerance** and **minimal key remap**
  on cluster membership changes

No external dependencies. Tested on Python 3.9.

---

## Files

| File         | Purpose |
|--------------|---------|
| `ring.py`    | `ConsistentHashRing` — virtual-node hash ring; key → node(s) |
| `node.py`    | `LRUCache` (LRU + TTL) and `CacheNode` HTTP server |
| `client.py`  | `CacheClient` — routes via the ring, enforces N/R/W quorums |
| `cluster.py` | `Cluster` — starts N nodes in background threads on localhost |
| `demo.py`    | End-to-end demo: put/get, node kill, node add + remap measure |
| `tests.py`   | 14 unit + integration tests |
| `README.md`  | This document |

## Run it

```bash
python3 tests.py     # unit + integration tests
python3 demo.py      # full end-to-end demonstration
```

You can also run a single node or a standalone cluster:

```bash
python3 node.py node-0 9000        # one node on port 9000
python3 cluster.py                  # 4 nodes on random free ports
```

---

## 1. Consistent hashing

Naive sharding (`node = hash(key) % num_nodes`) is a disaster when the cluster
size changes: adding or removing one node changes the modulus, so **almost
every key remaps** (~`1 - 1/num_nodes` of them). For a 5→6 node change that's
~83% of keys moving — a cache-destroying stampede.

**Consistent hashing** instead maps both nodes and keys onto a fixed circular
hash space `[0, 2^32)`:

1. Each node is hashed to one or more points on the ring.
2. Each key is hashed to a point on the ring.
3. The key is owned by the **first node found walking clockwise** from the
   key's position (wrapping around at the top).

When a node is added, it only steals the arc between itself and its
counter-clockwise neighbor — so only the keys in that arc move. On average a
membership change of a single node remaps just **~1/(num_nodes+1)** of keys.

> **Measured in this project:** adding a 6th node to a 5-node cluster remapped
> **16.9%** of primary key ownership — essentially the theoretical ideal of
> `1/6 = 16.7%`, versus ~83% for naive modulo hashing.

## 2. Virtual nodes

If each physical node occupied a single point on the ring, the arcs would be
wildly uneven (random points are not evenly spaced), and removing a node would
dump its entire load onto a single neighbor.

**Virtual nodes** fix this: each physical node is hashed to many points
(`vnodes=150` by default) as `node#0, node#1, …, node#149`. Now each physical
node owns many small arcs spread around the ring. Benefits:

- **Even load** — the law of large numbers smooths the distribution.
- **Even rebalancing** — when a node leaves, its many small arcs are absorbed
  by *many* different neighbors rather than one.
- **Heterogeneity** — a more powerful node can be given more vnodes.

`tests.py` asserts that with 200 vnodes across 5 nodes, no node owns more than
1.8× its fair share over 10,000 keys.

## 3. Replication (factor N)

For fault tolerance, each key is stored on **N nodes**, not one. The
**preference list** for a key is the first **N distinct physical nodes**
encountered walking clockwise from the key's hash. `ring.get_nodes(key, N)`
skips repeated physical nodes (multiple vnodes of the same node) so the N
replicas are always distinct machines.

A write (`PUT`) is sent to all N replicas; a read (`GET`) consults the same
preference list. If one replica is down, the data still lives on N−1 others.

## 4. Quorums (R / W) and why R + W > N

Contacting every replica on every operation is slow and brittle. Instead we
require only a **quorum**:

- A **write** succeeds when **W** of the N replicas acknowledge it.
- A **read** succeeds when **R** of the N replicas respond.

Each stored value carries a write timestamp (`time_ns()`); a read returns the
value with the newest timestamp among the responders (last-writer-wins
reconciliation).

The key invariant is:

```
R + W > N
```

If the read quorum and the write quorum together exceed N, then **any read
quorum must overlap any write quorum on at least one node** (pigeonhole). That
overlapping node has the latest committed write, so a successful read is
guaranteed to observe it. This gives strong read-your-writes consistency
*without* talking to every replica.

This project's demo uses **N=3, R=2, W=2** → `R+W = 4 > 3`. Tradeoffs:

| Setting           | Property |
|-------------------|----------|
| `W=N, R=1`        | Fast reads, slow/durable writes |
| `W=1, R=N`        | Fast writes, slow consistent reads |
| `R+W>N`           | Guaranteed quorum overlap (consistency) |
| `R+W<=N`          | Possible stale reads (eventual consistency) |

With N=3/R=2/W=2 the cluster tolerates the loss of **one** replica for any
given key while still satisfying both read and write quorums — exactly what
the demo shows when it kills a node and 1000/1000 reads still succeed.

---

## Node HTTP API

Each `CacheNode` speaks JSON over HTTP:

| Method   | Path          | Body                              | Response |
|----------|---------------|-----------------------------------|----------|
| `GET`    | `/kv/<key>`   | —                                 | `200 {value}` / `404` |
| `PUT`    | `/kv/<key>`   | `{"value": ..., "ttl": <secs>}`   | `200 {ok}` |
| `DELETE` | `/kv/<key>`   | —                                 | `200 {ok}` |
| `GET`    | `/stats`      | —                                 | `200 {node,size,keys}` |
| `GET`    | `/health`     | —                                 | `200 {ok}` |

The coordinator wraps stored values as `{"v": <user value>, "ts": <ns>}` to
support quorum reconciliation; this is transparent to API callers using
`CacheClient`.

---

## Design notes & limitations

- **In-process cluster.** `cluster.py` runs all nodes as threads in one
  process for easy demoing; the nodes are nonetheless *real* HTTP servers
  reachable on localhost ports, and the client talks to them over TCP.
- **Lazy + sweep TTL.** Expired keys are removed on access and best-effort
  swept on each write. No background reaper thread (kept simple).
- **Last-writer-wins.** Conflicts are resolved by nanosecond timestamp, not
  vector clocks — adequate for a cache, not for a source-of-truth store.
- **No hinted handoff / read repair.** A production Dynamo-style system would
  re-replicate on recovery; here the demo manually re-replicates moved keys
  after adding a node to illustrate the migration step.
