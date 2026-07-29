# Configuration Sphinx — documentation Embewi Agent.
# Markdown consommé directement via MyST-Parser (aucune réécriture des .md).

project = "Embewi"
author = "Embewi"
copyright = "2026, Embewi"
language = "fr"

# i18n : français = langue source, anglais = traduction via gettext/sphinx-intl.
#   sphinx-build -b gettext docs docs/_build/gettext   → extrait les .pot
#   sphinx-intl update -p docs/_build/gettext -l en    → génère locale/en/LC_MESSAGES/*.po
#   (traduire les .po)
#   sphinx-intl build -d locale                        → compile en .mo
#   sphinx-build -b html -D language=en docs docs/_build/html/en
locale_dirs = ["locale/"]
gettext_compact = True

extensions = ["myst_parser", "sphinx_rtd_theme"]

# Markdown → pages. heading_anchors : ancres h1–h3 pour les liens inter-sections.
source_suffix = {".md": "markdown"}
myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3

# Fichiers du dossier docs/ à NE PAS traiter comme des pages.
exclude_patterns = ["_build", "requirements.txt", "conf.py", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_title = "Embewi — Documentation"
html_theme_options = {
    "navigation_depth": 3,        # sous-sections dans la nav latérale
    "collapse_navigation": False, # garde l'arbo dépliée
    "style_external_links": True, # icône sur les liens externes
}

# Assets de marque déposés dans docs/_static/.
html_static_path = ["_static"]
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"
