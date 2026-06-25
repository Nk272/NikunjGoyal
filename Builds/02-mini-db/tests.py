"""
tests.py
========
Assertion-based test suite. Run with:

    python3 tests.py

Covers tokenizer, parser, storage/persistence, and every executor feature:
projection, WHERE (simple + compound), ORDER BY, LIMIT, INNER JOIN, and all
aggregates with and without GROUP BY.
"""

import os
import tempfile

from engine import Engine
from parser import parse, parse_many
import ast_nodes as A
import tokenizer
from storage import Database
from ast_nodes import ColumnDef


PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ok  - %s" % msg)
    else:
        FAIL += 1
        print("  FAIL- %s" % msg)


def fresh_engine():
    e = Engine()
    e.execute_script("""
        CREATE TABLE emp (id INT, name TEXT, dept_id INT, salary FLOAT, age INT);
        CREATE TABLE dept (id INT, name TEXT);
        INSERT INTO dept (id, name) VALUES (1,'Eng'),(2,'Sales'),(3,'Res');
        INSERT INTO emp (id,name,dept_id,salary,age) VALUES
            (1,'Alice',1,95000.0,32),
            (2,'Bob',1,82000.0,41),
            (3,'Carol',2,71000.0,29),
            (4,'Dave',2,67000.0,38),
            (5,'Eve',3,120000.0,45),
            (6,'Frank',1,88000.0,27);
    """)
    return e


# --- tokenizer -------------------------------------------------------------
def test_tokenizer():
    print("[tokenizer]")
    toks = tokenizer.tokenize("SELECT a, COUNT(*) FROM t WHERE x >= 3;")
    kinds = [t.kind for t in toks]
    check(kinds[0] == tokenizer.KEYWORD, "first token is keyword SELECT")
    check(any(t.kind == tokenizer.STAR for t in toks), "recognizes '*'")
    check(any(t.value == ">=" for t in toks), "recognizes '>=' operator")
    check(toks[-1].kind == tokenizer.EOF, "stream ends with EOF")
    strtoks = tokenizer.tokenize("INSERT INTO t VALUES ('o''brien')")
    check(any(t.kind == tokenizer.STRING and t.value == "o'brien" for t in strtoks),
          "handles escaped quotes in strings")


# --- parser ----------------------------------------------------------------
def test_parser():
    print("[parser]")
    stmt = parse("CREATE TABLE t (id INT, name TEXT)")
    check(isinstance(stmt, A.CreateTable) and len(stmt.columns) == 2,
          "parses CREATE TABLE with 2 columns")
    check(stmt.columns[0].type == "int" and stmt.columns[1].type == "text",
          "maps column types correctly")

    ins = parse("INSERT INTO t (id,name) VALUES (1,'a'),(2,'b')")
    check(isinstance(ins, A.Insert) and len(ins.rows) == 2,
          "parses multi-row INSERT")

    sel = parse("SELECT a, COUNT(*) AS n FROM t WHERE x>1 AND y<5 "
                "GROUP BY a ORDER BY n DESC LIMIT 10")
    check(isinstance(sel, A.Select), "parses SELECT")
    check(isinstance(sel.items[1].expr, A.Aggregate), "detects aggregate")
    check(sel.items[1].alias == "n", "captures aggregate alias")
    check(isinstance(sel.where, A.BinOp) and sel.where.op == "and",
          "parses compound WHERE as AND")
    check(len(sel.group_by) == 1, "parses GROUP BY")
    check(sel.order_by[0].descending and sel.limit == 10,
          "parses ORDER BY DESC and LIMIT")

    j = parse("SELECT * FROM a JOIN b ON a.x = b.y")
    check(j.join is not None and j.join.table == "b", "parses JOIN clause")


# --- storage / persistence -------------------------------------------------
def test_storage():
    print("[storage/persistence]")
    db = Database()
    db.create_table("t", [ColumnDef("id", "int"), ColumnDef("name", "text")])
    db.get_table("t").insert({"id": "1", "name": "x"})  # coercion from str
    check(db.get_table("t").rows[0]["id"] == 1, "coerces value to int type")

    path = os.path.join(tempfile.gettempdir(), "minidb_test.db")
    if os.path.exists(path):
        os.remove(path)
    # bigger table to force multi-page write
    db.create_table("big", [ColumnDef("n", "int")])
    for i in range(2000):
        db.get_table("big").insert({"n": i})
    db.save(path)
    check(os.path.exists(path), "writes database file")
    check(os.path.getsize(path) % 4096 == 0, "file is a whole number of pages")

    db2 = Database(path)
    check(db2.get_table("t").rows == [{"id": 1, "name": "x"}],
          "reloads small table exactly")
    check(len(db2.get_table("big")) == 2000 and
          db2.get_table("big").rows[1999]["n"] == 1999,
          "reloads multi-page table exactly")
    os.remove(path)


# --- executor features -----------------------------------------------------
def rows_of(engine, sql):
    return engine.execute(sql).rows


def test_select_basic():
    print("[select: projection / where]")
    e = fresh_engine()
    r = rows_of(e, "SELECT * FROM dept;")
    check(len(r) == 3, "SELECT * returns all rows")
    check(set(r[0].keys()) == {"id", "name"}, "SELECT * projects bare columns")

    r = rows_of(e, "SELECT name FROM emp WHERE dept_id = 1;")
    check(sorted(x["name"] for x in r) == ["Alice", "Bob", "Frank"],
          "WHERE equality filter")

    r = rows_of(e, "SELECT name FROM emp WHERE salary >= 80000 AND age < 40;")
    check(sorted(x["name"] for x in r) == ["Alice", "Frank"],
          "compound WHERE (AND + comparisons)")

    r = rows_of(e, "SELECT name FROM emp WHERE dept_id = 1 OR dept_id = 3;")
    check(len(r) == 4, "WHERE with OR")


def test_order_limit():
    print("[select: order by / limit]")
    e = fresh_engine()
    r = rows_of(e, "SELECT name, salary FROM emp ORDER BY salary DESC LIMIT 3;")
    check([x["name"] for x in r] == ["Eve", "Alice", "Frank"],
          "ORDER BY DESC + LIMIT")
    r = rows_of(e, "SELECT name FROM emp ORDER BY age ASC LIMIT 2;")
    check([x["name"] for x in r] == ["Frank", "Carol"], "ORDER BY ASC")


def test_join():
    print("[select: inner join]")
    e = fresh_engine()
    r = rows_of(e,
        "SELECT emp.name AS emp_name, dept.name AS dept_name FROM emp "
        "JOIN dept ON emp.dept_id = dept.id ORDER BY emp.name;")
    check(len(r) == 6, "join produces one row per matching emp")
    # Eng has Alice, Bob, Frank
    eng = [x for x in r if x["dept_name"] == "Eng"]
    check(len(eng) == 3, "join maps dept correctly")


def test_aggregates():
    print("[select: aggregates]")
    e = fresh_engine()
    r = rows_of(e, "SELECT COUNT(*), MIN(salary), MAX(salary) FROM emp;")
    check(r[0]["COUNT(*)"] == 6, "global COUNT(*)")
    check(r[0]["MIN(salary)"] == 67000.0, "global MIN")
    check(r[0]["MAX(salary)"] == 120000.0, "global MAX")

    r = rows_of(e, "SELECT SUM(salary) AS s, AVG(age) AS a FROM emp;")
    check(abs(r[0]["s"] - 523000.0) < 1e-6, "global SUM")
    check(abs(r[0]["a"] - (32+41+29+38+45+27)/6) < 1e-6, "global AVG")

    r = rows_of(e,
        "SELECT dept_id, COUNT(*) AS n, AVG(salary) AS avg_sal "
        "FROM emp GROUP BY dept_id ORDER BY dept_id;")
    check(len(r) == 3, "GROUP BY produces one row per group")
    by_dept = {x["dept_id"]: x for x in r}
    check(by_dept[1]["n"] == 3, "GROUP BY count for dept 1")
    check(abs(by_dept[1]["avg_sal"] - (95000+82000+88000)/3) < 1e-6,
          "GROUP BY avg for dept 1")
    check(by_dept[3]["n"] == 1, "GROUP BY count for dept 3")


def test_join_groupby():
    print("[select: join + group by full pipeline]")
    e = fresh_engine()
    r = rows_of(e,
        "SELECT dept.name, COUNT(*) AS n, SUM(emp.salary) AS payroll "
        "FROM emp JOIN dept ON emp.dept_id = dept.id "
        "GROUP BY dept.name ORDER BY payroll DESC;")
    check(len(r) == 3, "join+group yields 3 dept groups")
    check(r[0]["payroll"] >= r[1]["payroll"] >= r[2]["payroll"],
          "ORDER BY payroll DESC on aggregate output")
    eng = [x for x in r if x["name"] == "Eng"][0]
    check(eng["n"] == 3 and abs(eng["payroll"] - 265000.0) < 1e-6,
          "Eng payroll = 95000+82000+88000")


def test_empty_and_edge():
    print("[edge cases]")
    e = fresh_engine()
    r = rows_of(e, "SELECT name FROM emp WHERE dept_id = 99;")
    check(r == [], "empty result set when nothing matches")
    r = rows_of(e, "SELECT COUNT(*) FROM emp WHERE dept_id = 99;")
    check(r[0]["COUNT(*)"] == 0, "COUNT(*) is 0 over empty filter")


def main():
    test_tokenizer()
    test_parser()
    test_storage()
    test_select_basic()
    test_order_limit()
    test_join()
    test_aggregates()
    test_join_groupby()
    test_empty_and_edge()

    print("\n" + "=" * 50)
    print("RESULTS: %d passed, %d failed" % (PASS, FAIL))
    print("=" * 50)
    if FAIL:
        raise SystemExit(1)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
