import ast

from .transform import ClassTransformer


def fix_class_name_resolution(mod: ast.Module) -> ast.Module:
    return ast.fix_missing_locations(ClassTransformer().visit(mod))
