# -- Path setup --------------------------------------------------------------
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------
project = 'workflow-api'
copyright = '2025, Caltech'
author = 'Caltech/JPL Labcas Team'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'swagger_plugin_for_sphinx',
    'sphinxcontrib.mermaid',
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']
