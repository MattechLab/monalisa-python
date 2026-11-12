# Configuration file for the Sphinx documentation builder of monalisa-python.
#
# Same structure, theme and pages as the documentation of the MATLAB toolbox
# (https://mattechlab.github.io/monalisa/, docs/ of https://github.com/MattechLab/monalisa), with the
# code examples in Python and the API generated from the docstrings of the package.
#
# Build: cd docs && make html  (requirements: docs/requirements.txt and the package itself)

import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))  # the package of this checkout, also when it is not installed

import monalisa  # noqa: E402

# -- Project information -----------------------------------------------------

project = "Monalisa (Python)"
copyright = "2024-2026, MatTech Lab"
author = "MatTech Lab"
release = monalisa.__version__
version = release

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.mathjax",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

mathjax3_config = {
    "tex": {
        "inlineMath": [["$", "$"], ["\\(", "\\)"]],
        "displayMath": [["$$", "$$"], ["\\[", "\\]"]],
    },
    "TeX": {
        "Macros": {
            "coloneqq": r"\mathrel{\mathpalette\coloneqq@{}}",
            "parallel": r"\parallel",
        }
    },
}

templates_path = ["../_templates"]
exclude_patterns = ["../_build", "Thumbs.db", ".DS_Store"]
primary_domain = "py"
highlight_language = "default"  # Python, without warnings for plain-text blocks

# API pages: the public functions of each subpackage (its __all__), in source order
autodoc_default_options = {"members": True, "undoc-members": True, "member-order": "bysource"}
autodoc_typehints = "none"  # the signatures keep the MATLAB argument names, without annotations
add_module_names = False

myst_heading_anchors = 3

# -- Markdown pages of the repository (docs/*.md) ------------------------------
# Pages of this site that are Markdown files of docs/ (single source, also read on GitHub): the
# placeholder page rst/<page>.md is replaced by the file when it is read, with its links to files
# of the repository rewritten to GitHub and its links to the other Markdown pages to their pages.

GITHUB = "https://github.com/MattechLab/monalisa-python/blob/main/"
MD_PAGES = {
    "docker.md": "5_docker",
    "renaming.md": "9-1_renaming",
    "porting_method.md": "9-2_porting_method",
    "validation_tutorial_1.md": "9-3_validation_tutorial_1",
    "validation_registration.md": "9-4_validation_registration",
}
DOCS = Path(__file__).resolve().parents[1]


def rewrite_links(text: str) -> str:
    """Links of a docs/*.md file (relative to docs/) for the page of this site."""

    def repl(m):
        target, anchor = m.group(2), m.group(3) or ""
        if re.match(r"[a-z]+:", target):  # http:, https:, mailto:
            return m.group(0)
        if Path(target).name in MD_PAGES:  # another Markdown page: its page on this site
            return f"{m.group(1)}({MD_PAGES[Path(target).name]}.md{anchor})"
        path = posixpath.normpath(posixpath.join("docs", target))  # a file of the repository
        return f"{m.group(1)}({GITHUB}{path}{anchor})"

    return re.sub(r"(\])\(([^)#\s]+)(#[^)\s]*)?\)", repl, text)


def _md_page(app, docname, source):
    md = {page: name for name, page in MD_PAGES.items()}.get(docname)
    if md is not None:
        app.env.note_dependency(str(DOCS / md))
        source[0] = rewrite_links((DOCS / md).read_text(encoding="utf-8"))


def setup(app):
    app.connect("source-read", _md_page)


# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
html_static_path = ["../_static"]
html_title = f"Monalisa (Python) {release}"
html_theme_options = {
    "description": "Python port of the Monalisa MRI reconstruction toolbox",
    "github_user": "MattechLab",
    "github_repo": "monalisa-python",
    "github_button": True,
    "fixed_sidebar": False,
}

# Same custom CSS and JavaScript as the MATLAB documentation
html_css_files = ["custom-navigation.css", "custom-button.css", "important.css", "tip.css"]
html_js_files = ["custom.js"]
