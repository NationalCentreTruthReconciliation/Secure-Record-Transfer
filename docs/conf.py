# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute.
import os
import sys
import tempfile

import django

sys.path.insert(0, os.path.abspath("../app"))
os.environ["DJANGO_SETTINGS_MODULE"] = "app.settings.test"
os.environ["UPLOAD_STORAGE_FOLDER"] = tempfile.gettempdir()
django.setup()


# -- Project information -----------------------------------------------------

project = "NCTR Secure Record Transfer"
copyright = "2024, National Centre for Truth and Reconciliation"
author = "Daniel Lovegrove, National Centre for Truth and Reconciliation"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx_rtd_theme',
    'sphinxcontrib.mermaid'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Order members by the order they appear in the source
autodoc_member_order = 'bysource'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

master_doc = 'index'

# Force removing the build directory before building
build_dir_removal_warn = False
