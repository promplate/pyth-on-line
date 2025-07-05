from functools import cache
from sys import modules

from micropip._compat import LOCKFILE_PACKAGES
from pyodide.code import find_imports


@cache
def build_reversed_index() -> dict[str, str]:
    return {import_name: package_name for package_name, info in LOCKFILE_PACKAGES.items() for import_name in info["imports"]}


def import_name_to_package_name(import_name: str):
    if import_name not in modules:
        return build_reversed_index().get(import_name)


def find_packages_to_install(source: str):
    return list(filter(None, map(import_name_to_package_name, find_imports(source))))
