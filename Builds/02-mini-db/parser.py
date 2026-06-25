"""
parser.py
=========
Recursive-descent parser. Consumes the token stream from tokenizer.py and
produces an AST (see ast_nodes.py).

Grammar (informal):

  statement   := create | insert | select
  create      := CREATE TABLE ident '(' coldef (',' coldef)* ')'
  coldef      := ident type
  insert      := INSERT INTO ident ['(' ident (',' ident)* ')']
                 VALUES rowlist
  rowlist     := row (',' row)*
  row         := '(' literal (',' literal)* ')'
  select      := SELECT projlist FROM ident [alias]
                 [join] [WHERE expr] [GROUP BY collist]
                 [ORDER BY orderlist] [LIMIT number]
  projlist    := '*' | selitem (',' selitem)*
  selitem     := (aggregate | column) [AS ident]
  expr        := or_expr
  or_expr     := and_expr (OR and_expr)*
  and_expr    := cmp_expr (AND cmp_expr)*
  cmp_expr    := primary (cmpop primary)?
  primary     := column | literal | '(' expr ')'
"""

from tokenizer import (
    tokenize, KEYWORD, IDENT, NUMBER, STRING, OPERATOR, PUNCT, STAR, EOF,
)
import ast_nodes as A


class ParseError(Exception):
    pass


# Type keyword -> canonical storage type.
TYPE_MAP = {
    "int": "int", "integer": "int",
    "float": "float", "real": "float",
    "text": "text", "string": "text",
}

COMPARISON_OPS = {"=", "==", "!=", "<>", "<", ">", "<=", ">="}
AGG_FUNCS = {"count", "sum", "avg", "min", "max"}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    # --- token helpers ----------------------------------------------------
    def peek(self):
        return self.tokens[self.i]

    def advance(self):
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def at_end(self):
        return self.peek().kind == EOF

    def check(self, kind, value=None):
        tok = self.peek()
        if tok.kind != kind:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def check_kw(self, *words):
        tok = self.peek()
        return tok.kind == KEYWORD and tok.value in words

    def match_kw(self, word):
        if self.check(KEYWORD, word):
            self.advance()
            return True
        return False

    def expect(self, kind, value=None):
        tok = self.peek()
        if tok.kind != kind or (value is not None and tok.value != value):
            want = value if value is not None else kind
            raise ParseError(
                "Expected %r but got %r at pos %d" % (want, tok.value, tok.pos))
        return self.advance()

    def expect_kw(self, word):
        if not self.match_kw(word):
            tok = self.peek()
            raise ParseError(
                "Expected keyword %r but got %r at pos %d"
                % (word, tok.value, tok.pos))

    # --- entry point ------------------------------------------------------
    def parse_statement(self):
        if self.check_kw("create"):
            stmt = self.parse_create()
        elif self.check_kw("insert"):
            stmt = self.parse_insert()
        elif self.check_kw("select"):
            stmt = self.parse_select()
        else:
            tok = self.peek()
            raise ParseError("Unknown statement starting at %r" % tok.value)
        # optional trailing semicolon
        if self.check(PUNCT, ";"):
            self.advance()
        return stmt

    # --- CREATE TABLE -----------------------------------------------------
    def parse_create(self):
        self.expect_kw("create")
        self.expect_kw("table")
        name = self.expect(IDENT).value
        self.expect(PUNCT, "(")
        cols = []
        while True:
            col_name = self.expect(IDENT).value
            type_tok = self.peek()
            if type_tok.kind != KEYWORD or type_tok.value not in TYPE_MAP:
                raise ParseError("Expected column type, got %r" % type_tok.value)
            self.advance()
            cols.append(A.ColumnDef(col_name, TYPE_MAP[type_tok.value]))
            if self.check(PUNCT, ","):
                self.advance()
                continue
            break
        self.expect(PUNCT, ")")
        return A.CreateTable(name, cols)

    # --- INSERT -----------------------------------------------------------
    def parse_insert(self):
        self.expect_kw("insert")
        self.expect_kw("into")
        name = self.expect(IDENT).value
        columns = None
        if self.check(PUNCT, "("):
            self.advance()
            columns = []
            while True:
                columns.append(self.expect(IDENT).value)
                if self.check(PUNCT, ","):
                    self.advance()
                    continue
                break
            self.expect(PUNCT, ")")
        self.expect_kw("values")
        rows = []
        while True:
            self.expect(PUNCT, "(")
            row = []
            while True:
                row.append(self.parse_literal())
                if self.check(PUNCT, ","):
                    self.advance()
                    continue
                break
            self.expect(PUNCT, ")")
            rows.append(row)
            if self.check(PUNCT, ","):
                self.advance()
                continue
            break
        return A.Insert(name, columns, rows)

    # --- SELECT -----------------------------------------------------------
    def parse_select(self):
        self.expect_kw("select")
        items = self.parse_projection()
        self.expect_kw("from")
        from_table = self.expect(IDENT).value
        from_alias = None
        # optional alias: FROM t AS a  or  FROM t a
        if self.match_kw("as"):
            from_alias = self.expect(IDENT).value
        elif self.check(IDENT):
            from_alias = self.advance().value

        join = None
        if self.check_kw("join", "inner"):
            join = self.parse_join()

        where = None
        if self.match_kw("where"):
            where = self.parse_expr()

        group_by = []
        if self.match_kw("group"):
            self.expect_kw("by")
            while True:
                group_by.append(self.parse_column())
                if self.check(PUNCT, ","):
                    self.advance()
                    continue
                break

        order_by = []
        if self.match_kw("order"):
            self.expect_kw("by")
            while True:
                col = self.parse_column()
                desc = False
                if self.match_kw("asc"):
                    desc = False
                elif self.match_kw("desc"):
                    desc = True
                order_by.append(A.OrderKey(col, desc))
                if self.check(PUNCT, ","):
                    self.advance()
                    continue
                break

        limit = None
        if self.match_kw("limit"):
            limit = int(self.expect(NUMBER).value)

        return A.Select(
            items=items, from_table=from_table, from_alias=from_alias,
            join=join, where=where, group_by=group_by,
            order_by=order_by, limit=limit,
        )

    def parse_projection(self):
        # bare '*'
        if self.check(STAR):
            self.advance()
            return [A.SelectItem(A.Star())]
        items = []
        while True:
            expr = self.parse_select_expr()
            alias = None
            if self.match_kw("as"):
                alias = self.expect(IDENT).value
            elif self.check(IDENT):
                # `expr name` style alias (not a keyword)
                alias = self.advance().value
            if isinstance(expr, A.Aggregate):
                expr.alias = alias
            items.append(A.SelectItem(expr, alias))
            if self.check(PUNCT, ","):
                self.advance()
                continue
            break
        return items

    def parse_select_expr(self):
        # aggregate?  count(*) / sum(col) ...
        if self.check_kw(*AGG_FUNCS):
            func = self.advance().value
            self.expect(PUNCT, "(")
            if self.check(STAR):
                self.advance()
                arg = A.Star()
            else:
                arg = self.parse_column()
            self.expect(PUNCT, ")")
            return A.Aggregate(func, arg)
        return self.parse_column()

    def parse_join(self):
        # optional INNER, then JOIN
        self.match_kw("inner")
        self.expect_kw("join")
        table = self.expect(IDENT).value
        self.expect_kw("on")
        left = self.parse_column()
        op = self.peek()
        if not (op.kind == OPERATOR and op.value in ("=", "==")):
            raise ParseError("JOIN only supports equality (=) conditions")
        self.advance()
        right = self.parse_column()
        return A.JoinClause(table, left, right)

    # --- expressions ------------------------------------------------------
    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.match_kw("or"):
            right = self.parse_and()
            left = A.BinOp("or", left, right)
        return left

    def parse_and(self):
        left = self.parse_cmp()
        while self.match_kw("and"):
            right = self.parse_cmp()
            left = A.BinOp("and", left, right)
        return left

    def parse_cmp(self):
        left = self.parse_primary()
        tok = self.peek()
        if tok.kind == OPERATOR and tok.value in COMPARISON_OPS:
            self.advance()
            right = self.parse_primary()
            return A.BinOp(tok.value, left, right)
        return left

    def parse_primary(self):
        if self.check(PUNCT, "("):
            self.advance()
            e = self.parse_expr()
            self.expect(PUNCT, ")")
            return e
        tok = self.peek()
        if tok.kind in (NUMBER, STRING) or self.check_kw("true", "false", "null"):
            return self.parse_literal()
        return self.parse_column()

    def parse_column(self):
        first = self.expect(IDENT).value
        if self.check(PUNCT, "."):
            self.advance()
            second = self.expect(IDENT).value
            return A.Column(name=second, table=first)
        return A.Column(name=first)

    def parse_literal(self):
        tok = self.peek()
        if tok.kind == NUMBER:
            self.advance()
            if "." in tok.value:
                return A.Literal(float(tok.value), "float")
            return A.Literal(int(tok.value), "int")
        if tok.kind == STRING:
            self.advance()
            return A.Literal(tok.value, "string")
        if self.check_kw("true"):
            self.advance()
            return A.Literal(True, "bool")
        if self.check_kw("false"):
            self.advance()
            return A.Literal(False, "bool")
        if self.check_kw("null"):
            self.advance()
            return A.Literal(None, "null")
        raise ParseError("Expected literal but got %r at pos %d" % (tok.value, tok.pos))


def parse(sql):
    """Parse a single SQL statement into an AST node."""
    return Parser(tokenize(sql)).parse_statement()


def parse_many(sql):
    """Parse multiple ';'-separated statements into a list of AST nodes."""
    p = Parser(tokenize(sql))
    stmts = []
    while not p.at_end():
        stmts.append(p.parse_statement())
    return stmts


if __name__ == "__main__":
    import sys
    src = " ".join(sys.argv[1:]) or "SELECT dept, COUNT(*) AS n FROM emp GROUP BY dept ORDER BY n DESC LIMIT 5"
    print(parse(src))
