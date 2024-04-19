# type: ignore

from micropip import install

await install(
    [
        "promplate==0.3.4.2",
        "promplate-pyodide==0.0.3.2",
    ]
)
del install

from promplate_pyodide import patch_all

await patch_all()

from promplate import *
from promplate.llm.openai import *
