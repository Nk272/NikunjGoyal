"""
ring.py -- Consistent-hashing ring with virtual nodes.

A consistent-hashing ring maps both nodes and keys onto the same circular
hash space [0, 2**32). To find which node owns a key we hash the key and
walk clockwise to the first node hash >= the key hash (wrapping around at
the top of the ring).

Virtual nodes (a.k.a. "vnodes" or replicas-on-the-ring) place each physical
node at many points on the ring. This smooths out the key distribution so
that no single node owns a disproportionately large arc, and it means that
when a node joins or leaves only a small, roughly even fraction of keys move.
"""

import bisect
import hashlib


def _hash(value: str) -> int:
    """Stable 32-bit hash of a string using MD5 (used only for placement,
    not security). Returns an int in [0, 2**32)."""
    digest = hashlib.md5(value.encode("utf-8")).digest()
    # take the first 4 bytes -> 32-bit unsigned int
    return int.from_bytes(digest[:4], "big")


class ConsistentHashRing:
    def __init__(self, vnodes: int = 150):
        """
        :param vnodes: number of virtual nodes per physical node. More vnodes
                       => smoother distribution, more memory in the ring.
        """
        self.vnodes = vnodes
        self._ring = {}          # hash position -> physical node id
        self._sorted_hashes = [] # sorted list of hash positions
        self._nodes = set()      # set of physical node ids

    def _vnode_key(self, node: str, i: int) -> str:
        return f"{node}#{i}"

    def add_node(self, node: str) -> None:
        """Add a physical node, placing `vnodes` virtual points on the ring."""
        if node in self._nodes:
            return
        self._nodes.add(node)
        for i in range(self.vnodes):
            h = _hash(self._vnode_key(node, i))
            # On the rare collision, probe forward deterministically.
            while h in self._ring:
                h = (h + 1) % (2 ** 32)
            self._ring[h] = node
            bisect.insort(self._sorted_hashes, h)

    def remove_node(self, node: str) -> None:
        """Remove a physical node and all of its virtual points."""
        if node not in self._nodes:
            return
        self._nodes.discard(node)
        # Rebuild is simplest & safe given collision probing above.
        self._ring = {h: n for h, n in self._ring.items() if n != node}
        self._sorted_hashes = sorted(self._ring.keys())

    def get_node(self, key: str):
        """Return the single owning node for `key`, or None if ring empty."""
        if not self._ring:
            return None
        h = _hash(key)
        idx = bisect.bisect(self._sorted_hashes, h)
        if idx == len(self._sorted_hashes):
            idx = 0  # wrap around the top of the ring
        return self._ring[self._sorted_hashes[idx]]

    def get_nodes(self, key: str, n: int):
        """
        Return the preference list: the first `n` DISTINCT physical nodes
        encountered walking clockwise from hash(key). Used for replication.
        """
        if not self._ring:
            return []
        n = min(n, len(self._nodes))
        h = _hash(key)
        idx = bisect.bisect(self._sorted_hashes, h)
        result = []
        count = len(self._sorted_hashes)
        i = 0
        while len(result) < n and i < count:
            pos = (idx + i) % count
            node = self._ring[self._sorted_hashes[pos]]
            if node not in result:
                result.append(node)
            i += 1
        return result

    @property
    def nodes(self):
        return set(self._nodes)
