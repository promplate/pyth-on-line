from functools import cache


@cache
def patch_input():
    import builtins

    def input(prompt=""):
        from js import window

        return window.prompt(prompt) or ""

    builtins.input = input
