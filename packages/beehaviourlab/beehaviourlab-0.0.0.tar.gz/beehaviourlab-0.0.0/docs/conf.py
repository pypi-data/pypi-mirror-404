project = "BEEhaviourLab"
author = "BEEhaviourLab"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
]
autosummary_generate = True
exclude_patterns = []
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "logo": {
        "image_light": "bee.png",
        "image_dark": "bee.png",
        "text": "BEEhaviourLab",
    },
    "navigation_depth": 2,
    "show_toc_level": 2,
    "secondary_sidebar_items": ["page-toc"],
    "show_prev_next": False,
}
html_static_path = ["_static"]
