# mini-db — a teaching SQL engine in pure Python

A small but real relational database engine that parses a useful subset of SQL,
plans queries into physical operators, and executes them with a textbook
**Volcano (iterator) model**. Pure Python 3.9+ standard library — no
dependencies, nothing to install.

```
SQL text ──▶ tokenizer ──▶ parser ──▶ AST ──▶ planner ──▶ operator tree ──▶ executor ──▶ rows
                                                              ▲
                                                          storage (in-memory rows
                                                          + page-based disk file)
```

## Supported SQL

- `CREATE TABLE t (col TYPE, ...)` — types: `INT`/`INTEGER`, `FLOAT`/`REAL`, `TEXT`/`STRING`
- `INSERT INTO t [(cols)] VALUES (...), (...), ...` — multi-row inserts
- `SELECT`
  - projection (`SELECT a, b`) and `SELECT *`
  - `WHERE` with `= != <> < > <= >=`, `AND`, `OR`, parentheses
  - `INNER JOIN ... ON a.x = b.y` (equi-join)
  - aggregates `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
  - `GROUP BY`
  - `ORDER BY ... [ASC|DESC]` (multi-key, stable)
  - `LIMIT n`
  - column/aggregate aliases via `AS`
- Column references may be bare (`age`) or qualified (`emp.age`).

## Files / modules

| File           | Responsibility |
|----------------|----------------|
| `tokenizer.py` | Lexical analysis: SQL string → list of `Token`. |
| `ast_nodes.py` | Dataclass AST node definitions. |
| `parser.py`    | Recursive-descent parser: tokens → AST. |
| `storage.py`   | In-memory row store + page-based on-disk persistence. |
| `planner.py`   | AST → tree of physical operators; also `EXPLAIN` rendering. |
| `executor.py`  | Physical operators (Volcano model): `SeqScan`, `Filter`, `Project`, `HashJoin`, `Sort`, `Limit`, `Aggregate`, plus expression evaluation. |
| `engine.py`    | High-level façade: dispatch CREATE/INSERT/SELECT; pretty result tables. |
| `repl.py`      | Interactive shell with `\` meta-commands. |
| `demo.py`      | Loads sample data and runs ~8 example queries + EXPLAIN + persistence. |
| `tests.py`     | 43 assertions covering every feature. |

## Quick start

```bash
python3 demo.py        # full demonstration
python3 tests.py       # run the test suite (exits non-zero on failure)
python3 repl.py        # interactive shell (optionally: python3 repl.py mydata.minidb)
```

In the REPL:

```
minidb> CREATE TABLE t (id INT, name TEXT);
minidb> INSERT INTO t VALUES (1, 'alice'), (2, 'bob');
minidb> SELECT * FROM t WHERE id > 1;
minidb> \explain SELECT COUNT(*) FROM t GROUP BY name;
minidb> \save mydata.minidb
minidb> \tables
minidb> \quit
```

## The Volcano (iterator) model

Every physical operator implements the same three-method interface:

```python
op.open()    # set up state, recursively open children
op.next()    # return the next output row (a dict), or None when exhausted
op.close()   # tear down, recursively close children
```

A query plan is a **tree of operators**. Execution is *demand-driven*: the
consumer calls `next()` on the root, which calls `next()` on its child, all the
way down to the leaf `SeqScan`s. Rows are *pulled* up the tree one at a time.

This gives **pipelined, row-at-a-time** execution: a row produced by a scan
flows through `Filter` → `Project` without ever materializing the full
intermediate relation. Only operators that *must* see all input before
producing output break the pipeline ("stop-and-go" / pipeline breakers):

- **`Sort`** must buffer every input row before it can emit the smallest one.
- **`Aggregate`** must consume the whole input to compute group totals.
- **`HashJoin`** buffers one side (the *build* side) into a hash table, then
  *streams* (probes) the other side — so it's half-pipelined.

A "row" in flight is a `dict` mapping column name → value. Scans emit both the
bare name (`age`) and the qualified name (`emp.age`) so filters and joins can
reference either form.

### Operators

| Operator   | Kind            | Notes |
|------------|-----------------|-------|
| `SeqScan`  | leaf            | Iterates a table's rows in insertion order. |
| `Filter`   | pipelined       | Drops rows where the `WHERE` predicate is false. |
| `Project`  | pipelined       | Computes the output column list (and reads pre-computed aggregate values). |
| `HashJoin` | semi-pipelined  | Builds a hash table on the right input, probes with the left. |
| `Sort`     | pipeline breaker| Buffers all rows, stable multi-key sort. |
| `Limit`    | pipelined       | Stops after `n` rows. |
| `Aggregate`| pipeline breaker| Hash-based grouping; computes COUNT/SUM/AVG/MIN/MAX. |

## How query planning works

`planner.plan_select()` performs a single rule-based pass that maps SQL clauses
onto a fixed operator pipeline (each stage is built only if its clause exists):

```
SeqScan(from_table)
  └─▶ HashJoin(+ SeqScan(join_table))   if JOIN
        └─▶ Filter(where)               if WHERE
              └─▶ Aggregate(group_by)   if GROUP BY / aggregates
                    └─▶ Sort(order_by)  if ORDER BY
                          └─▶ Project(select_list)
                                └─▶ Limit(n)   if LIMIT
```

The ordering encodes the relational-algebra rules: filter before aggregate,
aggregate before sort, project near the top, limit last. Because `ORDER BY` may
reference an alias defined in the `SELECT` list (e.g. `ORDER BY payroll`) but
`Sort` runs *below* `Project`, the `Aggregate` operator also emits values under
their projected aliases so later sorting can find them.

A production optimizer would additionally:
- separate a *logical* plan (relational algebra) from the *physical* plan,
- use a **cost model + statistics** to choose join algorithms and order,
- push predicates down below joins, prune projections early,
- pick indexes instead of always doing sequential scans.

This engine keeps a single deterministic plan so the mapping from SQL to
operators stays easy to read. Use `\explain <sql>` in the REPL (or
`planner.explain()`) to print the chosen operator tree, e.g.:

```
Project(departments.name, COUNT(*) AS n, SUM(salary) AS payroll)
  Sort(payroll DESC)
    Aggregate(group=[departments.name] aggs=[COUNT(*), SUM(salary)])
      HashJoin(employees.dept_id = departments.id)
        SeqScan(table=employees as employees)
        SeqScan(table=departments as departments)
```

## Storage & page-based persistence

In memory a `Table` is a schema (ordered columns + types) plus a list of row
dicts. Values are coerced to the column's declared type on insert.

On disk, the whole database serializes into a single file laid out as
fixed-size **4096-byte pages** (a teaching model of how real engines page data
rather than a high-performance format):

- **Page 0 (superblock):** `magic | version | page_size | num_pages | catalog_len`
  followed by a JSON catalog (per-table schema + which pages hold its data).
- **Pages 1+:** each table's rows are JSON-encoded, length-prefixed, and chunked
  across one or more contiguous pages.

The format is self-describing, so the REPL can re-open a `.minidb` file across
runs (`\save path` to write, `python3 repl.py path` to reopen). The test suite
verifies an exact round-trip including a multi-page (2000-row) table.

## Design notes & limitations

- Single statement types only: no `UPDATE`/`DELETE`, subqueries, `HAVING`,
  `LEFT JOIN`, or `DISTINCT` (intentionally out of scope).
- Joins are equi-joins on a single `=` condition.
- No indexes — every base-table access is a sequential scan.
- Reserved words (`avg`, `count`, `name` of keywords, etc.) can't be used as
  aliases; pick a non-keyword alias.

These boundaries keep each module small and readable while still demonstrating
the real architecture of a SQL execution engine end to end.
