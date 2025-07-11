import ast
from typing import override


class ClassTransformer(ast.NodeTransformer):
    @override
    def visit_ClassDef(self, node: ast.ClassDef):
        node.body = [
            name_lookup_function,
            *map(ClassBodyTransformer().visit, node.body),
            ast.Delete(targets=[ast.Name(id="__name_lookup", ctx=ast.Del())]),
        ]
        return node


class ClassBodyTransformer(ast.NodeTransformer):
    @override
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load) and node.id != "__name_lookup":
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

def __name_lookup(name):
    from collections import ChainMap
    from inspect import currentframe
    f = currentframe().f_back
    c = ChainMap(f.f_locals, f.f_globals, f.f_builtins)
    f = f.f_back
    while f is not None and f.f_code.co_name != "<module>":
        c.maps.insert(1, f.f_locals)
        f = f.f_back
    m = object()
    if (v := c.get(name, m)) is not m:
        return v
    raise NameError(name)

"""

name_lookup_function = ast.parse(name_lookup_source).body[0]
