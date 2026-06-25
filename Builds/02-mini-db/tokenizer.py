"""
tokenizer.py
============
Lexical analysis for the mini SQL engine.

Converts a raw SQL string into a flat list of `Token` objects. The tokenizer
is intentionally simple: it recognizes keywords, identifiers, numeric and
string literals, operators and punctuation, and skips whitespace.

The parser consumes this token stream to build an AST.
"""

from dataclasses import dataclass


# --- Token kinds -----------------------------------------------------------
KEYWORD = "KEYWORD"
IDENT = "IDENT"
NUMBER = "NUMBER"
STRING = "STRING"
OPERATOR = "OPERATOR"
PUNCT = "PUNCT"
STAR = "STAR"
EOF = "EOF"

# SQL keywords we understand (matched case-insensitively).
KEYWORDS = {
    "create", "table", "insert", "into", "values", "select", "from",
    "where", "order", "by", "limit", "asc", "desc", "and", "or",
    "join", "inner", "on", "group", "as",
    "int", "integer", "text", "string", "float", "real",
    "count", "sum", "avg", "min", "max",
    "true", "false", "null",
}

# Multi-character operators must be tried before single-character ones.
TWO_CHAR_OPS = {"<=", ">=", "!=", "<>", "=="}
ONE_CHAR_OPS = {"=", "<", ">", "+", "-", "*", "/"}


@dataclass
class Token:
    kind: str
    value: str
    pos: int  # character offset, useful for error messages

    def __repr__(self):
        return "Token({}, {!r})".format(self.kind, self.value)


class TokenizeError(Exception):
    pass


def tokenize(sql):
    """Return a list of Token, terminated by an EOF token."""
    tokens = []
    i = 0
    n = len(sql)

    while i < n:
        c = sql[i]

        # Whitespace ----------------------------------------------------
        if c.isspace():
            i += 1
            continue

        # Line comments -------------------------------------------------
        if c == "-" and i + 1 < n and sql[i + 1] == "-":
            while i < n and sql[i] != "\n":
                i += 1
            continue

        # String literal (single quotes) -------------------------------
        if c == "'":
            j = i + 1
            buf = []
            while j < n:
                if sql[j] == "'":
                    # support '' as an escaped quote
                    if j + 1 < n and sql[j + 1] == "'":
                        buf.append("'")
                        j += 2
                        continue
                    break
                buf.append(sql[j])
                j += 1
            if j >= n:
                raise TokenizeError("Unterminated string literal at pos %d" % i)
            tokens.append(Token(STRING, "".join(buf), i))
            i = j + 1
            continue

        # Number literal (int or float) --------------------------------
        if c.isdigit() or (c == "." and i + 1 < n and sql[i + 1].isdigit()):
            j = i
            seen_dot = False
            while j < n and (sql[j].isdigit() or sql[j] == "."):
                if sql[j] == ".":
                    if seen_dot:
                        break
                    seen_dot = True
                j += 1
            tokens.append(Token(NUMBER, sql[i:j], i))
            i = j
            continue

        # Identifier / keyword -----------------------------------------
        if c.isalpha() or c == "_":
            j = i
            while j < n and (sql[j].isalnum() or sql[j] == "_"):
                j += 1
            word = sql[i:j]
            low = word.lower()
            if low in KEYWORDS:
                tokens.append(Token(KEYWORD, low, i))
            else:
                tokens.append(Token(IDENT, word, i))
            i = j
            continue

        # Two-char operators -------------------------------------------
        two = sql[i:i + 2]
        if two in TWO_CHAR_OPS:
            tokens.append(Token(OPERATOR, two, i))
            i += 2
            continue

        # Single-char operators / punctuation --------------------------
        if c == "*":
            tokens.append(Token(STAR, "*", i))
            i += 1
            continue
        if c in ONE_CHAR_OPS:
            tokens.append(Token(OPERATOR, c, i))
            i += 1
            continue
        if c in "(),.;":
            tokens.append(Token(PUNCT, c, i))
            i += 1
            continue

        raise TokenizeError("Unexpected character %r at pos %d" % (c, i))

    tokens.append(Token(EOF, "", n))
    return tokens


if __name__ == "__main__":
    import sys
    src = " ".join(sys.argv[1:]) or "SELECT a, COUNT(*) FROM t WHERE x >= 3;"
    for t in tokenize(src):
        print(t)
