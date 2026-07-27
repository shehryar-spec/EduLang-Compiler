# ============================================================
# EduLang Compiler - Three Address Code Generator
# ============================================================

from parser import (ProgramNode, FunctionNode, DeclNode, AssignNode,
                    IfNode, WhileNode, ForNode, ReturnNode,
                    BinOpNode, NumberNode, IdentifierNode, StringNode)


class TACGenerator:
    def __init__(self, ast):
        self.ast          = ast
        self.instructions = []
        self.temp_count   = 0
        self.label_count  = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instr):
        self.instructions.append(instr)

    def generate(self):
        if self.ast is None:
            return []
        for fn in self.ast.functions:
            self.gen_fn(fn)
        return self.instructions

    def gen_fn(self, node):
        self.emit(f"FUNC {node.name}:")
        for s in node.body:
            self.gen_stmt(s)
        self.emit(f"END {node.name}")

    def gen_stmt(self, node):
        if isinstance(node, DeclNode):
            if node.init_expr is not None:
                val = self.gen_expr(node.init_expr)
                self.emit(f"{node.name} = {val}")
        elif isinstance(node, AssignNode):
            val = self.gen_expr(node.expr)
            self.emit(f"{node.name} = {val}")
        elif isinstance(node, IfNode):
            self.gen_if(node)
        elif isinstance(node, WhileNode):
            self.gen_while(node)
        elif isinstance(node, ForNode):
            self.gen_for(node)
        elif isinstance(node, ReturnNode):
            if node.expr:
                val = self.gen_expr(node.expr)
                self.emit(f"return {val}")
            else:
                self.emit("return")

    def gen_if(self, node):
        cond      = self.gen_cond_str(node.condition)
        neg       = self.negate(cond)
        else_lbl  = self.new_label()
        end_lbl   = self.new_label()

        self.emit(f"if {neg} goto {else_lbl}")
        for s in node.then_body:
            self.gen_stmt(s)
        if node.else_body:
            self.emit(f"goto {end_lbl}")
        self.emit(f"{else_lbl}:")
        for s in node.else_body:
            self.gen_stmt(s)
        if node.else_body:
            self.emit(f"{end_lbl}:")

    def gen_while(self, node):
        start = self.new_label()
        end   = self.new_label()
        cond  = self.gen_cond_str(node.condition)
        neg   = self.negate(cond)

        self.emit(f"{start}:")
        self.emit(f"if {neg} goto {end}")
        for s in node.body:
            self.gen_stmt(s)
        self.emit(f"goto {start}")
        self.emit(f"{end}:")

    def gen_for(self, node):
        # initializer
        self.gen_stmt(node.init)

        start = self.new_label()
        end   = self.new_label()
        cond  = self.gen_cond_str(node.condition)
        neg   = self.negate(cond)

        self.emit(f"{start}:")
        self.emit(f"if {neg} goto {end}")
        for s in node.body:
            self.gen_stmt(s)
        # update
        self.gen_stmt(node.update)
        self.emit(f"goto {start}")
        self.emit(f"{end}:")

    def gen_expr(self, node):
        if isinstance(node, NumberNode):
            return str(node.value)
        if isinstance(node, StringNode):
            return node.value
        if isinstance(node, IdentifierNode):
            return node.name
        if isinstance(node, BinOpNode):
            left  = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            # constant folding
            folded = self._fold(node.op, left, right)
            if folded is not None:
                return folded
            tmp = self.new_temp()
            self.emit(f"{tmp} = {left} {node.op} {right}")
            return tmp
        return "?"

    def _fold(self, op, left, right):
        try:
            l = float(left)
            r = float(right)
            res = {'+': l+r, '-': l-r, '*': l*r, '/': l/r}[op]
            return str(int(res)) if res == int(res) else str(res)
        except Exception:
            return None

    def gen_cond_str(self, node):
        if isinstance(node, BinOpNode):
            l = self.gen_expr(node.left)
            r = self.gen_expr(node.right)
            return f"{l} {node.op} {r}"
        return self.gen_expr(node)

    def negate(self, cond):
        neg_map = [
            ('>=', '##LT##'), ('<=', '##GT##'),
            ('!=', '##EQ##'), ('==', '##NE##'),
            ('<', '>='),      ('>', '<='),
        ]
        r = cond
        for old, new in neg_map:
            r = r.replace(old, new)
        r = (r.replace('##LT##', '<')
              .replace('##GT##', '>')
              .replace('##EQ##', '==')
              .replace('##NE##', '!='))
        return r