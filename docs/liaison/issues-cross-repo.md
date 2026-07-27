# Suivi des issues cross-repo

Décisions ou correctifs qui touchent le contrat **et** au moins un des deux
repos d'implémentation. Une issue purement contractuelle (vocabulaire,
clarification) n'a pas besoin d'entrée ici — seulement celles qui laissent du
travail de code derrière elles.

Aucune issue active pour le moment — toutes les issues 1-6 identifiées lors de
la revue de contrat ont au moins leur volet Core traité (cf. tableaux
ci-dessous).

## Issues terminées (toutes cases applicables ✔)

| # | Titre | Ce qui a été fait |
|---|---|---|
| 1 | Rotation de token — rétention `McuSecret.previousToken` | Core (2026-07-23) : `internal/heartbeat/server.go` (`validateToken` accepte `token`/`previousToken`, `clearPreviousToken` sur confirmation) + `internal/controller/mcunode_controller.go` (`reconcileTokenRotation`, rejoue `POST /token` tant que non confirmé, Events `TokenRotationApplied`/`TokenRotationFailed`). Déclencheur : écriture atomique `data["token"]`+`data["previousToken"]` dans le Secret par l'opérateur/GitOps (documenté sur `McuNodeSpec.TokenRef`, `api/v1alpha1/mcunode_types.go`). Pas de changement agent (un seul `POST /token` reçu, comme avant). Tests : `TestReconcile_TokenRotation_*` (controller), `TestHandleHeartbeat_{Previous,Current}Token_*` (heartbeat). |
| 3 | `heartbeat.ip` pilote l'EndpointSlice → primitive de redirection de trafic | Core (2026-07-23) : `internal/heartbeat/server.go` compare `hb.IP` à l'IP source TCP, émet l'Event `HeartbeatIPMismatch` (Warning) sans rejeter le heartbeat ni bloquer l'EndpointSlice. Pas de changement agent. Test : `TestHandleHeartbeat_IPMismatch_EmitsEvent`. |
| 5 | `POST /config` — restriction de la sentinelle `""` | Documentation seule (§4a du contrat) — pas de travail de code, converge dès la rédaction du contrat. |
| 6 | §8b (métriques Prometheus) dans le contrat transverse | Décision documentaire seule (page d'accueil reformulée) — pas de travail de code. |

## Issues partiellement terminées (Core fait, agent restant)

| # | Titre | Ce qui a été fait côté Core | Ce qui reste côté agent |
|---|---|---|---|
| 2 | NTP fail-closed → device silencieux | Core (2026-07-23) : `internal/heartbeat/server.go` — `HeartbeatPayload.Reason`, `ready` forcé à `false` si `reason=="clock_unsynced"` même si `state=running`+`ota_validated=true`, condition `Ready/ClockUnsynced` dédiée (distincte de `HeartbeatTimeout`/`DeviceNotReady`), `LastHeartbeat` mis à jour quand même (pas de silence, §2). Tests : `TestHandleHeartbeat_ClockUnsynced_NotReady`, `TestHandleHeartbeat_NoReason_StillReady`. | Émettre `reason:"clock_unsynced"` dans le heartbeat tant que SNTP n'a pas convergé, et ouvrir le flux sortant sans vérifier la validité temporelle (`notBefore`/`notAfter`) du certificat Core pendant cette fenêtre (chiffrement + CN/chaîne restent vérifiés). |
| 4 | Découverte de version d'API (`api_versions` dans `GET /info`) | Core (2026-07-25) : `internal/agent/client.go` — `InfoResponse.ApiVersions`, `agent.NegotiateAPIVersion()` (plus haute version commune ; champ absent → `v1alpha1` supposé, conforme §4) ; `internal/controller/mcudeployment_controller.go` (`persistNodeInfo` négocie à chaque `GET /info` dans `phasePreparing`/`phaseActivating`, stocke le résultat dans `McuNode.Status.ApiVersion`, échec de négociation → `dep.fail("APIVersionUnsupported", …)` + Event Warning, bloque le déploiement plutôt que de tenter un protocole incompatible). Tests : `TestNegotiateAPIVersion_*` (agent), `TestPhasePreparing_UnsupportedAPIVersion_Fails`, `TestPhasePreparing_APIVersionAbsent_NegotiatesV1Alpha1` (controller). | Émettre `api_versions` dans `GET /info` (aujourd'hui absent → le Core suppose `v1alpha1`, ce qui reste correct mais ne teste pas la négociation réelle côté device). |

## Convention

- **Contrat** : ✅ si la section normative est écrite et fusionnée dans
  `embewi-contract-v2.md` ; ⬜ sinon.
- **`embewi-core` / `embewi-agent-esp`** : ⬜ tant qu'aucun code ne couvre le
  comportement spécifié ; ✔ une fois mergé côté repo concerné (lier le
  commit/PR dans une note à droite de la case le jour où elle passe à ✔).
- Une ligne reste dans ce tableau tant qu'au moins une case n'est pas ✔ ; à
  retirer (ou archiver) une fois les trois colonnes converties.
- Ajouter une ligne dès qu'une revue de contrat identifie un écart qui
  déborde sur `embewi-core` ou `embewi-agent-esp` — avant même que
  l'implémentation ne commence.
