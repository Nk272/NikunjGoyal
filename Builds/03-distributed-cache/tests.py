"""
tests.py -- unit + integration tests for the distributed cache.
Run with: python3 tests.py
"""

import time
import unittest

from client import CacheClient
from cluster import Cluster
from node import LRUCache
from ring import ConsistentHashRing


class TestRing(unittest.TestCase):
    def test_empty_ring(self):
        r = ConsistentHashRing()
        self.assertIsNone(r.get_node("x"))
        self.assertEqual(r.get_nodes("x", 3), [])

    def test_deterministic_mapping(self):
        r = ConsistentHashRing(vnodes=100)
        for n in ["a", "b", "c"]:
            r.add_node(n)
        self.assertEqual(r.get_node("hello"), r.get_node("hello"))

    def test_preference_list_distinct(self):
        r = ConsistentHashRing(vnodes=100)
        for n in ["a", "b", "c", "d"]:
            r.add_node(n)
        nodes = r.get_nodes("somekey", 3)
        self.assertEqual(len(nodes), 3)
        self.assertEqual(len(set(nodes)), 3)  # distinct physical nodes

    def test_preference_list_capped_to_nodes(self):
        r = ConsistentHashRing(vnodes=50)
        for n in ["a", "b"]:
            r.add_node(n)
        self.assertEqual(len(r.get_nodes("k", 5)), 2)

    def test_distribution_is_balanced(self):
        r = ConsistentHashRing(vnodes=200)
        for n in ["a", "b", "c", "d", "e"]:
            r.add_node(n)
        counts = {n: 0 for n in r.nodes}
        for i in range(10000):
            counts[r.get_node(f"key{i}")] += 1
        # no node should own more than ~2x its fair share with 200 vnodes
        fair = 10000 / 5
        for n, c in counts.items():
            self.assertLess(c, fair * 1.8, f"{n} too hot: {c}")

    def test_remap_fraction_small(self):
        keys = [f"k{i}" for i in range(2000)]
        r = ConsistentHashRing(vnodes=200)
        for n in [f"n{i}" for i in range(5)]:
            r.add_node(n)
        before = {k: r.get_node(k) for k in keys}
        r.add_node("n5")
        after = {k: r.get_node(k) for k in keys}
        moved = sum(1 for k in keys if before[k] != after[k])
        frac = moved / len(keys)
        # ideal ~1/6 = 0.167; allow generous band
        self.assertLess(frac, 0.30, f"remap too high: {frac}")
        self.assertGreater(frac, 0.05, f"remap suspiciously low: {frac}")


class TestLRU(unittest.TestCase):
    def test_put_get(self):
        c = LRUCache(10)
        c.put("a", 1)
        self.assertEqual(c.get("a"), 1)

    def test_eviction(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")          # touch a -> b is now LRU
        c.put("c", 3)       # evicts b
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("c"), 3)

    def test_ttl_expiry(self):
        c = LRUCache(10)
        c.put("a", 1, ttl=0.1)
        self.assertEqual(c.get("a"), 1)
        time.sleep(0.15)
        self.assertIsNone(c.get("a"))

    def test_delete(self):
        c = LRUCache(10)
        c.put("a", 1)
        self.assertTrue(c.delete("a"))
        self.assertFalse(c.delete("a"))


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = Cluster().start(5)
        cls.client = CacheClient(cls.cluster.addresses(), n=3, r=2, w=2)

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop_all()

    def test_put_get_roundtrip(self):
        res = self.client.put("foo", {"x": 42})
        self.assertTrue(res["ok"])
        self.assertGreaterEqual(res["acks"], 2)
        got = self.client.get("foo")
        self.assertTrue(got["ok"])
        self.assertEqual(got["value"], {"x": 42})

    def test_replication_factor(self):
        replicas = self.client.replicas_for("foo")
        self.assertEqual(len(replicas), 3)

    def test_read_after_node_failure(self):
        self.client.put("survivor", {"alive": True})
        replicas = self.client.replicas_for("survivor")
        # kill one replica of this key
        victim = replicas[0]
        self.cluster.kill(victim)
        time.sleep(0.1)
        got = self.client.get("survivor")
        self.assertTrue(got["ok"], "read quorum should survive 1 node loss")
        self.assertEqual(got["value"], {"alive": True})
        # restart for other tests' independence not required (last test ordering)

    def test_delete(self):
        self.client.put("tmp", {"v": 1})
        self.client.delete("tmp")
        got = self.client.get("tmp")
        # after delete, value should be gone (None) though read quorum ok
        self.assertIsNone(got["value"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
