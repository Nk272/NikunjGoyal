"""
engine.py
=========
High-level façade that ties the pipeline together:

    SQL string -> tokenize -> parse -> (plan + execute) -> results

Handles statement dispatch (CREATE / INSERT / SELECT) against a Database.
"""

from parser import parse, parse_many
import ast_nodes as A
import planner
from storage import Database


class Engine:
    def __init__(self, path=None):
        self.db = Database(path)

    def execute(self, sql):
        """Execute one statement. Returns a Result object."""
        stmt = parse(sql)
        return self._dispatch(stmt)

    def execute_script(self, sql):
        """Execute many ';'-separated statements; return the last Result."""
        result = None
        for stmt in parse_many(sql):
            result = self._dispatch(stmt)
        return result

    def _dispatch(self, stmt):
        if isinstance(stmt, A.CreateTable):
            self.db.create_table(stmt.table, stmt.columns)
            return Result(message="Table %r created" % stmt.table)
        if isinstance(stmt, A.Insert):
            return self._do_insert(stmt)
        if isinstance(stmt, A.Select):
            columns, rows = planner.execute(stmt, self.db)
            return Result(columns=columns, rows=rows)
        raise RuntimeError("Unsupported statement: %r" % type(stmt).__name__)

    def _do_insert(self, stmt):
        table = self.db.get_table(stmt.table)
        cols = stmt.columns or table.columns
        n = 0
        for row in stmt.rows:
            if len(row) != len(cols):
                raise RuntimeError(
                    "INSERT column/value count mismatch for %r" % stmt.table)
            row_dict = {c: lit.value for c, lit in zip(cols, row)}
            table.insert(row_dict)
            n += 1
        return Result(message="%d row(s) inserted into %r" % (n, stmt.table))

    def save(self, path=None):
        self.db.save(path)


class Result:
    def __init__(self, columns=None, rows=None, message=None):
        self.columns = columns or []
        self.rows = rows or []
        self.message = message

    @property
    def is_query(self):
        return self.message is None

    def render(self):
        """Pretty ASCII table (or status message)."""
        if not self.is_query:
            return self.message
        if not self.rows:
            header = " | ".join(self.columns) if self.columns else "(no columns)"
            return header + "\n(0 rows)"

        cols = self.columns
        widths = {c: len(str(c)) for c in cols}
        for r in self.rows:
            for c in cols:
                widths[c] = max(widths[c], len(_fmt(r.get(c))))

        def line(values):
            return " | ".join(str(v).ljust(widths[c])
                              for c, v in zip(cols, values))

        sep = "-+-".join("-" * widths[c] for c in cols)
        out = [line(cols), sep]
        for r in self.rows:
            out.append(line([_fmt(r.get(c)) for c in cols]))
        out.append("(%d row%s)" % (len(self.rows),
                                   "" if len(self.rows) == 1 else "s"))
        return "\n".join(out)


def _fmt(v):
    if v is None:
        return "NULL"
    if isinstance(v, float):
        # trim trailing zeros for clean display
        s = "{:.4f}".format(v).rstrip("0").rstrip(".")
        return s if s else "0"
    return str(v)
