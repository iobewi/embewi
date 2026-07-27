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
> **Fiabilité des références agent.** Colonne Agent auditée par lecture de
> code dans `embewi-agent-esp` le **2026-07-27** (voir `tracabilite.md`) —
> les chemins/lignes cités sont vérifiés à cette date, pas de garantie
> au-delà (pas de vérification automatique/CI cross-repo). Une correction et
> un écart pré-existant ont été trouvés à cet audit : voir « Écarts
> complémentaires » dans `tracabilite.md`.
