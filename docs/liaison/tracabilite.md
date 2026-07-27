# Matrice de traçabilité

Colonne **Core** vérifiée par lecture de code dans `embewi-core`, dernier
audit complet **2026-07-23** (voir écarts complémentaires en bas de page).
Colonne **Agent** limitée à ce que le contrat nomme déjà (fonctions ESP-IDF,
fichiers cités en §10) — non vérifiée contre `embewi-agent-esp`, absent de ce
workspace.

| Section contrat | Core (`embewi-core`) | Agent (`embewi-agent-esp`) | Statut |
|---|---|---|---|
| §1 Token Bearer, transport HTTPS | `internal/heartbeat/server.go:152-178` (`validateToken`, `subtle.ConstantTimeCompare`) ; `internal/agent/client.go:87` (header `Authorization: Bearer` sur tous les appels inbound) | Secure Boot v2, Flash Encryption, `CONFIG_EMBEWI_VERIFY_CORE_CERT` — détail dans `embewi-prod-security.md` (agent) | Core ✔ |
| §1 Vérification signature (rôle « efficacité » du Core, tableau §1) | ✔ (2026-07-25) `internal/oci/client.go` : `WithTrustedPublicKey` (Ed25519) + `verifySignature` vérifient l'annotation manifeste `embewi.io/signature` avant de retourner `FirmwareMeta` — opt-in via `OCI_TRUSTED_PUBLIC_KEY`, no-op si absent (posture dev/MVP). ✔ `StreamBlob` (`*oci.BlobStream`) re-hache les octets réellement reçus au fil de l'eau et les compare au digest attendu (`Err()` → `ErrBlobDigestMismatch`) ; `phaseWriting` (`mcudeployment_controller.go`) vérifie ce résultat après `OTAWrite`, émet `OTABlobDigestMismatch` et ne fait pas avancer vers Activating en cas de divergence — la signature protège le digest *déclaré*, le re-hash protège la correspondance digest↔octets réels | Seule vérification réelle du binaire écrit : incrémentale côté agent | Core ✔ |
| §1 Rayon d'action d'un token compromis (issue 3) | ✔ `internal/heartbeat/server.go` (comparaison `hb.IP`/`tcpIP`, Event `HeartbeatIPMismatch`) — cf. ligne §8 ci-dessous | — | Core ✔ |
| §1a Enrôlement, identité device | `api/v1alpha1/mcunode_types.go:31-39` (`TokenRef`), `internal/controller/mcunode_controller.go` | Portail captif AP, NVS `embewi_prov` (mentionné §1a) | Core ✔ (nominal) |
| §1a Rejet d'un `node_id` en double | ✔ (2026-07-25) `findNode` (`internal/heartbeat/server.go`) détecte >1 `McuNode` matchant `spec.nodeId`, refuse d'attacher le heartbeat à l'un d'eux (fail-safe, pas de pick silencieux du premier), émet un Event `DuplicateNodeID` sur chaque objet concerné. Pas de webhook d'unicité (validation a posteriori au heartbeat, pas à la création du McuNode) | — l'agent s'annonce, ne déduplique pas (attendu) | Core ✔ |
| §2 États de l'agent | `internal/heartbeat/server.go` (`validNodeStates`, rejette en 400 tout `state` hors enum) | Machine d'état `booting/pending_verify/running/degraded/rollback/failed` — source de vérité côté agent | Core ✔ |
| §3 Séquence OTA | `internal/controller/mcudeployment_controller.go:29` (`ConfirmTimeout`), `:74-114` (dispatch des phases), `:464-490` (`phaseActivating`) ; `internal/agent/client.go` (`OTAPrepare:175-188`, `OTAWrite`, `OTAActivate:367-379`) | `esp_ota_set_boot_partition`, `esp_ota_mark_app_valid_cancel_rollback`, TWDT (cités §3) | Core ✔ |
| §4 Endpoints inbound `/info /health /config /reboot` | `internal/agent/client.go` (`GetInfo:127`, `GetHealth:145`, `GetConfig:317`, `PostConfig:331`, `PostReboot:348`) | Handlers HTTPS agent — non vérifiés depuis ce repo | Core ✔ (implémentés) ; ⚠ `GetHealth` n'est appelé **nulle part** hors tests (contrat le dit optionnel, donc pas bloquant) |
| §4 `POST /ota/prepare`, `/ota/activate` | `internal/agent/client.go` (`OTAPrepare:175-188`, `OTAActivate:367-379`) ; mapping Events conforme (`mcudeployment_controller.go:390-404`) | — | Core ✔ |
| §4 `PUT /ota/write` + Content-Range | ✔ (2026-07-27) `internal/agent/client.go` (`OTAWrite`/`putOTAChunk`) : chunke en plages de 64 KiB (`otaChunkSize`), une coupure réseau sur une plage retente jusqu'à 3 fois la même plage bufferisée (sans retransmettre les plages déjà confirmées, sans retoucher au flux OCI source), gère le resync 416 (`written` reporté par le device) en ré-émettant uniquement le reliquat de la plage courante | — | Core ✔ |
| §4 `POST /token` (rotation) | ✔ `internal/controller/mcunode_controller.go` (`reconcileTokenRotation`, appelle `RotateToken()` tant que `previousToken` est présent) | reçoit et applique la rotation (mentionné §4) | Core ✔ |
| §4 `api_versions` (issue 4, nouveau) | ✔ `internal/agent/client.go` (`InfoResponse.ApiVersions`, `NegotiateAPIVersion` — plus haute version commune, absent → `v1alpha1` supposé) ; `internal/controller/mcudeployment_controller.go` (`persistNodeInfo` négocie à chaque `GET /info`, stocke `McuNode.Status.ApiVersion`, échec → `fail("APIVersionUnsupported", …)` + Event) | ⬜ à émettre dans `GET /info` (non vérifié côté agent — le Core suppose `v1alpha1` en son absence, comportement conforme mais non testé en conditions réelles) | Core ✔ ; agent ⬜ |
| §4 Rotation token — rétention `previousToken` (issue 1, nouveau) | ✔ `internal/heartbeat/server.go` (`validateToken` accepte `token`/`previousToken`, `clearPreviousToken` sur confirmation) ; `internal/controller/mcunode_controller.go` (`reconcileTokenRotation` rejoue `POST /token` tant que non confirmé). Déclencheur = écriture atomique `token`+`previousToken` dans le Secret par l'opérateur/GitOps (pas d'auto-génération périodique côté Core) | — (aucun changement d'ordre côté agent : reçoit toujours un seul `POST /token`) | Core ✔ |
| §4 `POST /app/port`, `POST /tls/cert` | ✔ (2026-07-27) `internal/agent/client.go` : `PostAppPort` (valide 1024-65535 côté client avant l'appel), `PostTLSCert`. ⚠ aucun controller ne les appelle encore — pas de champ CRD portant le port applicatif désiré ni de `SecretRef` pour le cert TLS ; méthodes prêtes, réconciliation non câblée (décision de schéma à prendre) | — | Core ✔ (méthodes client) ; ⚠ réconciliation non câblée |
| §4a Modèle de config en couches | `internal/controller/mcudeployment_controller.go:237-240` (limites 15/63 caractères validées avant push), `:254` (clés `_` filtrées) | `embewi_app_init` lit NVS au boot (cité §4a) | Core ✔ |
| §4b Codes d'erreur → Events K8s | `internal/controller/mcudeployment_controller.go:390-404` (prepare refusé), `:427-441` (write refusé) (`Recorder.Event`, vrais Events K8s) | Émission des codes stables (contrat, table §4b) | Core ✔ pour prepare/write ; ✔ `ConfigMapNotFound` distinct de `ConfigInvalid` (`errConfigMapNotFound`, `configFailReason()`, 2026-07-25) |
| §5 Heartbeat / logs | `internal/heartbeat/server.go` (`handleHeartbeat`, `HeartbeatPayload:62-81`), filtrage `temp_celsius=-127.0` (`:332`, `internal/metrics/metrics.go:140-142`) | `embewi_log_emit()`, SNTP au boot (cités §5) | Core ✔ |
| §5 Canal de détresse NTP (issue 2, nouveau) | ✔ `internal/heartbeat/server.go` : `HeartbeatPayload.Reason`, `ready` forcé à `false` si `reason=="clock_unsynced"` (même si `state=running`+`ota_validated=true`), condition `Ready/ClockUnsynced` dédiée, `LastHeartbeat` mis à jour quand même (pas de silence, §2) | ⬜ à implémenter côté agent (bypass validité temporelle du cert Core tant que `!sntp_synced`, émission de `reason`) | Core ✔ ; agent ⬜ |
| §6 Idempotence (reprise sur crash Core, OTA) | `internal/controller/mcudeployment_controller.go:339-375` (`phasePreparing` relit `staged.state`), `:464-490` (`phaseActivating` anti-double-activate) | `staged` exposé par `GET /info` | Core ✔ |
| §6 Idempotence config (`generation` vs `active_generation`) | ✔ (2026-07-25) `pushConfigIfNeeded` compare aussi `ActiveGeneration < Generation` quand le nvs est déjà conforme → `needsReboot=true` sans repush (`mcudeployment_controller.go:262-270`). `reconcileConfigOnly` reboote dans ce cas comme après un push classique. | — | Core ✔ |
| §7 Politique de binding | `internal/controller/mcudeployment_controller.go:117-158` (`NoDeviceMatched`, `AmbiguousBinding`), `:165-179` (`checkNotBusy`, first-bound-wins) | — (résolution Core) | Core ✔ |
| §7a McuConfigMap | `api/v1alpha1/mcuconfigmap_types.go`, `internal/controller/mcudeployment_controller.go` (`pushConfigIfNeeded:225-278`, `:315-336` watch `configMapToDeployments`) | `embewi_config.c` (cité §10) | Core ✔ |
| §8 EndpointSlice (`heartbeat.ip` → `addresses`, `ready`) | `internal/controller/mcunode_controller.go:202-255` (`reconcileEndpointSlice`) | émission `ip` au heartbeat (§5) | Core ✔ |
| §8 Détection divergence `heartbeat.ip` (issue 3, nouveau) | ✔ `internal/heartbeat/server.go` (`tcpIP` vs `hb.IP`, `Recorder.Eventf(..., "HeartbeatIPMismatch", ...)` — détection seule, pas de rejet) | — | Core ✔ |
| §8a Conditions CRDs | McuNode : `internal/heartbeat/server.go:336-373`, `internal/controller/mcunode_controller.go:103-128` — McuDeployment : `mcudeployment_controller.go` (`fail:607-629`, `setReadyCondition:634-654`, `setDeploymentConditions:657-694`) | — (opaque aux conditions K8s côté agent) | Core ✔ — tous les `reason` du contrat couverts |
| §8b Métriques Prometheus | `internal/metrics/metrics.go:14-52` (8 gauges), nettoyage cardinalité `:107-134` + finalizer McuNode | — (agent ignore Prometheus) | Core ✔ |

## Écarts complémentaires identifiés à l'audit (2026-07-23)

Trouvés en lisant le code, sans lien avec les issues 1-6 de la revue de
contrat — donc pas dans `issues-cross-repo.md` (pas de travail agent
attaché), mais à corriger côté Core :

1. ✔ (2026-07-25) Reason `ConfigMapNotFound` émise distinctement de
   `ConfigInvalid` — `errConfigMapNotFound` + `configFailReason()`
   (`mcudeployment_controller.go:36-48`), les deux call sites
   (`reconcileConfigOnly` et `phasePreparing`) mappent désormais
   correctement. Tests : `TestPhasePreparing_ConfigMapMissing_FailsWithConfigMapNotFound`,
   `TestPhasePreparing_ConfigMapInvalidValue_FailsWithConfigInvalid`.
2. ✔ (2026-07-25) `active_generation` comparé à `generation` — voir ligne §6
   ci-dessus. Tests : `TestReconcileConfigOnly_GenerationsEqual_NoReboot`,
   `TestReconcileConfigOnly_ActiveGenerationBehind_RebootsWithoutRepush`,
   `TestReconcileConfigOnly_NVSDiverges_PushesAndReboots`.
3. ✔ (2026-07-25) Détection de `node_id` dupliqué entre plusieurs `McuNode` —
   voir ligne §1a ci-dessus. Test : `TestHandleHeartbeat_DuplicateNodeID_Returns200AndSkipsUpdate`.
4. ✔ (2026-07-25) Vérification de signature Ed25519 avant transfert OTA, et
   re-hash du blob streamé contre le digest déclaré — voir ligne §1
   ci-dessus. Tests : `TestResolveFirmware_TrustedKey_*`, `TestStreamBlob_*`
   (`internal/oci/client_test.go`), `TestPhaseWriting_OCIBlobDigestMismatch_DoesNotAdvanceToActivating`
   (`internal/controller/mcudeployment_controller_test.go`).
5. ✔ (2026-07-27) Méthodes clientes `PostAppPort`/`PostTLSCert` — voir ligne
   §4 ci-dessus. Tests : `TestPostAppPort_*`, `TestPostTLSCert_SendsBody`
   (`internal/agent/client_test.go`). ⚠ reste ouvert : aucune réconciliation
   ne les appelle (pas de champ CRD source de vérité pour port/cert désirés).
6. ✔ (2026-07-27) `PUT /ota/write` chunké (64 KiB) avec retry par plage — voir
   ligne §4 ci-dessus. Tests : `TestOTAWrite_MultiChunk_*`,
   `TestOTAWrite_ChunkResync416_*`, `TestOTAWrite_ChunkStalls416_*`
   (`internal/agent/client_test.go`).

## Comment l'utiliser

- Avant de merger un changement de contrat marqué `[NORMATIF]` : chercher la
  ligne correspondante ici, vérifier qu'un ⬜ n'est pas resté après
  l'implémentation.
- Après avoir implémenté un morceau (Core ou agent) : mettre à jour le
  statut de la ligne dans le même PR que le code — cette page dérive vite si
  elle n'est mise à jour qu'a posteriori.
- Une divergence entre cette page et `embewi-contract-v2.md` §10 (Ordre de
  réalisation) est un signal que l'un des deux documents est périmé.
