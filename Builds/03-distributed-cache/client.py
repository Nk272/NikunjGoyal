"""
client.py -- Coordinator/client that routes keys via the consistent-hash
ring and enforces a replication factor N with read/write quorums R and W.

Quorum intuition:
  * Every key has a preference list of N nodes (the first N distinct nodes
    clockwise on the ring).
  * A write must be acked by at least W of those N replicas to succeed.
  * A read must collect responses from at least R replicas; we return the
    value with the freshest write (we tag each value with a logical/clock
    timestamp on PUT).
  * If R + W > N, the read and write quorums are guaranteed to overlap on at
    least one node, so a read quorum always sees the most recent committed
    write -> strong-ish consistency without contacting every replica.

This client maps logical node ids -> HTTP addresses and speaks the node API.
"""

import json
import time
import urllib.error
import urllib.request

from ring import ConsistentHashRing


class CacheClient:
    def __init__(self, addresses: dict, n=3, r=2, w=2, vnodes=150, timeout=2.0):
        """
        :param addresses: {node_id: "host:port"}
        :param n: replication factor
        :param r: read quorum
        :param w: write quorum
        """
        self.addresses = dict(addresses)
        self.n = n
        self.r = r
        self.w = w
        self.timeout = timeout
        self.ring = ConsistentHashRing(vnodes=vnodes)
        for node_id in self.addresses:
            self.ring.add_node(node_id)

    # ---- cluster membership -------------------------------------------------
    def add_node(self, node_id, address):
        self.addresses[node_id] = address
        self.ring.add_node(node_id)

    def remove_node(self, node_id):
        self.addresses.pop(node_id, None)
        self.ring.remove_node(node_id)

    def replicas_for(self, key):
        return self.ring.get_nodes(key, self.n)

    # ---- low-level HTTP -----------------------------------------------------
    def _request(self, node_id, method, path, body=None):
        addr = self.addresses.get(node_id)
        if not addr:
            raise RuntimeError(f"unknown node {node_id}")
        url = f"http://{addr}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")

    # ---- public API ---------------------------------------------------------
    def put(self, key, value, ttl=None):
        """Write to N replicas; succeed if >= W ack. Stamps a write timestamp
        so reads can pick the freshest value."""
        replicas = self.replicas_for(key)
        # monotonic-ish timestamp; nanoseconds avoid collisions within a run
        stamped = {"v": value, "ts": time.time_ns()}
        acks = 0
        errors = []
        for node_id in replicas:
            try:
                status, _ = self._request(
                    node_id, "PUT", f"/kv/{key}",
                    {"value": stamped, "ttl": ttl},
                )
                if status == 200:
                    acks += 1
            except (urllib.error.URLError, OSError) as e:
                errors.append((node_id, str(e)))
        ok = acks >= self.w
        return {"ok": ok, "acks": acks, "w": self.w, "replicas": replicas,
                "errors": errors}

    def get(self, key):
        """Read from up to N replicas; succeed if >= R respond. Returns the
        value carrying the newest write timestamp among responders."""
        replicas = self.replicas_for(key)
        responses = 0
        best = None  # (ts, value)
        errors = []
        for node_id in replicas:
            try:
                status, payload = self._request(node_id, "GET", f"/kv/{key}")
                if status == 200:
                    responses += 1
                    stamped = payload.get("value") or {}
                    ts = stamped.get("ts", -1)
                    if best is None or ts > best[0]:
                        best = (ts, stamped.get("v"))
                elif status == 404:
                    # node is up and authoritatively has no value -> counts
                    responses += 1
            except (urllib.error.URLError, OSError) as e:
                errors.append((node_id, str(e)))
        ok = responses >= self.r
        value = best[1] if best else None
        return {"ok": ok, "value": value, "responses": responses,
                "r": self.r, "replicas": replicas, "errors": errors}

    def delete(self, key):
        replicas = self.replicas_for(key)
        acks = 0
        for node_id in replicas:
            try:
                status, _ = self._request(node_id, "DELETE", f"/kv/{key}")
                if status == 200:
                    acks += 1
            except (urllib.error.URLError, OSError):
                pass
        return {"ok": acks >= self.w, "acks": acks}
