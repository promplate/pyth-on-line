from pathlib import Path

from promplate import Template

here = Path(__file__).parent

explain_error = Template.read(here / "explain-error.j2")
groundings = Template.read(here / "groundings.j2")

components = {"ExplainError": explain_error, "Groundings": groundings}

explain_error.context = groundings.context = components
