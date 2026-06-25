"""
demo.py -- End-to-end demonstration of the distributed cache.

Scenario:
  1. Start a 5-node cluster.
  2. PUT/GET a batch of keys with N=3, R=2, W=2 (so R+W>N => overlapping
     quorums => reads see the latest write).
  3. Kill a node and show reads still succeed via surviving replicas.
  4. Add a new node and measure the fraction of keys whose owning replica set
     changed -- demonstrating that consistent hashing remaps only a small
     fraction of keys.
"""

import time

from client import CacheClient
from cluster import Cluster

N, R, W = 3, 2, 2
NUM_KEYS = 1000


def banner(title):
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def main():
    banner("1) START 5-NODE CLUSTER")
    cluster = Cluster().start(5)
    addrs = cluster.addresses()
    for nid, a in addrs.items():
        print(f"   {nid:8s} -> {a}")
    client = CacheClient(addrs, n=N, r=R, w=W)
    print(f"\n   Replication N={N}, read quorum R={R}, write quorum W={W} "
          f"(R+W={R+W} > N={N} => quorum overlap)")

    banner("2) PUT / GET KEYS")
    keys = [f"user:{i}" for i in range(NUM_KEYS)]
    for k in keys:
        client.put(k, {"name": k, "score": hash(k) % 100})
    # verify a sample
    ok = 0
    for k in keys:
        res = client.get(k)
        if res["ok"] and res["value"] and res["value"]["name"] == k:
            ok += 1
    print(f"   Wrote {NUM_KEYS} keys, read back {ok}/{NUM_KEYS} correctly.")

    # show a sample preference list
    sample = keys[0]
    print(f"   Preference list for '{sample}': {client.replicas_for(sample)}")

    banner("3) KILL A NODE -> READS STILL SUCCEED VIA REPLICAS")
    victim = "node-2"
    print(f"   Killing {victim} ...")
    cluster.kill(victim)
    # NOTE: we keep the ring unchanged so the client still routes to the
    # (now dead) replica, proving that a read quorum of R survivors works.
    time.sleep(0.2)
    survived = 0
    degraded = 0
    for k in keys:
        res = client.get(k)
        if res["ok"]:
            survived += 1
            if res["errors"]:
                degraded += 1
    print(f"   Reads succeeding after node loss: {survived}/{NUM_KEYS}")
    print(f"   (of those, {degraded} had a failed replica but still met R={R})")

    banner("4) ADD A NODE -> MEASURE KEY REMAP FRACTION")
    # Snapshot ownership BEFORE adding the node (use full live cluster view).
    # Rebuild a fresh client representing the healthy 5-node ring for a clean
    # before/after comparison of consistent-hashing remap.
    before_addrs = dict(addrs)  # original 5 nodes
    before_client = CacheClient(before_addrs, n=N, r=R, w=W)
    before = {k: tuple(before_client.replicas_for(k)) for k in keys}

    after_addrs = dict(before_addrs)
    after_addrs["node-5"] = "127.0.0.1:0"  # placement only; ring math is local
    after_client = CacheClient(after_addrs, n=N, r=R, w=W)
    after = {k: tuple(after_client.replicas_for(k)) for k in keys}

    moved = sum(1 for k in keys if before[k] != after[k])
    pct = 100.0 * moved / len(keys)
    ideal = 100.0 / (len(before_addrs) + 1)  # ~1/(nodes+1) for primary owner

    # Primary-owner remap (the classic consistent-hashing metric): only the
    # single owning node, not the full N-replica set.
    before_owner = {k: before[k][0] for k in keys}
    after_owner = {k: after[k][0] for k in keys}
    moved_owner = sum(1 for k in keys if before_owner[k] != after_owner[k])
    pct_owner = 100.0 * moved_owner / len(keys)

    print(f"   Nodes before: {len(before_addrs)}, after: {len(after_addrs)}")
    print(f"   PRIMARY-owner remap: {moved_owner}/{len(keys)} = {pct_owner:.1f}% "
          f"(ideal ~1/(n+1) = {ideal:.1f}%)")
    print(f"   Full N={N}-replica-set remap: {moved}/{len(keys)} = {pct:.1f}%")
    print(f"   (Naive hashing (key % nodes) would remap ~"
          f"{100.0*(1-1/len(after_addrs)):.0f}% of keys.)")
    print(f"   Consistent hashing keeps remap small and bounded.")

    # Also start the real node-5 server and migrate the moved keys to show
    # the system continues to function with the new member.
    new_node = cluster.start_node("node-5")
    client.add_node("node-5", new_node.address)
    re_put = 0
    for k in keys:
        if before[k] != tuple(client.replicas_for(k)):
            res = client.get(k)
            if res["value"]:
                client.put(k, res["value"])
                re_put += 1
    print(f"   Live cluster now has {len(client.addresses)} nodes; "
          f"re-replicated {re_put} moved keys onto node-5.")

    banner("SUMMARY")
    print(f"   Primary-owner remap on node addition: {pct_owner:.1f}% "
          f"(vs ~83% for naive key%%N hashing)")
    print(f"   Full {N}-replica-set remap: {pct:.1f}% "
          f"(measured over {NUM_KEYS} keys)")
    cluster.stop_all()
    print("   Cluster stopped. Demo complete.")


if __name__ == "__main__":
    main()
