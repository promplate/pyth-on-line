import ast

from .transform import ABOVE_3_14, ClassTransformer


def fix_class_name_resolution[T: ast.AST](mod: T, lineno_offset=0, col_offset=0, skip_annotations=ABOVE_3_14) -> T:
    new_mod = ClassTransformer(skip_annotations).visit(mod)
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


def is_future_annotations_enabled(flags: int):
    import __future__

    return flags & __future__.annotations.compiler_flag != 0
