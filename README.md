# Introducing Pythonline

Pythonline is a Python interpreter that runs in your browser. It is based on the [Pyodide](https://github.com/pyodide/pyodide) project, which is a WASM build of CPython.

With Pythonline, you can easily share your Python snippets with others, without the need to install Python on their local machine. You can also use it to run Python code on your phone or tablet, without the need to install any apps. Let's take the `math` module as an example:

```python
>>> import math
>>> math.pi
```

If you hover over the code block above, you will see a button to run the code.
After that, you can inspect these values by hovering over them 👇

| Kind           | Examples                                      |
| -------------- | --------------------------------------------- |
| Global Names   | `_`, `__name__`, `int`, `Exception`           |
| Literal Values | `[{}]`, `1,2`, `1+2j`, `.0`, `0b10`           |
| Expressions    | `math.pi / 2`                                 |
| Assignments    | `one = -(math.e ** complex(0, math.pi)).real` |

## Main Features

You can use top-level await:

```python
from asyncio import sleep

for i in range(10):
    print(i, end=" ")
    await sleep(0.1)
```

Native and informative traceback:

```python
def reciprocal(x: int):
    return 1 / x
```

Try this:

```python
1 + reciprocal(0)
```

## Basic Usage

Pyodide supports [a large subset of the Python standard library](https://pyodide.org/en/stable/usage/wasm-constraints.html). You can use all of them here.
It also supports all pure-python libs or [adapted hybrid libs](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) such as famous scientific libraries like NumPy, Pandas, SciPy, SciKit-Learn, etc.

Furthermore, you can use global variables like `navigator` from the `window` scope by:

```python
from js import navigator

print(navigator.languages)
await navigator.clipboard.readText()
```

Let's try invoking web requests:

```python
from asyncio import gather
from pyodide.http import pyfetch  # which is just a wrapper on the fetch in js

async def f(url):
    res = await pyfetch(url, method="HEAD", cache="no-store")
    print(res.status, res.status_text, res.headers.get("content-type"))
    return res.ok

await gather(*(f(".") for _ in range(10)))
```

> This project is still work in progress for now, so feel free to [get in touch](https://github.com/promplate/pyth-on-line/discussions) if you have any feedback or suggestions!

## Acknowledgements

- This project is heavily inspired by [StackBlitz](https://stackblitz.com/), [CodePen](https://codepen.io/) and [Marimo](https://github.com/marimo-team/marimo)
- Developers from [pyodide](https://github.com/pyodide) helped me a lot
- There are some other similar projects like [futurecoder](https://futurecoder.io/), [JupyterLite](https://jupyterlite.github.io/demo) and [PyScript](https://pyscript.com/)

## Development

### Running Tests

This project includes comprehensive frontend testing:

```bash
# Unit tests
npm test          # Watch mode
npm run test:run  # Run once

# E2E tests  
npm run test:e2e
```

See [docs/TESTING.md](docs/TESTING.md) for detailed testing documentation.
