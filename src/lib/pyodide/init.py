# type: ignore

from micropip import install

await install(
    [
        "promplate==0.3.3.4",
        "promplate-pyodide==0.0.1",
    ]
)
del install

from promplate_pyodide import patch_promplate

patch_promplate(True)

from promplate import *
from promplate.llm.openai import *
