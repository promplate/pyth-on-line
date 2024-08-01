from difflib import ndiff


def diff(a: str, b: str):
    return "\n".join(i for i in ndiff(a.splitlines(), b.splitlines()) if not i.startswith(" "))
