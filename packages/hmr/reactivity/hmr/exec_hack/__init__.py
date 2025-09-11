import ast

from .transform import ClassTransformer


def fix_class_name_resolution[T: ast.AST](mod: T, lineno_offset=0, col_offset=0) -> T:
    new_mod = ClassTransformer().visit(mod)
    if lineno_offset:
        ast.increment_lineno(new_mod, lineno_offset)
    if col_offset:
        _increment_col_offset(new_mod, col_offset)
    return new_mod


def _increment_col_offset[T: ast.AST](tree: T, n: int) -> T:
    for node in ast.walk(tree):
        if isinstance(node, (ast.stmt, ast.expr)):
            node.col_offset += n
            if isinstance(node.end_col_offset, int):
                node.end_col_offset += n
    return tree


def dedent(source: str):
    lines = source.splitlines(keepends=True)
    level = len(lines[0]) - len(lines[0].lstrip())
    return "".join(line[level:] for line in lines), level
