# embewi-contract

Contrat d'interface **versionné** (`v1alpha1`) entre l'agent embarqué ESP32
([iobewi/embewi](https://github.com/iobewi/embewi)) et le runtime Kubernetes
([iobewi/embewi-core](https://github.com/iobewi/embewi-core)) du système Embewi.

**Source de vérité** de l'API Core ↔ Agent : les deux composants s'y conforment
et l'épinglent par version (submodule / tag).

## Contenu

```text
docs/
├── embewi-contract-v2.md   # spécification normative (la référence)
├── index.md / conf.py      # site de doc (Sphinx + MyST)
└── _static/                # logo, favicon
.github/workflows/docs.yml  # build + publication GitHub Pages
```

## Doc en ligne

Site publié sur GitHub Pages à chaque push (voir le workflow).
Prérequis une fois : **Settings → Pages → Source = GitHub Actions**.

## Build local

```bash
pip install -r docs/requirements.txt
sphinx-build -b html -W docs docs/_build/html
```
