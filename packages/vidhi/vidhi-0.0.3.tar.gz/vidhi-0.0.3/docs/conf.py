# Configuration file for the Sphinx documentation builder.

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parents[1].resolve()))

# -- Project information -----------------------------------------------------

project = "vidhi"
copyright = "2024-onwards Systems for AI Lab, Georgia Institute of Technology"
author = "Vidhi Team"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_title = "vidhi"

html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#4A90A4",
        "color-brand-content": "#4A90A4",
    },
}
