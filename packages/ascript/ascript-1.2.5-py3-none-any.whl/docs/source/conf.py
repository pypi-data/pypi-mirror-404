# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ascript-api'
copyright = '2025, su'
author = 'su'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# 添加自定义扩展路径
import os
import sys
sys.path.insert(0, os.path.abspath('../source/'))

extensions = [
    'autoapi.extension',
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'doc_extractor'
]

# Napoleon 设置
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

autoapi_type = 'python'
autoapi_dirs = ['../../ascript']  # 指向你的代码目录
html_theme = 'sphinx_rtd_theme'

templates_path = ['_templates']
exclude_patterns = []

language = 'ch'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_static_path = ['_static']
