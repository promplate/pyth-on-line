from pathlib import Path
from re import compile

pattern = compile(r"[\w-]+")


def get_package_name(package: str):
    if package.endswith(".whl"):
        return Path(package).stem

    if match := pattern.search(package):
        return match.group()
    else:
        return package
