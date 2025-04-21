import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "goit_python_web"
copyright = "2025, Nick"
author = "Nick"

extensions = ["sphinx.ext.autodoc"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "nature"
html_static_path = ["_static"]
