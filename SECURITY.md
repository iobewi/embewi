# Politique de sécurité

Ce dépôt ne contient qu'une spécification (contrat `v1alpha1`) et de la
documentation — pas de code exécutable. La politique de sécurité complète
(divulgation privée, modèle de menace, dépôts couverts) est centralisée dans
[`embewi-core`](https://github.com/iobewi/embewi-core/blob/main/SECURITY.md).

Le modèle de menace lui-même est normatif ici : voir
[`docs/embewi-contract-v2.md` §1](docs/embewi-contract-v2.md) (`Core verifies
for efficiency. Bootloader verifies for trust.`).

Une ambiguïté ou une lacune dans le contrat qui aurait une conséquence
sécurité (ex. un endpoint mal spécifié, une contrainte NORMATIF absente)
suit la même procédure de signalement que le code : divulgation privée via
l'onglet **Security** de ce dépôt, pas d'issue publique.
