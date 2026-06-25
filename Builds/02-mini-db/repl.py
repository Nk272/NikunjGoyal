"""
repl.py
=======
Interactive read-eval-print loop for the mini DB.

Usage:
    python3 repl.py [database_file]

If a database file is given it is opened (and created on .save).  Meta-commands
start with a backslash:

    \\help            show help
    \\tables          list tables
    \\schema <name>   show a table's columns
    \\explain <sql>   show the physical plan for a SELECT
    \\save [path]     persist the database to disk
    \\quit            exit

Plain SQL statements are executed directly. End a statement with ';' or just
press enter on a complete line.
"""

import sys

from engine import Engine
from parser import parse
import planner


HELP = __doc__


def run(path=None):
    engine = Engine(path)
    print("mini-db REPL. Type \\help for help, \\quit to exit.")
    if path:
        print("Opened database file: %s" % path)

    buffer = ""
    while True:
        prompt = "minidb> " if not buffer else "    ...> "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        stripped = line.strip()

        # meta-commands (only when not mid-statement)
        if not buffer and stripped.startswith("\\"):
            if not _meta(engine, stripped):
                break
            continue

        buffer += line + "\n"
        if ";" not in buffer:
            continue

        sql = buffer.strip()
        buffer = ""
        try:
            result = engine.execute(sql)
            print(result.render())
        except Exception as e:
            print("Error: %s" % e)


def _meta(engine, cmd):
    """Handle a meta-command. Return False to quit."""
    parts = cmd.split(None, 1)
    name = parts[0]
    arg = parts[1].strip() if len(parts) > 1 else ""

    if name in ("\\quit", "\\q", "\\exit"):
        return False
    if name in ("\\help", "\\h", "\\?"):
        print(HELP)
    elif name == "\\tables":
        names = list(engine.db.tables.keys())
        print("\n".join(names) if names else "(no tables)")
    elif name == "\\schema":
        try:
            t = engine.db.get_table(arg)
            for c in t.columns:
                print("  %-16s %s" % (c, t.types[c]))
        except Exception as e:
            print("Error: %s" % e)
    elif name == "\\explain":
        try:
            stmt = parse(arg)
            op = planner.plan_select(stmt, engine.db)
            print(planner.explain(op))
        except Exception as e:
            print("Error: %s" % e)
    elif name in ("\\save", "\\w"):
        try:
            engine.save(arg or None)
            print("saved to %s" % (arg or engine.db.path))
        except Exception as e:
            print("Error: %s" % e)
    else:
        print("Unknown command: %s (try \\help)" % name)
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    run(path)
