# ============================================================
# EduLang Compiler - Recursive Descent Parser
# ============================================================

from lexer import Token


class SyntaxError_(Exception):
    pass


class ParseError:
    def __init__(self, message, line):
        self.message = message
        self.line    = line

    def __repr__(self):
        return f"Syntax Error at line {self.line}: {self.message}"


# ── AST Nodes ─────────────────────────────────────────────────

class ProgramNode:
    def __init__(self, functions):
        self.functions = functions

class FunctionNode:
    def __init__(self, return_type, name, body, line):
        self.return_type = return_type
        self.name        = name
        self.body        = body
        self.line        = line

class DeclNode:
    def __init__(self, var_type, name, init_expr, line):
        self.var_type  = var_type
        self.name      = name
        self.init_expr = init_expr
        self.line      = line

class AssignNode:
    def __init__(self, name, expr, line):
        self.name = name
        self.expr = expr
        self.line = line

class IfNode:
    def __init__(self, condition, then_body, else_body, line):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
        self.line      = line

class WhileNode:
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body      = body
        self.line      = line

class ForNode:
    def __init__(self, init, condition, update, body, line):
        self.init      = init
        self.condition = condition
        self.update    = update
        self.body      = body
        self.line      = line

class ReturnNode:
    def __init__(self, expr, line):
        self.expr = expr
        self.line = line

class BinOpNode:
    def __init__(self, op, left, right, line):
        self.op    = op
        self.left  = left
        self.right = right
        self.line  = line

class NumberNode:
    def __init__(self, value, line):
        self.value = value
        self.line  = line

class IdentifierNode:
    def __init__(self, name, line):
        self.name = name
        self.line = line

class StringNode:
    def __init__(self, value, line):
        self.value = value
        self.line  = line


# ── Parser ────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0
        self.errors = []

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', '', 0)

    def advance(self):
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, type_=None, value=None):
        tok = self.current()
        if type_ and tok.type != type_:
            line = tok.line if tok.type != 'EOF' else self._last_line()
            msg  = f"Expected {type_} '{value or ''}' but got '{tok.value}'"
            self.errors.append(ParseError(msg, line))
            raise SyntaxError_(msg)
        if value and tok.value != value:
            line = tok.line
            msg  = f"Expected '{value}' but got '{tok.value}'"
            self.errors.append(ParseError(msg, line))
            raise SyntaxError_(msg)
        return self.advance()

    def expect_semicolon(self):
        tok = self.current()
        if tok.type == 'DELIMITER' and tok.value == ';':
            return self.advance()
        line = tok.line if tok.type != 'EOF' else self._last_line()
        self.errors.append(ParseError("Missing semicolon ';'", line))
        raise SyntaxError_("Missing semicolon")

    def match(self, type_=None, value=None):
        tok = self.current()
        if type_ and tok.type != type_:
            return False
        if value and tok.value != value:
            return False
        return True

    def _last_line(self):
        return self.tokens[-1].line if self.tokens else 0

    def is_type_kw(self):
        return (self.current().type == 'KEYWORD' and
                self.current().value in ('int', 'float', 'string'))

    # ── Entry ─────────────────────────────────────────────────
    def parse(self):
        try:
            ast = self.parse_program()
        except SyntaxError_:
            ast = None
        return ast, self.errors

    def parse_program(self):
        funcs = []
        while self.current().type != 'EOF':
            try:
                funcs.append(self.parse_function())
            except SyntaxError_:
                while (self.current().type != 'EOF' and
                       not self.match('DELIMITER', '}')):
                    self.advance()
                if self.current().type != 'EOF':
                    self.advance()
        return ProgramNode(funcs)

    def parse_function(self):
        line     = self.current().line
        ret      = self.expect('KEYWORD')
        name_tok = self.expect('IDENTIFIER')
        self.expect('DELIMITER', '(')
        self.expect('DELIMITER', ')')
        self.expect('DELIMITER', '{')
        body = self.parse_stmt_list()
        self.expect('DELIMITER', '}')
        return FunctionNode(ret.value, name_tok.value, body, line)

    def parse_stmt_list(self):
        stmts = []
        while not (self.match('DELIMITER', '}') or
                   self.current().type == 'EOF'):
            try:
                stmts.append(self.parse_stmt())
            except SyntaxError_:
                while (self.current().type != 'EOF' and
                       not self.match('DELIMITER', ';') and
                       not self.match('DELIMITER', '}')):
                    self.advance()
                if self.match('DELIMITER', ';'):
                    self.advance()
        return stmts

    def parse_stmt(self):
        tok = self.current()

        if self.is_type_kw():
            return self.parse_decl()
        if tok.type == 'KEYWORD' and tok.value == 'if':
            return self.parse_if()
        if tok.type == 'KEYWORD' and tok.value == 'while':
            return self.parse_while()
        if tok.type == 'KEYWORD' and tok.value == 'for':
            return self.parse_for()
        if tok.type == 'KEYWORD' and tok.value == 'return':
            return self.parse_return()
        if tok.type == 'IDENTIFIER':
            return self.parse_assign()

        line = tok.line
        self.errors.append(ParseError(f"Unexpected token '{tok.value}'", line))
        self.advance()
        raise SyntaxError_(f"Unexpected token '{tok.value}'")

    # ── Declaration ───────────────────────────────────────────
    def parse_decl(self):
        line     = self.current().line
        var_type = self.advance().value
        name_tok = self.expect('IDENTIFIER')
        init     = None
        if self.match('ASSIGN', '='):
            self.advance()
            init = self.parse_expr()
        self.expect_semicolon()
        return DeclNode(var_type, name_tok.value, init, line)

    # ── Assignment ────────────────────────────────────────────
    def parse_assign(self):
        line     = self.current().line
        name_tok = self.expect('IDENTIFIER')
        self.expect('ASSIGN', '=')
        expr = self.parse_expr()
        self.expect_semicolon()
        return AssignNode(name_tok.value, expr, line)

    # ── If-Else ───────────────────────────────────────────────
    def parse_if(self):
        line = self.current().line
        self.expect('KEYWORD', 'if')
        self.expect('DELIMITER', '(')
        cond = self.parse_cond()
        self.expect('DELIMITER', ')')
        self.expect('DELIMITER', '{')
        then_b = self.parse_stmt_list()
        self.expect('DELIMITER', '}')
        else_b = []
        if self.match('KEYWORD', 'else'):
            self.advance()
            self.expect('DELIMITER', '{')
            else_b = self.parse_stmt_list()
            self.expect('DELIMITER', '}')
        return IfNode(cond, then_b, else_b, line)

    # ── While ─────────────────────────────────────────────────
    def parse_while(self):
        line = self.current().line
        self.expect('KEYWORD', 'while')
        self.expect('DELIMITER', '(')
        cond = self.parse_cond()
        self.expect('DELIMITER', ')')
        self.expect('DELIMITER', '{')
        body = self.parse_stmt_list()
        self.expect('DELIMITER', '}')
        return WhileNode(cond, body, line)

    # ── For ───────────────────────────────────────────────────
    def parse_for(self):
        line = self.current().line
        self.expect('KEYWORD', 'for')

        tok = self.current()
        if not (tok.type == 'DELIMITER' and tok.value == '('):
            self.errors.append(ParseError("Missing '(' after 'for'", tok.line))
            raise SyntaxError_("Missing '('")
        self.advance()

        # init
        init = self._for_init()

        # condition
        cond = self.parse_cond()

        # semicolon after condition
        tok = self.current()
        if not (tok.type == 'DELIMITER' and tok.value == ';'):
            self.errors.append(
                ParseError("Missing semicolon in for loop", tok.line))
            raise SyntaxError_("Missing semicolon in for loop")
        self.advance()

        # update
        update = self._for_update()

        tok = self.current()
        if not (tok.type == 'DELIMITER' and tok.value == ')'):
            self.errors.append(
                ParseError("Missing ')' in for loop", tok.line))
            raise SyntaxError_("Missing ')'")
        self.advance()

        self.expect('DELIMITER', '{')
        body = self.parse_stmt_list()
        self.expect('DELIMITER', '}')
        return ForNode(init, cond, update, body, line)

    def _for_init(self):
        line = self.current().line
        if self.is_type_kw():
            var_type = self.advance().value
            name_tok = self.expect('IDENTIFIER')
            self.expect('ASSIGN', '=')
            expr = self.parse_expr()
            tok  = self.current()
            if not (tok.type == 'DELIMITER' and tok.value == ';'):
                self.errors.append(
                    ParseError("Missing semicolon in for loop initializer",
                               tok.line))
                raise SyntaxError_("Missing semicolon in for init")
            self.advance()
            return DeclNode(var_type, name_tok.value, expr, line)
        else:
            name_tok = self.expect('IDENTIFIER')
            self.expect('ASSIGN', '=')
            expr = self.parse_expr()
            tok  = self.current()
            if not (tok.type == 'DELIMITER' and tok.value == ';'):
                self.errors.append(
                    ParseError("Missing semicolon in for loop initializer",
                               tok.line))
                raise SyntaxError_("Missing semicolon in for init")
            self.advance()
            return AssignNode(name_tok.value, expr, line)

    def _for_update(self):
        line     = self.current().line
        name_tok = self.expect('IDENTIFIER')
        self.expect('ASSIGN', '=')
        expr = self.parse_expr()
        return AssignNode(name_tok.value, expr, line)

    # ── Return ────────────────────────────────────────────────
    def parse_return(self):
        line = self.current().line
        self.expect('KEYWORD', 'return')
        expr = None
        if not self.match('DELIMITER', ';'):
            expr = self.parse_expr()
        self.expect_semicolon()
        return ReturnNode(expr, line)

    # ── Condition ─────────────────────────────────────────────
    def parse_cond(self):
        line = self.current().line
        left = self.parse_expr()
        if self.current().type == 'COMPARISON':
            op    = self.advance().value
            right = self.parse_expr()
            return BinOpNode(op, left, right, line)
        return left

    # ── Expression (precedence: additive > multiplicative) ────
    def parse_expr(self):
        return self.parse_additive()

    def parse_additive(self):
        line = self.current().line
        node = self.parse_term()
        while (self.current().type == 'OPERATOR' and
               self.current().value in ('+', '-')):
            op   = self.advance().value
            rhs  = self.parse_term()
            node = BinOpNode(op, node, rhs, line)
        return node

    def parse_term(self):
        line = self.current().line
        node = self.parse_factor()
        while (self.current().type == 'OPERATOR' and
               self.current().value in ('*', '/')):
            op   = self.advance().value
            rhs  = self.parse_factor()
            node = BinOpNode(op, node, rhs, line)
        return node

    def parse_factor(self):
        tok  = self.current()
        line = tok.line

        if tok.type == 'INTEGER':
            self.advance()
            return NumberNode(int(tok.value), line)
        if tok.type == 'FLOAT':
            self.advance()
            return NumberNode(float(tok.value), line)
        if tok.type == 'STRING':
            self.advance()
            return StringNode(tok.value, line)
        if tok.type == 'IDENTIFIER':
            self.advance()
            return IdentifierNode(tok.value, line)
        if tok.type == 'DELIMITER' and tok.value == '(':
            self.advance()
            expr = self.parse_expr()
            self.expect('DELIMITER', ')')
            return expr

        self.errors.append(
            ParseError(f"Unexpected token '{tok.value}' in expression", line))
        raise SyntaxError_(f"Unexpected in expression: {tok.value}")