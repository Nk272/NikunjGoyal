"""
cluster.py -- Spin up several CacheNode servers in background threads on
localhost, all within one process. Returns the running nodes and an address
map suitable for constructing a CacheClient.
"""

import socket
import time

from node import CacheNode


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Cluster:
    def __init__(self, host="127.0.0.1", capacity=4096):
        self.host = host
        self.capacity = capacity
        self.nodes = {}  # node_id -> CacheNode

    def start_node(self, node_id, port=None):
        if port is None:
            port = _free_port()
        node = CacheNode(node_id, self.host, port, capacity=self.capacity)
        node.start()
        self.nodes[node_id] = node
        return node

    def start(self, count):
        for i in range(count):
            self.start_node(f"node-{i}")
        self._wait_healthy()
        return self

    def kill(self, node_id):
        node = self.nodes.pop(node_id, None)
        if node:
            node.stop()
        return node

    def addresses(self):
        return {nid: n.address for nid, n in self.nodes.items()}

    def stop_all(self):
        for node in list(self.nodes.values()):
            node.stop()
        self.nodes.clear()

    def _wait_healthy(self, attempts=50):
        import urllib.request
        for nid, node in self.nodes.items():
            url = f"http://{node.address}/health"
            for _ in range(attempts):
                try:
                    with urllib.request.urlopen(url, timeout=1) as r:
                        if r.status == 200:
                            break
                except Exception:
                    time.sleep(0.02)


if __name__ == "__main__":
    c = Cluster().start(4)
    print("Cluster up:")
    for nid, addr in c.addresses().items():
        print(f"  {nid} -> {addr}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        c.stop_all()
