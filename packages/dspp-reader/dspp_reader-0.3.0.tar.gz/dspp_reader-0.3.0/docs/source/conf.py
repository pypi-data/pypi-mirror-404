# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('dspp_reader')
except PackageNotFoundError:
    __version__ = '0.0.0'

version = '.'.join(__version__.split('.')[:2])
release = __version__
project = 'Dark Sky Protection Photometers Reader'
copyright = '2025, NOIRLab'
author = 'Simón Torres, Guillermo Damke'
license = 'bsd3'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
html_static_path = ['_static']
