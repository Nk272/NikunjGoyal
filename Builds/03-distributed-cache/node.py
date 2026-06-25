"""
node.py -- A single cache node: in-memory LRU store with TTL expiry,
exposed over HTTP.

Storage semantics:
  * LRU eviction once `capacity` distinct keys are exceeded.
  * Per-key TTL (seconds). Expired keys are treated as absent (lazy expiry
    on access, plus a best-effort sweep on each write).

HTTP API:
  GET    /kv/<key>          -> 200 {"value":...,"ts":...} or 404
  PUT    /kv/<key>          body: {"value":...,"ttl":<secs or null>} -> 200
  DELETE /kv/<key>          -> 200
  GET    /stats             -> 200 {"node":..., "size":..., "keys":[...]}
  GET    /health           -> 200 {"ok":true}
"""

import json
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class LRUCache:
    def __init__(self, capacity: int = 1024):
        self.capacity = capacity
        self._store = OrderedDict()  # key -> (value, expires_at_or_None)
        self._lock = threading.Lock()

    def _expired(self, entry) -> bool:
        _, expires_at = entry
        return expires_at is not None and time.time() >= expires_at

    def _sweep(self):
        # caller must hold lock
        dead = [k for k, e in self._store.items() if self._expired(e)]
        for k in dead:
            del self._store[k]

    def get(self, key):
        with self._lock:
            if key not in self._store:
                return None
            entry = self._store[key]
            if self._expired(entry):
                del self._store[key]
                return None
            self._store.move_to_end(key)  # mark most-recently-used
            return entry[0]

    def put(self, key, value, ttl=None):
        with self._lock:
            self._sweep()
            expires_at = time.time() + ttl if ttl else None
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, expires_at)
            # evict least-recently-used while over capacity
            while len(self._store) > self.capacity:
                self._store.popitem(last=False)

    def delete(self, key):
        with self._lock:
            existed = key in self._store
            self._store.pop(key, None)
            return existed

    def snapshot(self):
        with self._lock:
            self._sweep()
            return list(self._store.keys())

    def size(self):
        with self._lock:
            self._sweep()
            return len(self._store)


def make_handler(node_id: str, cache: LRUCache):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass  # silence default stderr logging

        def _send(self, code, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _key(self):
            # path like /kv/<key>
            parts = self.path.split("/", 2)
            return parts[2] if len(parts) == 3 else None

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"ok": True, "node": node_id})
            if self.path == "/stats":
                return self._send(200, {
                    "node": node_id,
                    "size": cache.size(),
                    "keys": cache.snapshot(),
                })
            if self.path.startswith("/kv/"):
                key = self._key()
                val = cache.get(key)
                if val is None:
                    return self._send(404, {"error": "not found", "key": key})
                return self._send(200, {"key": key, "value": val})
            return self._send(404, {"error": "bad path"})

        def do_PUT(self):
            if not self.path.startswith("/kv/"):
                return self._send(404, {"error": "bad path"})
            key = self._key()
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": "bad json"})
            cache.put(key, data.get("value"), data.get("ttl"))
            return self._send(200, {"ok": True, "key": key, "node": node_id})

        def do_DELETE(self):
            if not self.path.startswith("/kv/"):
                return self._send(404, {"error": "bad path"})
            key = self._key()
            existed = cache.delete(key)
            return self._send(200, {"ok": True, "key": key, "existed": existed})

    return Handler


class CacheNode:
    """A cache node running an HTTP server on a background thread."""

    def __init__(self, node_id: str, host: str, port: int, capacity: int = 1024):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.cache = LRUCache(capacity)
        self._server = None
        self._thread = None

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    def start(self):
        handler = make_handler(self.node_id, self.cache)
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None


if __name__ == "__main__":
    import sys
    nid = sys.argv[1] if len(sys.argv) > 1 else "node-0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    n = CacheNode(nid, "127.0.0.1", port)
    n.start()
    print(f"{nid} listening on 127.0.0.1:{port}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        n.stop()
