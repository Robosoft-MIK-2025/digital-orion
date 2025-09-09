import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(".."))

project = "Digital Oreon"
author = "Roman Ivanov"
copyright = f"{datetime.now().year}, {author}"
language = "ru"

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinxcontrib.plantuml",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "furo"
html_static_path = ["_static"]

# PlantUML configuration
# Use public PlantUML server and render PNG
plantuml = os.getenv("PLANTUML_CMD", "plantuml")
plantuml_output_format = "png"
plantuml_syntax_error_image = True
plantuml_server = os.getenv("PLANTUML_SERVER", "https://www.plantuml.com/plantuml")

# Simple substitutions available in MyST markdown
rst_prolog = """
.. |ProjectName| replace:: Digital Oreon
.. |Author| replace:: Roman Ivanov
"""


