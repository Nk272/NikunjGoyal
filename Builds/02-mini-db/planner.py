"""
planner.py
==========
Turns an AST into a tree of physical operators (see executor.py).

This is a deliberately small, rule-based planner.  Real systems separate a
*logical* plan (relational algebra) from a *physical* plan (chosen operators)
and use a cost model to pick between alternatives.  Here we do a single pass
that maps SQL clauses directly onto a fixed operator pipeline:

    SeqScan(from)                         -- read base table
      -> [HashJoin with SeqScan(join)]    -- if JOIN present
      -> [Filter]                         -- if WHERE present
      -> [Aggregate]                      -- if GROUP BY / aggregates present
      -> [Sort]                           -- if ORDER BY present
      -> [Project]                        -- projection list
      -> [Limit]                          -- if LIMIT present

The order matters: filtering before aggregation, aggregation before sort,
projection near the top, limit last.  Each stage is optional; we only build an
operator when the corresponding clause exists.

The function `explain()` renders the chosen operator tree as indented text so
you can see the plan the same way `EXPLAIN` would show it.
"""

import ast_nodes as A
import executor as X


class PlanError(Exception):
    pass


def _collect_aggregates(items):
    """Return the list of Aggregate exprs found in the projection."""
    return [it.expr for it in items if isinstance(it.expr, A.Aggregate)]


def plan_select(stmt, db):
    """Build a physical operator tree for a SELECT AST node."""
    # --- leaf scan(s) ---------------------------------------------------
    base = db.get_table(stmt.from_table)
    base_alias = stmt.from_alias or stmt.from_table
    root = X.SeqScan(base, base_alias)

    # --- join -----------------------------------------------------------
    if stmt.join is not None:
        right_tbl = db.get_table(stmt.join.table)
        right = X.SeqScan(right_tbl, stmt.join.table)
        # Decide which side of the ON condition belongs to which input.
        left_key, right_key = _orient_join_keys(
            stmt.join, base_alias, stmt.join.table)
        root = X.HashJoin(root, right, left_key, right_key)

    # --- filter ---------------------------------------------------------
    if stmt.where is not None:
        root = X.Filter(root, stmt.where)

    # --- aggregate ------------------------------------------------------
    aggregates = _collect_aggregates(stmt.items)
    if aggregates or stmt.group_by:
        aliases = {}
        for it in stmt.items:
            if it.alias:
                if isinstance(it.expr, A.Aggregate):
                    aliases[X._agg_key(it.expr)] = it.alias
                elif isinstance(it.expr, A.Column):
                    aliases[it.expr.name] = it.alias
        root = X.Aggregate(root, stmt.group_by, aggregates, aliases)
        # after aggregation the only available columns are group keys +
        # aggregate outputs, so projection runs on top of it.
        projection_items = stmt.items
    else:
        # SELECT * has a single Star item -> project everything
        if len(stmt.items) == 1 and isinstance(stmt.items[0].expr, A.Star):
            projection_items = None
        else:
            projection_items = stmt.items

    # --- sort -----------------------------------------------------------
    if stmt.order_by:
        root = X.Sort(root, stmt.order_by)

    # --- project --------------------------------------------------------
    root = X.Project(root, projection_items)

    # --- limit ----------------------------------------------------------
    if stmt.limit is not None:
        root = X.Limit(root, stmt.limit)

    return root


def _orient_join_keys(join, left_alias, right_alias):
    """Ensure (left_key, right_key) line up with (left input, right input)."""
    a, b = join.on_left, join.on_right
    # If column tables are specified, use them to orient.
    if a.table == right_alias or b.table == left_alias:
        return b, a
    return a, b


def execute(stmt, db):
    """Plan + run a SELECT, returning (column_names, list_of_row_dicts)."""
    op = plan_select(stmt, db)
    rows = []
    op.open()
    try:
        while True:
            r = op.next()
            if r is None:
                break
            rows.append(r)
    finally:
        op.close()
    columns = list(rows[0].keys()) if rows else _output_columns(stmt)
    return columns, rows


def _output_columns(stmt):
    """Best-effort column names for an empty result set."""
    if len(stmt.items) == 1 and isinstance(stmt.items[0].expr, A.Star):
        return []
    names = []
    for it in stmt.items:
        if isinstance(it.expr, A.Column):
            names.append(it.alias or it.expr.name)
        elif isinstance(it.expr, A.Aggregate):
            names.append(it.alias or X._agg_key(it.expr))
        else:
            names.append(it.alias or "expr")
    return names


# ---------------------------------------------------------------------------
# EXPLAIN: render the physical plan as text
# ---------------------------------------------------------------------------
def explain(op, indent=0):
    pad = "  " * indent
    name = type(op).__name__
    detail = ""
    children = []

    if isinstance(op, X.SeqScan):
        detail = "table={} as {}".format(op.table.name, op.alias)
    elif isinstance(op, X.Filter):
        detail = "pred=" + _expr_str(op.predicate)
        children = [op.child]
    elif isinstance(op, X.Project):
        if op.items is None:
            detail = "*"
        else:
            detail = ", ".join(_item_str(i) for i in op.items)
        children = [op.child]
    elif isinstance(op, X.HashJoin):
        detail = "{} = {}".format(op.left_key.qualified, op.right_key.qualified)
        children = [op.left, op.right]
    elif isinstance(op, X.Sort):
        detail = ", ".join(
            "{}{}".format(k.expr.qualified, " DESC" if k.descending else "")
            for k in op.order_keys)
        children = [op.child]
    elif isinstance(op, X.Limit):
        detail = str(op.n)
        children = [op.child]
    elif isinstance(op, X.Aggregate):
        gb = ", ".join(g.qualified for g in op.group_by)
        ags = ", ".join(X._agg_key(a) for a in op.aggregates)
        detail = "group=[{}] aggs=[{}]".format(gb, ags)
        children = [op.child]

    line = "{}{}({})".format(pad, name, detail)
    out = [line]
    for c in children:
        out.append(explain(c, indent + 1))
    return "\n".join(out)


def _expr_str(e):
    if isinstance(e, A.Literal):
        return repr(e.value)
    if isinstance(e, A.Column):
        return e.qualified
    if isinstance(e, A.BinOp):
        return "({} {} {})".format(_expr_str(e.left), e.op, _expr_str(e.right))
    return str(e)


def _item_str(it):
    e = it.expr
    if isinstance(e, A.Star):
        s = "*"
    elif isinstance(e, A.Column):
        s = e.qualified
    elif isinstance(e, A.Aggregate):
        s = X._agg_key(e)
    else:
        s = _expr_str(e)
    if it.alias:
        s += " AS " + it.alias
    return s
