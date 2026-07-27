# ============================================================
# EduLang Compiler - Pipeline Orchestrator
# ============================================================

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer         import Lexer
from parser        import Parser
from semantic      import SemanticAnalyzer
from tac_generator import TACGenerator


class CompilerResult:
    def __init__(self):
        self.tokens          = []
        self.lexical_errors  = []
        self.parse_errors    = []
        self.semantic_errors = []
        self.tac             = []
        self.symbol_table    = {}
        self.ast             = None
        self.success         = False


def compile_source(source_code: str) -> CompilerResult:
    result = CompilerResult()

    # Stage 1 – Lexical Analysis
    lexer = Lexer(source_code)
    result.tokens, result.lexical_errors = lexer.tokenize()
    if result.lexical_errors:
        return result

    # Stage 2 – Parsing
    parser = Parser(result.tokens)
    result.ast, result.parse_errors = parser.parse()
    if result.parse_errors:
        return result

    # Stage 3 – Semantic Analysis
    analyzer = SemanticAnalyzer(result.ast)
    result.semantic_errors, sym = analyzer.analyze()
    result.symbol_table = sym.all_symbols()
    if result.semantic_errors:
        return result

    # Stage 4 – TAC Generation
    tac_gen    = TACGenerator(result.ast)
    result.tac = tac_gen.generate()
    result.success = True
    return result


def format_output(source_code: str, result: CompilerResult) -> str:
    SEP = "=" * 62
    lines = [SEP,
             "         EduLang Compiler  —  Output Report",
             SEP]

    # Tokens
    lines.append("\n[TOKENS]")
    if result.tokens:
        lines.append(f"  {'Line':<6} {'Type':<14} Value")
        lines.append("  " + "-" * 44)
        for t in result.tokens:
            lines.append(f"  {t.line:<6} {t.type:<14} {t.value}")
    else:
        lines.append("  No tokens produced.")

    # Lexical Errors
    lines.append("\n[LEXICAL ERRORS]")
    if result.lexical_errors:
        for e in result.lexical_errors:
            lines.append(f"  [ERROR] {repr(e)}")
        lines.append("\n  *** Parsing halted due to lexical errors. ***")
    else:
        lines.append("  No lexical errors found.")

    # Syntax
    lines.append("\n[SYNTAX ANALYSIS]")
    if result.lexical_errors:
        lines.append("  Skipped (lexical errors present).")
    elif result.parse_errors:
        for e in result.parse_errors:
            lines.append(f"  [ERROR] {repr(e)}")
        lines.append("\n  *** Semantic analysis halted due to syntax errors. ***")
    else:
        lines.append("  Syntax analysis passed successfully.")

    # Semantic
    lines.append("\n[SEMANTIC ANALYSIS]")
    if result.lexical_errors or result.parse_errors:
        lines.append("  Skipped (earlier errors present).")
    elif result.semantic_errors:
        for e in result.semantic_errors:
            lines.append(f"  [ERROR] {repr(e)}")
        lines.append("\n  *** TAC generation halted due to semantic errors. ***")
    else:
        lines.append("  Semantic analysis passed successfully.")

    # Symbol Table
    lines.append("\n[SYMBOL TABLE]")
    if result.symbol_table:
        lines.append(f"  {'Name':<20} {'Type':<12} Declared at Line")
        lines.append("  " + "-" * 46)
        for name, info in result.symbol_table.items():
            lines.append(f"  {name:<20} {info['type']:<12} {info['line']}")
    else:
        lines.append("  Empty.")

    # TAC
    lines.append("\n[THREE ADDRESS CODE]")
    if result.tac:
        for instr in result.tac:
            lines.append(f"  {instr}")
    else:
        lines.append("  Not generated (errors present).")

    lines.append("\n" + SEP)
    status = "COMPILATION SUCCESSFUL" if result.success else "COMPILATION FAILED"
    lines.append(f"  STATUS: {status}")
    lines.append(SEP)

    return "\n".join(lines)


def run_compiler(input_path: str, output_path: str):
    with open(input_path, 'r', encoding='utf-8') as f:
        source = f.read()
    result = compile_source(source)
    report = format_output(source, result)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    return result, report