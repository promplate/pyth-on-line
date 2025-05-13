<div align="center">

# HMR for Python

<sup> on-demand · fine-grained · push-pull reactivity </sup>

[![PyPI - Version](https://img.shields.io/pypi/v/hmr)](https://pypi.org/project/hmr/)
[![Supported Python Version](https://img.shields.io/python/required-version-toml?tomlFilePath=https://github.com/promplate/pyth-on-line/raw/refs/heads/reactivity/packages/hmr/pyproject.toml)](https://github.com/promplate/pyth-on-line/blob/reactivity/packages/hmr/pyproject.toml)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/hmr)](https://pepy.tech/projects/hmr)

</div>

HMR means Hot Module Reload / [Hot Module Replacement](https://webpack.js.org/concepts/hot-module-replacement/). It is a feature that allows part of your app to be updated at runtime without a full rerun.

- The module whose source file **you changed** will rerun
- The module / function that **depend on** the changed module will rerun
- Other modules that are unaffected (like third-party libraries) will not rerun

Thus, in contrast to the traditional way of **cold-reloading** Python applications (like [watchfiles CLI](https://watchfiles.helpmanual.io/cli/)), HMR is just more efficient.

Unlike static-analysis tools like [Tach](https://github.com/gauge-sh/tach), HMR works by tracking the dependencies between names and modules **during runtime** through a [reactive system](https://wikipedia.org/wiki/Reactive_programming).

## Usage

If you are running your entry file with `python foo.py bar baz ...`, you can just replace it with `hmr foo.py bar baz ...`.

You can also try it with `uvx` or `pipx`. If you are using a virtual environment, it is recommended to install `hmr` in the virtual environment instead of globally.
