# Embewi — Documentation

**Embewi** gère des microcontrôleurs (ESP32) comme des nœuds OTA d'un cluster
Kubernetes. Le système est fait de deux composants qui communiquent via un
**contrat versionné** — ce dépôt en est la source de vérité.

```text
  Core (Kubernetes, Go)  ── v1alpha1 ──►  Agent (ESP32, ESP-IDF)
  réconcilie, pousse OTA                  reçoit, valide, exécute
```

## Le contrat

```{toctree}
:maxdepth: 2
:caption: Spécification

Contrat Core ↔ Agent <embewi-contract-v2>
```

## Dépôts & docs composant

- **Référence (ce dépôt)** — [`iobewi/embewi`](https://github.com/iobewi/embewi) :
  contrat `v1alpha1` + doc système + site.
- **Agent** — [`iobewi/embewi-agent-esp`](https://github.com/iobewi/embewi-agent-esp)
  · [📖 doc](https://iobewi.github.io/embewi-agent-esp/) : firmware ESP32/ESP-IDF.
  Docs propres au device (build prod, Secure Boot) sur son site.
- **Core** — [`iobewi/embewi-core`](https://github.com/iobewi/embewi-core) :
  runtime Kubernetes. Design des contrôleurs dans son repo.

> Principe : le **contrat** (transverse, versionné) vit ici ; la doc **propre à
> chaque composant** vit avec son code, pour ne pas diverger.
