# 🚀 EduLang Compiler — Professional Edition

A complete compiler implementation for **EduLang**, a small educational programming language. Built as part of a Compiler Construction Lab project, this tool takes EduLang source code through the full compilation pipeline — lexical analysis, parsing, semantic analysis, and Three Address Code (TAC) generation — with a clean, professional desktop IDE interface.

![Version](https://img.shields.io/badge/version-1.0-blue)
![Status](https://img.shields.io/badge/status-active-success)

---

## 📖 About EduLang

EduLang is a small C-like language supporting:

- Variable declarations (`int`, `float`, `string`)
- Arithmetic expressions with correct operator precedence
- Assignment statements
- `if` / `else` conditional statements
- `while` loops
- `for` loops
- `return` statements

### Example Program

```c
int main() {
    int x = 10;
    int y = 20;
    int z;
    z = x + y * 2;
    if (z > 30) {
        z = z - 5;
    } else {
        z = z + 5;
    }
    while (z > 0) {
        z = z - 1;
    }
    return z;
}
```

---

## ✨ Features

The compiler is built as a full pipeline, with each stage's output visible in the IDE:

| Stage | Description |
|---|---|
| 🔤 **Lexical Analyzer** | Tokenizes source code; detects invalid identifiers, unterminated strings, invalid characters, and wrong numeric formats |
| 🌳 **Parser** | Builds the program structure, correctly handles operator precedence, and reports syntax errors (missing semicolons, braces, parentheses, invalid statements) |
| 🧠 **Semantic Analyzer** | Detects undeclared variables, type mismatches, invalid comparisons, and wrong return types |
| ⚡ **TAC Generator** | Produces optimized Three Address Code without redundant instructions |
| 📋 **Symbol Table** | Tracks all declared variables with their types and scope |
| 📄 **Full Report** | Combines Tokens, Errors, Semantic Results, Symbol Table, and TAC into a single exportable `output.txt` |

### 🔁 For Loop Support

The compiler supports `for` loops, translated into equivalent `while`-style TAC:

```c
for (int i = 0; i < 10; i = i + 1) {
    x = x + i;
}
```

**Grammar:**
```
ForStatement    -> for ( Initialization ; Condition ; Update ) { StatementList }
Initialization  -> Type Identifier = Expression | Identifier = Expression
Condition       -> Expression RelationalOperator Expression
Update          -> Identifier = Expression
```

### 🐞 Error Detection Examples

**Lexical Errors**
```
[ERROR] Lexical Error at line 3: Invalid identifier '2x' (identifier cannot start with a digit)
[ERROR] Lexical Error at line 5: Unterminated string literal: "Ali;
```

**Syntax Errors**
```
[ERROR] Syntax Error at line 3: Missing semicolon ';'
[ERROR] Syntax Error at line 4: Expected ')' but got '{'
```

**Semantic Errors**
```
[ERROR] Semantic Error at line 5: Undeclared variable 'total'
[ERROR] Semantic Error at line 6: Invalid comparison: cannot compare 'string' with 'int'
[ERROR] Semantic Error at line 7: Wrong return type: expected 'int' but got 'string'
```

---

## 🖥️ Screenshots

The IDE includes tabs for **Tokens**, **Lex Errors**, **Syntax**, **Semantic**, **Symbols**, **TAC**, and a combined **Full Report** — plus sample programs you can load directly (Valid Program, Lexical Errors, Syntax Errors, Semantic Errors, For Loop).

---

## 🛠️ Tech Stack

> _Update this section with your actual stack (e.g. Python + Tkinter/PyQt, Java Swing, C++ Qt, etc.)_

- Language: `<your language here>`
- GUI Framework: `<your framework here>`

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/edulang-compiler.git
cd edulang-compiler

# Install dependencies (edit based on your stack)
pip install -r requirements.txt

# Run the compiler
python main.py
```

---

## 🚀 Usage

1. Open the app.
2. Load a sample program from the **Load Sample** dropdown, or write your own EduLang code in the editor.
3. Click **COMPILE**.
4. Browse results in the **Tokens / Lex Errors / Syntax / Semantic / Symbols / TAC** tabs.
5. Click **Save Output** to export everything into `output.txt`.

---

## 📂 Output File Structure

Every compilation generates an `output.txt` containing:

```
[TOKENS]
[LEXICAL ERRORS]
[SYNTAX ANALYSIS RESULT]
[SEMANTIC ANALYSIS RESULT]
[SYMBOL TABLE]
[THREE ADDRESS CODE]
```

---

## 📚 Project Context

This project was developed as a submission for a **Compiler Construction Lab Final Exam**, covering:

- **Debugging & Error Detection** — lexical, syntax, and semantic error handling
- **Feature Extension** — adding full `for` loop support across lexer, grammar, parser, semantic checker, and TAC generator

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the [issues page](../../issues).

---

## 📄 License

This project is licensed under the MIT License — feel free to use and modify it for learning purposes.

---

## 👤 Author

Made with ❤️ for Compiler Construction Lab.
