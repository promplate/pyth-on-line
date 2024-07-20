# Introducing Pythonline

Pythonline is a Python interpreter that runs in your browser. It is based on the [Pyodide](https://github.com/pyodide/pyodide) project, which is a WASM build of CPython.

With Pythonline, you can easily share your Python snippets with others, without the need to install Python on their local machine. You can also use it to run Python code on your phone or tablet, without the need to install any apps. Let's take the `math` module as an example:

```python
>>> import math
>>> math.pi
```

How about `math.e`? try hovering this! 👉 `math.pi / math.e`

## Basic Usage

Pyodide supports [a large subset of the Python standard library](https://pyodide.org/en/stable/usage/wasm-constraints.html). You can use all of them here.
It also supports [famous scientific libraries](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) like NumPy, Pandas, SciPy, SciKit-Learn, etc.
