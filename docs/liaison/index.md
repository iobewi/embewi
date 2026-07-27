# Liaison Core ↔ Agent

Le contrat (`embewi-contract-v2.md`) spécifie **quoi** ; cette section relie ce
qui y est écrit à **où** c'est implémenté, de chaque côté. Objectif : pouvoir
répondre vite à deux questions qui reviennent à chaque revue du contrat :

- une section `[NORMATIF]` a-t-elle bien une contrepartie code des deux
  côtés (ou une raison documentée de ne pas en avoir) ?
- une modification du contrat touche-t-elle un seul repo ou les deux, et
  où en est-on de son implémentation ?

```{toctree}
:maxdepth: 1

tracabilite
issues-cross-repo
```

> **Portée.** Ce dossier vit dans `embewi` (le contrat), pas dans
> `embewi-core` ni `embewi-agent-esp` : c'est le seul endroit qui voit les
> deux repos à la fois sans dupliquer leur doc d'implémentation respective
> (cf. principe en page d'accueil). Il ne remplace pas le detail design de
> chaque composant (`embewi-core-design.md`, doc Sphinx de l'agent) — il
> pointe vers eux.
>
> **Fiabilité des références agent.** Les chemins côté `embewi-agent-esp`
> cités ici sont ceux nommés par le contrat lui-même (ex. `embewi_config.c`,
> `esp_ota_*`) : ce repo n'est pas checké out à côté d'`embewi-core`, donc ces
> chemins ne sont **pas vérifiés automatiquement** — à confirmer contre
> `embewi-agent-esp` avant de s'appuyer dessus pour une modification.
