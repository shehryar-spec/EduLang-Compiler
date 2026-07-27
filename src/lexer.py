# ============================================================
# EduLang Compiler - Lexical Analyzer
# ============================================================



OPERATORS   = {'+', '-', '*', '/'}
COMPARISONS = {'==', '!=', '<=', '>=', '<', '>'}
DELIMITERS  = {'(', ')', '{', '}', ';', ','}


class Token:
    def __init__(self, type_, value, line):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line})"


class LexicalError:
    def __init__(self, message, line):
        self.message = message
        self.line    = line

    def __repr__(self):
        return f"Lexical Error at line {self.line}: {self.message}"


class Lexer:
    def __init__(self, source_code):
        self.source = source_code
        self.tokens = []
        self.errors = []

    def tokenize(self):
        src      = self.source
        i        = 0
        line_num = 1

        while i < len(src):

            # ── Newline ──────────────────────────────────────
            if src[i] == '\n':
                line_num += 1
                i += 1
                continue

            # ── Whitespace ───────────────────────────────────
            if src[i] in (' ', '\t', '\r'):
                i += 1
                continue

            # ── Single-line comment ──────────────────────────
            if src[i:i+2] == '//':
                while i < len(src) and src[i] != '\n':
                    i += 1
                continue

            # ── String literal ───────────────────────────────
            if src[i] == '"':
                start_line = line_num
                j = i + 1
                while j < len(src) and src[j] != '"' and src[j] != '\n':
                    j += 1
                if j >= len(src) or src[j] == '\n':
                    bad = src[i:j]
                    self.errors.append(LexicalError(
                        f"Unterminated string literal: {bad}", start_line))
                    i = j
                else:
                    self.tokens.append(Token('STRING', src[i:j+1], start_line))
                    i = j + 1
                continue

            # ── Two-char operators ───────────────────────────
            if src[i:i+2] in ('==', '!=', '<=', '>='):
                self.tokens.append(Token('COMPARISON', src[i:i+2], line_num))
                i += 2
                continue

            # ── Single-char comparison ───────────────────────
            if src[i] in ('<', '>'):
                self.tokens.append(Token('COMPARISON', src[i], line_num))
                i += 1
                continue

            # ── Assignment / equals ──────────────────────────
            if src[i] == '=':
                if i + 1 < len(src) and src[i+1] == '=':
                    self.tokens.append(Token('COMPARISON', '==', line_num))
                    i += 2
                else:
                    self.tokens.append(Token('ASSIGN', '=', line_num))
                    i += 1
                continue

            # ── Arithmetic operators ─────────────────────────
            if src[i] in OPERATORS:
                self.tokens.append(Token('OPERATOR', src[i], line_num))
                i += 1
                continue

            # ── Delimiters ───────────────────────────────────
            if src[i] in DELIMITERS:
                self.tokens.append(Token('DELIMITER', src[i], line_num))
                i += 1
                continue

            # ── Number ───────────────────────────────────────
            if src[i].isdigit():
                j = i
                while j < len(src) and src[j].isdigit():
                    j += 1

                # float check
                if j < len(src) and src[j] == '.':
                    j += 1
                    if j < len(src) and src[j].isdigit():
                        while j < len(src) and src[j].isdigit():
                            j += 1
                        self.tokens.append(Token('FLOAT', src[i:j], line_num))
                    else:
                        self.errors.append(LexicalError(
                            f"Invalid numeric format: '{src[i:j]}'", line_num))
                    i = j
                    continue

                # digit followed by letter → invalid identifier like 2x
                if j < len(src) and (src[j].isalpha() or src[j] == '_'):
                    k = j
                    while k < len(src) and (src[k].isalnum() or src[k] == '_'):
                        k += 1
                    bad = src[i:k]
                    self.errors.append(LexicalError(
                        f"Invalid identifier '{bad}' "
                        f"(identifier cannot start with a digit)", line_num))
                    i = k
                    continue

                self.tokens.append(Token('INTEGER', src[i:j], line_num))
                i = j
                continue

            # ── Identifier / Keyword ─────────────────────────
            if src[i].isalpha() or src[i] == '_':
                j = i
                while j < len(src) and (src[j].isalnum() or src[j] == '_'):
                    j += 1
                word = src[i:j]
                kind = 'KEYWORD' if word in KEYWORDS else 'IDENTIFIER'
                self.tokens.append(Token(kind, word, line_num))
                i = j
                continue

            # ── Unknown character ─────────────────────────────
            self.errors.append(LexicalError(
                f"Invalid character '{src[i]}'", line_num))
            i += 1

        return self.tokens, self.errors