# -*- coding: utf-8 -*-
"""Pruebas reproducibles: matriz de la sección 16."""
from command_analyzer import parse_minitcl, parse_minitcl_expr, expr_shape, analyze_command
from model import ParseError

_paso = 0; _fallo = 0
def _val(label, src):
    global _paso, _fallo
    try:
        parse_minitcl(src); print(f"  OK   {label}"); _paso += 1
    except Exception as e:
        print(f"  FALLA {label} -> {type(e).__name__}: {str(e).splitlines()[0]}"); _fallo += 1
def _err(label, src, expr=False):
    global _paso, _fallo
    try:
        (parse_minitcl_expr if expr else parse_minitcl)(src)
        print(f"  FALLA {label} -> no lanzo error"); _fallo += 1
    except ParseError:
        print(f"  OK   {label} (ParseError)"); _paso += 1
    except Exception as e:
        print(f"  FALLA {label} -> {type(e).__name__} (se esperaba ParseError)"); _fallo += 1
def _shape(label, src, shape):
    global _paso, _fallo
    try:
        got = expr_shape(parse_minitcl_expr(src))
        assert got == shape, f"esperado {shape}, obtuvo {got}"
        print(f"  OK   {label}"); _paso += 1
    except Exception as e:
        print(f"  FALLA {label} -> {e}"); _fallo += 1

print("VALIDOS (producen AST):")
_val('puts "" (comilla vacia)', 'puts ""')
_val('puts {} (braced vacio)', 'puts {}')
_val('set x hola_${nombre}_fin', 'set x hola_${nombre}_fin')
_val('puts [set x 1; set x]', 'puts [set x 1; set x]')
_val('puts [list [set x] y]', 'puts [list [set x] y]')
_val('puts {a {b} c}', 'puts {a {b} c}')
_val('puts {a\\{b\\}c}', 'puts {a\\{b\\}c}')
_val('puts a#b', 'puts a#b')
_val('puts #dato', 'puts #dato')
_val('# comentario (script vacio)', '# comentario')
_val('puts "a; b"', 'puts "a; b"')
_val('puts $a(3)', 'puts $a(3)')

print("VALIDOS ESTRUCTURALES (el error llega recien en validacion):")
_val('set x 1 2', 'set x 1 2')
_val('if {1} {puts si} else', 'if {1} {puts si} else')
_val('puts {if mal formado}', 'puts {if mal formado}')

print("ERRORES DE LEXER/PARSER (deben lanzar ParseError):")
_err('puts {sin cierre', 'puts {sin cierre')
_err('puts "sin cierre', 'puts "sin cierre')
_err('puts [set x 1', 'puts [set x 1')
_err('puts {a}b', 'puts {a}b')
_err('puts "a"b', 'puts "a"b')
_err('puts ]', 'puts ]')
_err('puts $a($i) (fuera de perfil)', 'puts $a($i)')

print("ESCAPE decodificado (TEXT ya decodificado):")
try:
    _t = parse_minitcl(r'puts a\tb').commands[0].words[1].parts[0].text
    assert '\t' in _t
    print("  OK   \\t -> tabulador real"); _paso += 1
except Exception as e:
    print("  FALLA escape ->", e); _fallo += 1

print("EXPRESIONES (forma del AST):")
_shape('2 + 3 * 4', '2 + 3 * 4', ('+',2,('*',3,4)))
_shape('10 - 3 - 2 (izq)', '10 - 3 - 2', ('-',('-',10,3),2))
_shape('2 ** 3 ** 2 (der)', '2 ** 3 ** 2', ('**',2,('**',3,2)))
_shape('-2 ** 2', '-2 ** 2', ('-',('**',2,2)))
_shape('2 ** -3', '2 ** -3', ('**',2,('-',3)))
_err('expr residuo "2 3"', '2 3', expr=True)
_err('expr "2 + " (incompleta)', '2 + ', expr=True)

print("VALIDACION (analyze_command):")
try:
    analyze_command(parse_minitcl('proc f {x x} {return $x}').commands[0])
    print("  FALLA proc {x x} -> no detecto duplicados"); _fallo += 1
except ParseError:
    print("  OK   proc {x x} duplicados (ParseError)"); _paso += 1
for lbl, src in [('expr {$x + 3}','expr {$x + 3}'),
                 ('if {$x>1} {puts a}','if {$x > 1} {puts a}'),
                 ('while {$i<10} {incr i}','while {$i < 10} {incr i}')]:
    try:
        analyze_command(parse_minitcl(src).commands[0]); print(f"  OK   analiza {lbl}"); _paso += 1
    except Exception as e:
        print(f"  FALLA analiza {lbl} -> {e}"); _fallo += 1

print("")
print(f"RESULTADO: {_paso} OK, {_fallo} fallas  ({_paso}/{_paso+_fallo})")

if _fallo:
    raise SystemExit(1)
