"""
storage.py
==========
Storage layer for the mini DB.

Two responsibilities:

  1. In-memory row store.  A `Table` holds a schema (ordered column names +
     types) and a python list of rows (each row is a dict {col: value}).

  2. Simple page-based on-disk persistence.  The whole catalog + data is
     serialized into fixed-size pages written to a single file.  This is a
     teaching model of how real engines lay bytes out in pages rather than a
     high-performance format.

Page layout
-----------
The file is a sequence of PAGE_SIZE-byte pages.

  Page 0  : header / superblock
            magic(8) | version(4) | page_size(4) | num_pages(4) | catalog_len(4)
            followed by a JSON catalog blob (schemas + per-table page ranges).

  Page 1+ : data pages.  Each table's rows are JSON-encoded, the byte stream is
            chunked across one or more contiguous pages.  A 4-byte length prefix
            at the start of the table's first page gives the payload size.

The format is deliberately straightforward and self-describing so the REPL can
re-open a database file across runs.
"""

import json
import os
import struct

PAGE_SIZE = 4096
MAGIC = b"MINIDB01"
VERSION = 1


class StorageError(Exception):
    pass


class Table:
    """In-memory representation of a single table."""

    def __init__(self, name, columns, types):
        self.name = name
        self.columns = list(columns)        # ordered list of column names
        self.types = dict(types)            # {col: 'int'|'float'|'text'}
        self.rows = []                      # list of dict {col: value}

    def insert(self, row_dict):
        # ensure every column is present (default to None) and coerce types
        full = {}
        for col in self.columns:
            val = row_dict.get(col, None)
            full[col] = self._coerce(col, val)
        self.rows.append(full)

    def _coerce(self, col, val):
        if val is None:
            return None
        t = self.types[col]
        try:
            if t == "int":
                return int(val)
            if t == "float":
                return float(val)
            if t == "text":
                return str(val)
        except (ValueError, TypeError):
            raise StorageError(
                "Cannot coerce %r into %s for column %s" % (val, t, col))
        return val

    def __len__(self):
        return len(self.rows)


class Database:
    """A collection of tables, with optional on-disk persistence."""

    def __init__(self, path=None):
        self.path = path
        self.tables = {}
        if path and os.path.exists(path):
            self.load()

    # --- catalog operations ----------------------------------------------
    def create_table(self, name, column_defs):
        if name in self.tables:
            raise StorageError("Table %r already exists" % name)
        cols = [c.name for c in column_defs]
        types = {c.name: c.type for c in column_defs}
        self.tables[name] = Table(name, cols, types)
        return self.tables[name]

    def get_table(self, name):
        if name not in self.tables:
            raise StorageError("No such table: %r" % name)
        return self.tables[name]

    def drop_table(self, name):
        self.tables.pop(name, None)

    # --- persistence ------------------------------------------------------
    def save(self, path=None):
        """Serialize the whole database to a page-based file."""
        path = path or self.path
        if not path:
            raise StorageError("No path given for save()")

        # Build catalog + data pages.
        catalog = {"tables": {}}
        data_pages = []          # list of bytes objects, each <= PAGE_SIZE
        next_page = 1            # page 0 is the header

        for name, table in self.tables.items():
            payload = json.dumps(table.rows).encode("utf-8")
            # length-prefix then chunk across pages
            blob = struct.pack("<I", len(payload)) + payload
            chunks = [blob[i:i + PAGE_SIZE] for i in range(0, len(blob), PAGE_SIZE)]
            if not chunks:
                chunks = [b""]
            start = next_page
            for ch in chunks:
                data_pages.append(ch.ljust(PAGE_SIZE, b"\x00"))
                next_page += 1
            catalog["tables"][name] = {
                "columns": table.columns,
                "types": table.types,
                "start_page": start,
                "num_pages": len(chunks),
                "payload_len": len(payload),
            }

        catalog_blob = json.dumps(catalog).encode("utf-8")
        if len(catalog_blob) + 24 > PAGE_SIZE:
            raise StorageError("Catalog too large for a single header page")

        num_pages = 1 + len(data_pages)
        header = MAGIC
        header += struct.pack("<IIII", VERSION, PAGE_SIZE, num_pages,
                              len(catalog_blob))
        header += catalog_blob
        header = header.ljust(PAGE_SIZE, b"\x00")

        with open(path, "wb") as f:
            f.write(header)
            for pg in data_pages:
                f.write(pg)
        self.path = path

    def load(self, path=None):
        """Read a database back from a page-based file."""
        path = path or self.path
        with open(path, "rb") as f:
            header = f.read(PAGE_SIZE)
            if header[:8] != MAGIC:
                raise StorageError("Bad magic; not a minidb file")
            version, page_size, num_pages, cat_len = struct.unpack(
                "<IIII", header[8:24])
            catalog = json.loads(header[24:24 + cat_len].decode("utf-8"))

            self.tables = {}
            for name, meta in catalog["tables"].items():
                # read this table's contiguous pages
                f.seek(meta["start_page"] * page_size)
                raw = f.read(meta["num_pages"] * page_size)
                (payload_len,) = struct.unpack("<I", raw[:4])
                payload = raw[4:4 + payload_len]
                rows = json.loads(payload.decode("utf-8")) if payload_len else []

                # rebuild Table
                col_defs = []
                from ast_nodes import ColumnDef
                for col in meta["columns"]:
                    col_defs.append(ColumnDef(col, meta["types"][col]))
                table = Table(name, meta["columns"], meta["types"])
                table.rows = rows
                self.tables[name] = table
        self.path = path


if __name__ == "__main__":
    from ast_nodes import ColumnDef
    db = Database()
    db.create_table("t", [ColumnDef("id", "int"), ColumnDef("name", "text")])
    db.get_table("t").insert({"id": 1, "name": "alice"})
    db.get_table("t").insert({"id": 2, "name": "bob"})
    db.save("/tmp/_minidb_demo.db")
    db2 = Database("/tmp/_minidb_demo.db")
    print("reloaded:", db2.get_table("t").rows)
