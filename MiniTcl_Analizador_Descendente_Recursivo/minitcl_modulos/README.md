# MiniTcl — módulos de la entrega

Analizador de MiniTcl: lexer manual + parser descendente recursivo para scripts,
y lexer/parser LALR(1) con SLY para expresiones. Construye el AST; no ejecuta.

## Módulos (dependen en este orden)
- `model.py`          — AST e infraestructura: Span, Token, ParseError, TokenCursor, nodos, show_ast.
- `script_lexer.py`   — ScriptLexer: tokeniza scripts (modos: llaves, comillas, sustituciones).
- `script_parser.py`  — ScriptParser: descenso recursivo -> AST estructural.
- `expr_lexer.py`     — ExprLexer(sly.Lexer): tokens de expresiones.
- `expr_parser.py`    — ExprParser(sly.Parser): gramática LALR(1) -> AST de expresiones.
- `command_analyzer.py` — Validación de comandos, reanálisis de cuerpos/condiciones y las
  fachadas `parse_minitcl` / `parse_minitcl_expr` (con diagnósticos de línea/columna).
- `test_minitcl.py`   — Pruebas reproducibles (matriz de la sección 16).

## Requisito
    pip install sly

## Correr las pruebas
    python test_minitcl.py        # imprime "RESULTADO: 34 OK, 0 fallas (34/34)"

## Uso rápido
    from command_analyzer import parse_minitcl, parse_minitcl_expr, expr_shape
    ast = parse_minitcl('puts "Hola $nombre"; set x {a b}')
    print(expr_shape(parse_minitcl_expr('2 + 3 * 4')))   # ('+', 2, ('*', 3, 4))
