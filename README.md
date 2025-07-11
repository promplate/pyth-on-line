# 这是什么？

Pythonline 是一个原生运行于浏览器中的 Python 解释器，所有代码都在本地运行，而不是任何服务器上。这是基于 [一个编译成 WASM 的 CPython](https://github.com/pyodide/pyodide) 实现的。

通过本平台你可以与他人分享你的 Python 代码片段，而他们无需在本地机器上安装 Python。你甚至也可以在手机或平板上运行 Python 代码，而无需安装任何应用程序。以 `math` 模块为例：

```python
>>> import math
>>> math.pi
```

如果你将鼠标悬停在上面的代码块上，会看到一个按钮可以运行代码。点击之后，试试看将鼠标悬浮在下面的行内代码上 👇

| 类型     | 示例                                          |
| -------- | --------------------------------------------- |
| 全局变量 | `_` `__name__` `int` `Exception`              |
| 字面量   | `[{}]` `1,2` `1+2j` `.0` `0b10`               |
| 表达式   | `math.pi / 2`                                 |
| 赋值语句 | `one = -(math.e ** complex(0, math.pi)).real` |

## 特性简介

我们支持一些类似 IPython 的特性，比如你可以直接 await 异步函数：

```python
from asyncio import sleep

for i in range(10):
    print(i, end=" ")
    await sleep(0.1)
```

再比如原生的报错，但又能显示源码信息：

```python
def reciprocal(x: int):
    return 1 / x

1 + reciprocal(0)
```

## 可用的模块

我们支持所有 Pyodide 支持的库。包括 [绝大多数 Python 标准库](https://pyodide.org/en/stable/usage/wasm-constraints.html)、所有纯 Python 包、以及 [其它适配了 Pyodide 的库](https://pyodide.org/en/stable/usage/packages-in-pyodide.html)，如常见的科学计算库 NumPy、Pandas 和机器学习库 SciPy、SciKit-Learn 等。

此外，你可以使用浏览器 JavaScript 下的全局变量，比如下面这个例子，通过 `navigator` 查看你剪贴板中的文本：

```python
from js import navigator

await navigator.clipboard.readText()
```

下面这个例子，会并发发起 10 个 HTTP 请求：

```python
from asyncio import gather
from pyodide.http import pyfetch  # 这只是 js 中 fetch 的一个包装器

async def f(url):
    res = await pyfetch(url, method="HEAD", cache="no-store")
    print(res.status, res.status_text, res.headers.get("content-type"))
    return res.ok

await gather(*(f(".") for _ in range(10)))
```

> 此项目目前仍在活跃开发中，如果你有任何反馈或建议，请随时[联系我们](https://github.com/promplate/pyth-on-line/discussions)，不胜感激！

## 致谢

- 该项目深受 [StackBlitz](https://stackblitz.com/)、[CodePen](https://codepen.io/) 和 [Marimo](https://github.com/marimo-team/marimo) 的启发
- 来自 [pyodide](https://github.com/pyodide) 的开发人员给予了大量帮助
