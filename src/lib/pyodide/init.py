# type: ignore

from functools import partial, wraps

import micropip as pip

pip.install = wraps(pip.install)(partial(pip.install, index_urls=["/simple"]))

await pip.install(
    [
        "promplate==0.3.4.2",
        "promplate-pyodide==0.0.3.2",
    ]
)

from promplate_pyodide import patch_all

await patch_all()

from promplate import *
from promplate.llm.openai import *
