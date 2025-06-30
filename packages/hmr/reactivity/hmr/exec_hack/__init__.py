import ast

from .transform import ClassTransformer


def fix_class_name_resolution(mod: ast.Module, lineno_offset=0) -> ast.Module:
    new_mod = ClassTransformer().visit(mod)
    if lineno_offset:
        ast.increment_lineno(new_mod, lineno_offset)
    return ast.fix_missing_locations(new_mod)
