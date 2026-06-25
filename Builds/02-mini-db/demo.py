"""
demo.py
=======
End-to-end demonstration of the mini DB engine.

Creates two tables (employees, departments), loads sample data, then runs a
series of queries exercising every supported feature:

  1. SELECT *                         (full scan + projection)
  2. projection + WHERE               (Filter)
  3. WHERE with AND / comparison      (compound predicate)
  4. ORDER BY ... DESC + LIMIT        (Sort + Limit)
  5. INNER JOIN                       (HashJoin)
  6. aggregates without GROUP BY      (global Aggregate)
  7. GROUP BY + COUNT/AVG             (grouped Aggregate)
  8. JOIN + GROUP BY + ORDER BY       (full pipeline)

It also shows EXPLAIN output for one query and round-trips the database
through the on-disk page format.
"""

import os

from engine import Engine
from parser import parse
import planner


SCHEMA = """
CREATE TABLE employees (
    id     INT,
    name   TEXT,
    dept_id INT,
    salary FLOAT,
    age    INT
);
CREATE TABLE departments (
    id   INT,
    name TEXT,
    city TEXT
);
"""

DATA = """
INSERT INTO departments (id, name, city) VALUES
    (1, 'Engineering', 'Bangalore'),
    (2, 'Sales',       'Mumbai'),
    (3, 'Research',    'Pune');

INSERT INTO employees (id, name, dept_id, salary, age) VALUES
    (1, 'Alice',   1, 95000.0, 32),
    (2, 'Bob',     1, 82000.0, 41),
    (3, 'Carol',   2, 71000.0, 29),
    (4, 'Dave',    2, 67000.0, 38),
    (5, 'Eve',     3, 120000.0, 45),
    (6, 'Frank',   1, 88000.0, 27),
    (7, 'Grace',   3, 105000.0, 51),
    (8, 'Heidi',   2, 60000.0, 24);
"""

QUERIES = [
    ("1. All departments (SELECT *)",
     "SELECT * FROM departments;"),

    ("2. Projection + WHERE",
     "SELECT name, salary FROM employees WHERE dept_id = 1;"),

    ("3. Compound WHERE (AND + comparisons)",
     "SELECT name, age, salary FROM employees "
     "WHERE salary >= 80000 AND age < 40;"),

    ("4. ORDER BY salary DESC, LIMIT 3",
     "SELECT name, salary FROM employees ORDER BY salary DESC LIMIT 3;"),

    ("5. INNER JOIN employees x departments",
     "SELECT employees.name AS emp_name, departments.name AS dept_name, "
     "departments.city FROM employees "
     "JOIN departments ON employees.dept_id = departments.id "
     "ORDER BY employees.name;"),

    ("6. Global aggregates (no GROUP BY)",
     "SELECT COUNT(*), AVG(salary), MIN(salary), MAX(salary) FROM employees;"),

    ("7. GROUP BY dept_id with COUNT and AVG",
     "SELECT dept_id, COUNT(*) AS headcount, AVG(salary) AS avg_salary "
     "FROM employees GROUP BY dept_id ORDER BY dept_id;"),

    ("8. JOIN + GROUP BY + ORDER BY (full pipeline)",
     "SELECT departments.name, COUNT(*) AS n, SUM(employees.salary) AS payroll "
     "FROM employees JOIN departments ON employees.dept_id = departments.id "
     "GROUP BY departments.name ORDER BY payroll DESC;"),
]


def main():
    engine = Engine()
    engine.execute_script(SCHEMA)
    engine.execute_script(DATA)

    print("=" * 70)
    print("MINI DB ENGINE — DEMO")
    print("=" * 70)

    for title, sql in QUERIES:
        print("\n" + title)
        print("SQL: " + " ".join(sql.split()))
        print("-" * 70)
        result = engine.execute(sql)
        print(result.render())

    # EXPLAIN demonstration -------------------------------------------------
    print("\n" + "=" * 70)
    print("EXPLAIN for query 8 (physical operator tree):")
    print("-" * 70)
    stmt = parse(QUERIES[7][1])
    op = planner.plan_select(stmt, engine.db)
    print(planner.explain(op))

    # Persistence round-trip ------------------------------------------------
    print("\n" + "=" * 70)
    print("PERSISTENCE: save to page-based file and reload")
    print("-" * 70)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "demo.minidb")
    engine.save(db_path)
    size = os.path.getsize(db_path)
    print("Wrote %s (%d bytes, %d pages)" % (db_path, size, size // 4096))

    reopened = Engine(db_path)
    res = reopened.execute(
        "SELECT name, salary FROM employees ORDER BY salary DESC LIMIT 2;")
    print("Reloaded and queried top-2 earners:")
    print(res.render())


if __name__ == "__main__":
    main()
