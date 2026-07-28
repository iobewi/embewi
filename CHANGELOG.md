# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/).

## [1.0.0] - 2026-07-28

Première version publique du contrat Core↔Agent (`embewi-contract-v2.md`),
implémentée et vérifiée croisée dans
[`embewi-core`](https://github.com/iobewi/embewi-core) et
[`embewi-agent-esp`](https://github.com/iobewi/embewi-agent-esp).

> **Pourquoi `v1.0.0` alors que le protocole reste `v1alpha1` ?**
> Version logicielle (ce tag, maturité de la spec et de ses deux
> implémentations) et version de protocole (`v1alpha1`, le préfixe
> `/v1alpha1/...` effectivement utilisé sur le réseau) sont deux axes
> indépendants — comme Kubernetes lui-même, versionné en `v1.29` pendant
> que ses groupes d'API évoluent séparément (`apps/v1`, `batch/v1`…).
> Rester en `v1alpha1` signale honnêtement que l'interface (endpoints,
> `api_versions`, négociation) peut encore évoluer ; ce n'est pas un oubli.
> Migrer le préfixe lui-même serait un changement cassant sur une flotte de
> devices physiques — un projet à part, avec un vrai plan de compatibilité,
> pas une simple étape de release.

### Ajouté

- Contrat `v1alpha1` complet (§0-§9) : modèle de sécurité, enrôlement,
  machine d'état agent, séquence OTA, endpoints inbound, modèle de config
  en couches, codes d'erreur stables, flux sortants (heartbeat/logs),
  idempotence, politique de binding, effets Kubernetes, conditions CRDs,
  pipeline métriques.
- 6 issues de revue de contrat résolues (Core **et** agent) : rétention de
  token (`previousToken`), détection de divergence `heartbeat.ip`, canal de
  détresse NTP, découverte de version d'API (`api_versions`), restriction
  de la sentinelle `""` (§4a), place des métriques dans le contrat
  transverse (§8b).
- Dossier `docs/liaison/` : matrice de traçabilité contrat↔code (Core et
  agent, vérifiée ligne à ligne, SHA agent pinné) et suivi des issues
  cross-repo.
