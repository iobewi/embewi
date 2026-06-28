# Embewi

Dépôt de **référence** du système Embewi : le **contrat** d'interface versionné
(`v1alpha1`), la documentation transverse et le site de doc.

Embewi gère des microcontrôleurs (ESP32) comme des nœuds OTA d'un cluster
Kubernetes, via deux composants qui se conforment au contrat :

- **Agent** — [iobewi/embewi-agent-esp](https://github.com/iobewi/embewi-agent-esp) : firmware ESP32 / ESP-IDF.
- **Core** — [iobewi/embewi-core](https://github.com/iobewi/embewi-core) : runtime Kubernetes.

**Source de vérité** de l'API Core ↔ Agent : les composants l'épinglent par
version (submodule / tag).

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
