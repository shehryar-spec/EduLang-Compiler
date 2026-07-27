# ============================================================
# EduLang Compiler - Semantic Analyzer
# ============================================================

from parser import (ProgramNode, FunctionNode, DeclNode, AssignNode,
                    IfNode, WhileNode, ForNode, ReturnNode,
                    BinOpNode, NumberNode, IdentifierNode, StringNode)


class SemanticError:
    def __init__(self, message, line):
        self.message = message
        self.line    = line

    def __repr__(self):
        return f"Semantic Error at line {self.line}: {self.message}"


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, var_type, line):
        if name in self.scopes[-1]:
            return False
        self.scopes[-1][name] = {'type': var_type, 'line': line}
        return True

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def all_symbols(self):
        result = {}
        for scope in self.scopes:
            result.update(scope)
        return result


NUMERIC = {'int', 'float'}


def get_type(node, sym):
    if isinstance(node, NumberNode):
        return 'float' if isinstance(node.value, float) else 'int'
    if isinstance(node, StringNode):
        return 'string'
    if isinstance(node, IdentifierNode):
        info = sym.lookup(node.name)
        return info['type'] if info else 'unknown'
    if isinstance(node, BinOpNode):
        lt = get_type(node.left,  sym)
        rt = get_type(node.right, sym)
        if lt == 'float' or rt == 'float':
            return 'float'
        if lt == 'int' and rt == 'int':
            return 'int'
        return 'unknown'
    return 'unknown'


class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast       = ast
        self.errors    = []
        self.sym       = SymbolTable()
        self.fn_return = None

    def analyze(self):
        if self.ast is None:
            return self.errors, self.sym
        for fn in self.ast.functions:
            self.visit_fn(fn)
        return self.errors, self.sym

    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        method = getattr(self, method_name, None)
        if method:
            method(node)

    def visit_fn(self, node):
        self.fn_return = node.return_type
        self.sym.push_scope()
        for s in node.body:
            self.visit(s)
        self.sym.pop_scope()

    # ── Statements ────────────────────────────────────────────

    def visit_DeclNode(self, node):
        if node.init_expr is not None:
            self._check_declared(node.init_expr)
            it = get_type(node.init_expr, self.sym)
            if it != 'unknown':
                if node.var_type in NUMERIC and it == 'string':
                    self.errors.append(SemanticError(
                        f"Type mismatch: cannot assign 'string' to "
                        f"'{node.var_type}' variable '{node.name}'",
                        node.line))
                if node.var_type == 'string' and it in NUMERIC:
                    self.errors.append(SemanticError(
                        f"Type mismatch: cannot assign '{it}' to "
                        f"'string' variable '{node.name}'",
                        node.line))
        if not self.sym.declare(node.name, node.var_type, node.line):
            self.errors.append(SemanticError(
                f"Variable '{node.name}' already declared in this scope",
                node.line))

    def visit_AssignNode(self, node):
        info = self.sym.lookup(node.name)
        if info is None:
            self.errors.append(SemanticError(
                f"Undeclared variable '{node.name}'",
                node.line))
            return
        self._check_declared(node.expr)
        et = get_type(node.expr, self.sym)
        if et != 'unknown':
            if info['type'] in NUMERIC and et == 'string':
                self.errors.append(SemanticError(
                    f"Type mismatch: cannot assign 'string' to "
                    f"'{info['type']}' variable '{node.name}'",
                    node.line))
            if info['type'] == 'string' and et in NUMERIC:
                self.errors.append(SemanticError(
                    f"Type mismatch: cannot assign '{et}' to "
                    f"'string' variable '{node.name}'",
                    node.line))

    def visit_IfNode(self, node):
        self._check_cond(node.condition)
        self.sym.push_scope()
        for s in node.then_body:
            self.visit(s)
        self.sym.pop_scope()
        if node.else_body:
            self.sym.push_scope()
            for s in node.else_body:
                self.visit(s)
            self.sym.pop_scope()

    def visit_WhileNode(self, node):
        self._check_cond(node.condition)
        self.sym.push_scope()
        for s in node.body:
            self.visit(s)
        self.sym.pop_scope()

    def visit_ForNode(self, node):
        self.sym.push_scope()
        self.visit(node.init)
        self._check_cond(node.condition)
        self.visit(node.update)
        for s in node.body:
            self.visit(s)
        self.sym.pop_scope()

    def visit_ReturnNode(self, node):
        if node.expr is None:
            return
        self._check_declared(node.expr)
        rt = get_type(node.expr, self.sym)
        if rt != 'unknown' and self.fn_return:
            if self.fn_return in NUMERIC and rt == 'string':
                self.errors.append(SemanticError(
                    f"Wrong return type: expected '{self.fn_return}' "
                    f"but got 'string'",
                    node.line))
            if self.fn_return == 'string' and rt in NUMERIC:
                self.errors.append(SemanticError(
                    f"Wrong return type: expected 'string' "
                    f"but got '{rt}'",
                    node.line))

    # ── Helpers ───────────────────────────────────────────────

    def _check_declared(self, node):
        if isinstance(node, IdentifierNode):
            if self.sym.lookup(node.name) is None:
                self.errors.append(SemanticError(
                    f"Variable '{node.name}' is not declared",
                    node.line))
        elif isinstance(node, BinOpNode):
            self._check_declared(node.left)
            self._check_declared(node.right)

    def _check_cond(self, node):
        if not isinstance(node, BinOpNode):
            return
        if node.op not in ('==', '!=', '<', '>', '<=', '>='):
            self.errors.append(SemanticError(
                f"Invalid comparison operator '{node.op}'",
                getattr(node, 'line', 0)))
            return
        self._check_declared(node.left)
        self._check_declared(node.right)
        lt = get_type(node.left,  self.sym)
        rt = get_type(node.right, self.sym)
        if (lt != 'unknown' and rt != 'unknown'
                and lt != rt
                and not (lt in NUMERIC and rt in NUMERIC)):
            self.errors.append(SemanticError(
                f"Invalid comparison: cannot compare '{lt}' with '{rt}'",
                getattr(node, 'line', 0)))