# type: ignore

from micropip import install

await install(
    [
        "promplate==0.3.3.4",
        "promplate-pyodide==0.0.2.3",
    ]
)
del install

from promplate_pyodide import patch_all

await patch_all()

from promplate import *
from promplate.llm.openai import *
