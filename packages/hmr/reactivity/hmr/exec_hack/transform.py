import ast
from typing import override


class ClassTransformer(ast.NodeTransformer):
    @override
    def visit_ClassDef(self, node: ast.ClassDef):
        traverser = ClassBodyTransformer()
        has_docstring = node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)
        node.body[has_docstring:] = [
            *def_name_lookup().body,
            *map(traverser.visit, node.body[has_docstring:]),
            ast.Delete(targets=[ast.Name(id="__name_lookup", ctx=ast.Del())]),
            ast.parse(f"False and ( {','.join(traverser.names)} )").body[0],
        ]
        return ast.fix_missing_locations(node)


class ClassBodyTransformer(ast.NodeTransformer):
    def __init__(self):
        self.names: dict[str, None] = {}  # to keep order for better readability

    @override
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load) and node.id != "__name_lookup":
            self.names[node.id] = None
            return build_name_lookup(node.id)
        return node

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        self.visit(node.args)
        if node.returns:
            node.returns = self.visit(node.returns)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore  # noqa: N815

    @override
    def visit_Lambda(self, node: ast.Lambda):
        self.visit(node.args)
        return node


def build_name_lookup(name: str) -> ast.Call:
    return ast.Call(func=ast.Name(id="__name_lookup", ctx=ast.Load()), args=[ast.Constant(value=name)], keywords=[])


name_lookup_source = """

def __name_lookup():
    from builtins import KeyError, NameError
    from collections import ChainMap
    from inspect import currentframe
    f = currentframe().f_back
    c = ChainMap(f.f_locals, f.f_globals, f.f_builtins)
    if freevars := f.f_code.co_freevars:
        c.maps.insert(1, e := {})
        freevars = {*f.f_code.co_freevars}
        while freevars:
            f = f.f_back
            for name in f.f_code.co_cellvars:
                if name in freevars.intersection(f.f_code.co_cellvars):
                    freevars.remove(name)
                    e[name] = f.f_locals[name]
    def lookup(name):
        try:
            return c[name]
        except KeyError as e:
            raise NameError(*e.args) from None
    return lookup

__name_lookup = __name_lookup()

"""


def def_name_lookup():
    tree = ast.parse(name_lookup_source)

    for node in ast.walk(tree):
        for attr in ("lineno", "end_lineno", "col_offset", "end_col_offset"):
            if hasattr(node, attr):
                delattr(node, attr)

    return tree
