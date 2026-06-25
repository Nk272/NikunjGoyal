"""
executor.py
===========
Physical operators implemented in the Volcano (a.k.a. iterator) model.

The Volcano model
-----------------
Every physical operator exposes the same interface:

    open()        -> prepare state, recursively open children
    next()        -> return the next output row, or None when exhausted
    close()       -> release resources, recursively close children

A query plan is a tree of these operators.  Rows are *pulled* from the root:
the root calls next() on its child, which calls next() on its child, and so on
down to the leaf scans.  This gives pipelined, row-at-a-time execution with no
intermediate materialization except where an operator inherently must buffer
(Sort and Aggregate).

A "row" flowing through operators is a dict mapping a (possibly qualified)
column name to a value.  Scans emit both the bare name (`age`) and the
qualified name (`emp.age`) so that filters/joins can reference either form.

Each operator below is a python iterator wrapper around the open/next/close
protocol; `__iter__`/`__next__` are provided so you can also just loop.
"""

import ast_nodes as A


# ---------------------------------------------------------------------------
# Expression evaluation
# ---------------------------------------------------------------------------
def eval_expr(expr, row):
    """Evaluate a WHERE-style expression node against a row dict."""
    if isinstance(expr, A.Literal):
        return expr.value
    if isinstance(expr, A.Column):
        return lookup(row, expr)
    if isinstance(expr, A.BinOp):
        return eval_binop(expr, row)
    raise RuntimeError("Cannot evaluate expression node: %r" % (expr,))


def lookup(row, col):
    """Resolve a Column against a row, trying qualified then bare name."""
    if col.table is not None:
        key = col.qualified
        if key in row:
            return row[key]
        # fall back to bare name
        if col.name in row:
            return row[col.name]
        raise RuntimeError("Unknown column %r" % key)
    if col.name in row:
        return row[col.name]
    # maybe it is stored qualified under exactly one table
    matches = [v for k, v in row.items() if k.endswith("." + col.name)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RuntimeError("Ambiguous column %r" % col.name)
    raise RuntimeError("Unknown column %r" % col.name)


def eval_binop(expr, row):
    op = expr.op
    if op == "and":
        return bool(eval_expr(expr.left, row)) and bool(eval_expr(expr.right, row))
    if op == "or":
        return bool(eval_expr(expr.left, row)) or bool(eval_expr(expr.right, row))

    left = eval_expr(expr.left, row)
    right = eval_expr(expr.right, row)

    if op in ("=", "=="):
        return left == right
    if op in ("!=", "<>"):
        return left != right
    if op == "<":
        return _cmp_safe(left, right) < 0
    if op == ">":
        return _cmp_safe(left, right) > 0
    if op == "<=":
        return _cmp_safe(left, right) <= 0
    if op == ">=":
        return _cmp_safe(left, right) >= 0
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        return left / right
    raise RuntimeError("Unknown operator %r" % op)


def _cmp_safe(a, b):
    """Three-way compare that tolerates None and mixed numeric/str."""
    if a is None and b is None:
        return 0
    if a is None:
        return -1
    if b is None:
        return 1
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


# ---------------------------------------------------------------------------
# Base operator
# ---------------------------------------------------------------------------
class Operator:
    def open(self):
        raise NotImplementedError

    def next(self):
        raise NotImplementedError

    def close(self):
        pass

    # Make every operator usable as a python iterator too.
    def __iter__(self):
        self.open()
        return self

    def __next__(self):
        row = self.next()
        if row is None:
            self.close()
            raise StopIteration
        return row


# ---------------------------------------------------------------------------
# SeqScan: leaf operator, reads rows from a Table
# ---------------------------------------------------------------------------
class SeqScan(Operator):
    def __init__(self, table, alias=None):
        self.table = table
        self.alias = alias or table.name
        self._idx = 0

    def open(self):
        self._idx = 0

    def next(self):
        if self._idx >= len(self.table.rows):
            return None
        raw = self.table.rows[self._idx]
        self._idx += 1
        # emit both bare and qualified column names
        out = {}
        for col in self.table.columns:
            out[col] = raw.get(col)
            out["{}.{}".format(self.alias, col)] = raw.get(col)
        return out


# ---------------------------------------------------------------------------
# Filter: apply a WHERE predicate
# ---------------------------------------------------------------------------
class Filter(Operator):
    def __init__(self, child, predicate):
        self.child = child
        self.predicate = predicate

    def open(self):
        self.child.open()

    def next(self):
        while True:
            row = self.child.next()
            if row is None:
                return None
            if eval_expr(self.predicate, row):
                return row

    def close(self):
        self.child.close()


# ---------------------------------------------------------------------------
# Project: select / compute output columns
# ---------------------------------------------------------------------------
class Project(Operator):
    def __init__(self, child, items):
        # items: list of SelectItem, or None for SELECT *
        self.child = child
        self.items = items

    def open(self):
        self.child.open()

    def next(self):
        row = self.child.next()
        if row is None:
            return None
        if self.items is None:        # SELECT *
            # strip qualified duplicates for a clean output
            return {k: v for k, v in row.items() if "." not in k}
        out = {}
        for item in self.items:
            name, val = self._eval_item(item, row)
            out[name] = val
        return out

    def _eval_item(self, item, row):
        expr = item.expr
        if isinstance(expr, A.Column):
            name = item.alias or expr.name
            return name, lookup(row, expr)
        # pre-computed aggregate value carried in the row under its output key
        if isinstance(expr, A.Aggregate):
            name = item.alias or expr.alias or _agg_key(expr)
            return name, row.get(_agg_key(expr))
        # generic expression
        name = item.alias or "expr"
        return name, eval_expr(expr, row)

    def close(self):
        self.child.close()


def _agg_key(agg):
    arg = "*" if isinstance(agg.arg, A.Star) else agg.arg.name
    return "{}({})".format(agg.func.upper(), arg)


# ---------------------------------------------------------------------------
# HashJoin: equi-join two inputs on left.key = right.key
# ---------------------------------------------------------------------------
class HashJoin(Operator):
    def __init__(self, left, right, left_key, right_key):
        self.left = left
        self.right = right
        self.left_key = left_key      # A.Column
        self.right_key = right_key    # A.Column
        self._build = {}              # hash table: key -> list of right rows
        self._cur_left = None
        self._matches = []
        self._match_idx = 0

    def open(self):
        self.left.open()
        self.right.open()
        # Build phase: hash the RIGHT (build) side into memory.
        self._build = {}
        while True:
            r = self.right.next()
            if r is None:
                break
            k = lookup(r, self.right_key)
            self._build.setdefault(k, []).append(r)
        self._cur_left = None
        self._matches = []
        self._match_idx = 0

    def next(self):
        # Probe phase: stream the LEFT side, emit one row per match.
        while True:
            if self._cur_left is not None and self._match_idx < len(self._matches):
                right_row = self._matches[self._match_idx]
                self._match_idx += 1
                merged = dict(self._cur_left)
                merged.update(right_row)
                return merged
            # advance to next left row
            self._cur_left = self.left.next()
            if self._cur_left is None:
                return None
            k = lookup(self._cur_left, self.left_key)
            self._matches = self._build.get(k, [])
            self._match_idx = 0

    def close(self):
        self.left.close()
        self.right.close()


# ---------------------------------------------------------------------------
# Sort: ORDER BY (buffers all input — a "stop-and-go" operator)
# ---------------------------------------------------------------------------
class Sort(Operator):
    def __init__(self, child, order_keys):
        self.child = child
        self.order_keys = order_keys    # list of A.OrderKey
        self._buf = []
        self._idx = 0

    def open(self):
        self.child.open()
        self._buf = []
        while True:
            row = self.child.next()
            if row is None:
                break
            self._buf.append(row)
        # Stable multi-key sort: apply keys from last to first.
        import functools

        def cmp_rows(a, b):
            for key in self.order_keys:
                va = lookup(a, key.expr)
                vb = lookup(b, key.expr)
                c = _cmp_safe(va, vb)
                if c != 0:
                    return -c if key.descending else c
            return 0

        self._buf.sort(key=functools.cmp_to_key(cmp_rows))
        self._idx = 0

    def next(self):
        if self._idx >= len(self._buf):
            return None
        row = self._buf[self._idx]
        self._idx += 1
        return row

    def close(self):
        self.child.close()


# ---------------------------------------------------------------------------
# Limit
# ---------------------------------------------------------------------------
class Limit(Operator):
    def __init__(self, child, n):
        self.child = child
        self.n = n
        self._count = 0

    def open(self):
        self.child.open()
        self._count = 0

    def next(self):
        if self._count >= self.n:
            return None
        row = self.child.next()
        if row is None:
            return None
        self._count += 1
        return row

    def close(self):
        self.child.close()


# ---------------------------------------------------------------------------
# Aggregate: COUNT/SUM/AVG/MIN/MAX with optional GROUP BY
# ---------------------------------------------------------------------------
class Aggregate(Operator):
    def __init__(self, child, group_by, aggregates, aliases=None):
        # group_by: list of A.Column
        # aggregates: list of A.Aggregate
        # aliases: optional {canonical_key: alias} so ORDER BY can reference
        #          a projected alias that only exists after aggregation.
        self.child = child
        self.group_by = group_by
        self.aggregates = aggregates
        self.aliases = aliases or {}
        self._out = []
        self._idx = 0

    def open(self):
        self.child.open()
        groups = {}          # group_key tuple -> {state}
        order = []           # preserve first-seen group order

        while True:
            row = self.child.next()
            if row is None:
                break
            key = tuple(lookup(row, g) for g in self.group_by)
            if key not in groups:
                groups[key] = self._new_state()
                order.append(key)
            self._accumulate(groups[key], row)

        self._out = []
        for key in order:
            state = groups[key]
            out = {}
            # group columns
            for g, kval in zip(self.group_by, key):
                out[g.name] = kval
                if g.table:
                    out[g.qualified] = kval
                if g.name in self.aliases:
                    out[self.aliases[g.name]] = kval
            # aggregate results
            for i, agg in enumerate(self.aggregates):
                ak = _agg_key(agg)
                val = self._finalize(i, agg, state)
                out[ak] = val
                if ak in self.aliases:
                    out[self.aliases[ak]] = val
            self._out.append(out)

        # if no group by and no rows, still produce one row (e.g. COUNT=0)
        if not self.group_by and not order:
            out = {}
            state = self._new_state()
            for i, agg in enumerate(self.aggregates):
                out[_agg_key(agg)] = self._finalize(i, agg, state)
            self._out.append(out)

        self._idx = 0

    def _new_state(self):
        return {i: {"count": 0, "sum": 0.0, "min": None, "max": None,
                    "nonnull": 0}
                for i in range(len(self.aggregates))}

    def _accumulate(self, state, row):
        for i, agg in enumerate(self.aggregates):
            s = state[i]
            s["count"] += 1
            if isinstance(agg.arg, A.Star):
                continue
            val = lookup(row, agg.arg)
            if val is None:
                continue
            s["nonnull"] += 1
            if isinstance(val, (int, float)):
                s["sum"] += val
            if s["min"] is None or _cmp_safe(val, s["min"]) < 0:
                s["min"] = val
            if s["max"] is None or _cmp_safe(val, s["max"]) > 0:
                s["max"] = val

    def _finalize(self, i, agg, state):
        s = state[i]
        f = agg.func
        if f == "count":
            if isinstance(agg.arg, A.Star):
                return s["count"]
            return s["nonnull"]
        if f == "sum":
            return s["sum"]
        if f == "avg":
            return s["sum"] / s["nonnull"] if s["nonnull"] else None
        if f == "min":
            return s["min"]
        if f == "max":
            return s["max"]
        raise RuntimeError("Unknown aggregate %r" % f)

    def next(self):
        if self._idx >= len(self._out):
            return None
        row = self._out[self._idx]
        self._idx += 1
        return row

    def close(self):
        self.child.close()
