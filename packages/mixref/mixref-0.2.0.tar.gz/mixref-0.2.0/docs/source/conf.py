# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add src to path for autodoc
sys.path.insert(0, os.path.abspath("../../src"))

# Import version from package
from mixref import __version__

# -- Project information -----------------------------------------------------
project = "mixref"
copyright = "2026, mixref"
author = "mixref"
release = __version__

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Google-style docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_gallery.gen_gallery",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Suppress warnings
suppress_warnings = ["config.cache", "ref.duplicate", "intersphinx.external"]

# -- Napoleon settings (Google-style docstrings) ----------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Sphinx-Gallery configuration --------------------------------------------
sphinx_gallery_conf = {
    "examples_dirs": "examples",  # Path to example scripts
    "gallery_dirs": "auto_examples",  # Where to save gallery generated output
    "filename_pattern": "/plot_",  # Only run plot_*.py files
    "ignore_pattern": r"__init__\.py",
    "plot_gallery": "True",  # Execute examples
    "download_all_examples": False,
    "remove_config_comments": True,
    "expected_failing_examples": [],
    "min_reported_time": 0,
    "image_scrapers": ("matplotlib",),
    "reset_argv": lambda gallery_conf, script_vars: [],
}

# -- Intersphinx configuration -----------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "librosa": ("https://librosa.org/doc/latest/", None),
}

# Set a reasonable timeout for intersphinx to avoid long waits
intersphinx_timeout = 5

# -- Autodoc configuration ---------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
