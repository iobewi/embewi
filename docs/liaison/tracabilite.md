# Matrice de traçabilité

Colonne **Core** vérifiée par lecture de code dans `embewi-core`, dernier
audit complet **2026-07-23** (voir écarts complémentaires en bas de page).
Colonne **Agent** vérifiée par lecture de code dans `embewi-agent-esp`
@ [`4d0a129`](https://github.com/iobewi/embewi-agent-esp/commit/4d0a129f2fa7e454bab633f31a2c047c9b7f16b6)
(pinné — re-vérifier cette colonne si l'agent avance sans mise à jour ici).
Trois passes :
- **2026-07-27** (ciblée sur les issues 1-4 + §3) : build dev + build prod
  compilés avec succès pour valider les lignes touchées. Correction : la
  ligne §3 citait TWDT (watchdog matériel) pour la deadline `pending_verify`
  — le code utilise en réalité un `esp_timer` logiciel.
- **2026-07-28** (balayage complet des lignes restantes, seule la colonne
  Agent était encore non vérifiée / recopiée du texte du contrat). Un écart
  trouvé : `idf_incompatible` (table §4b) jamais émis — `idf_version` parsé
  depuis `/ota/prepare` mais jamais comparé.
- **2026-07-28, correctif** : `idf_incompatible` implémenté côté agent
  (`embewi_idf_version_compatible`, `main/embewi_parse.c:131-137` — compare
  le major IDF déclaré à `ESP_IDF_VERSION_MAJOR` du device, fail-safe sur
  format invalide), câblé dans `embewi_ota_prepare` (`main/embewi_ota.c:117-119`).
  Le Core mappait déjà `idf_incompatible` → Event `OTARejectedIdf` depuis le
  début (jamais atteint faute d'émission agent) — boucle fermée sans rien à
  toucher côté Core. Tests : `test_idf_version_compatible`
  (`test/host/test_parse.c`, +8 assertions, 123 au total, vérifiées en local).

| Section contrat | Core (`embewi-core`) | Agent (`embewi-agent-esp`) | Statut |
|---|---|---|---|
| §1 Token Bearer, transport HTTPS | `internal/heartbeat/server.go:152-178` (`validateToken`, `subtle.ConstantTimeCompare`) ; `internal/agent/client.go:87` (header `Authorization: Bearer` sur tous les appels inbound) | ✔ `main/embewi_http.c:47-57` (`authorized`, comparaison temps-constant sur tous les endpoints) ; `sdkconfig.defaults.prod:19` (`CONFIG_SECURE_BOOT_V2_ENABLED`), `:29` (`CONFIG_SECURE_FLASH_ENC_ENABLED`), `:51` (`CONFIG_EMBEWI_VERIFY_CORE_CERT`) — détail dans `embewi-prod-security.md` (agent) | Core ✔ ; agent ✔ |
| §1 Vérification signature (rôle « efficacité » du Core, tableau §1) | ✔ (2026-07-25) `internal/oci/client.go` : `WithTrustedPublicKey` (Ed25519) + `verifySignature` vérifient l'annotation manifeste `embewi.io/signature` avant de retourner `FirmwareMeta` — opt-in via `OCI_TRUSTED_PUBLIC_KEY`, no-op si absent (posture dev/MVP). ✔ `StreamBlob` (`*oci.BlobStream`) re-hache les octets réellement reçus au fil de l'eau et les compare au digest attendu (`Err()` → `ErrBlobDigestMismatch`) ; `phaseWriting` (`mcudeployment_controller.go`) vérifie ce résultat après `OTAWrite`, émet `OTABlobDigestMismatch` et ne fait pas avancer vers Activating en cas de divergence — la signature protège le digest *déclaré*, le re-hash protège la correspondance digest↔octets réels | ✔ Seule vérification réelle du binaire écrit : SHA-256 incrémental (PSA crypto API) au fil des chunks reçus (`main/embewi_ota.c:25,131-155`), comparé au digest attendu à la finalisation (`embewi_ota_write_finish:160-186`, `digest_mismatch` si divergence) — aucune relecture flash après coup | Core ✔ ; agent ✔ |
| §1 Rayon d'action d'un token compromis (issue 3) | ✔ `internal/heartbeat/server.go` (comparaison `hb.IP`/`tcpIP`, Event `HeartbeatIPMismatch`) — cf. ligne §8 ci-dessous | — | Core ✔ |
| §1a Enrôlement, identité device | `api/v1alpha1/mcunode_types.go:31-39` (`TokenRef`), `internal/controller/mcunode_controller.go` | ✔ `main/embewi_provision.c` : portail captif AP, NVS `embewi_prov` (`:31`), fenêtre bornée à 10 min (`AP_PORTAL_TIMEOUT_MS:47`), fallback `node_id` dérivé de la MAC si NVS vide (`embewi_node_id_load:478-494`) | Core ✔ ; agent ✔ |
| §1a Rejet d'un `node_id` en double | ✔ (2026-07-25) `findNode` (`internal/heartbeat/server.go`) détecte >1 `McuNode` matchant `spec.nodeId`, refuse d'attacher le heartbeat à l'un d'eux (fail-safe, pas de pick silencieux du premier), émet un Event `DuplicateNodeID` sur chaque objet concerné. Pas de webhook d'unicité (validation a posteriori au heartbeat, pas à la création du McuNode) | — l'agent s'annonce, ne déduplique pas (attendu) | Core ✔ |
| §2 États de l'agent | `internal/heartbeat/server.go` (`validNodeStates`, rejette en 400 tout `state` hors enum) | ✔ `main/embewi_agent.h:17-22` (enum), transitions dans `main/embewi_selfcheck.c` : `:71-77` (self-check KO → `EMBEWI_ROLLBACK` → `esp_ota_mark_app_invalid_rollback_and_reboot`, ou `EMBEWI_FAILED` si le rollback échoue), `:89-92` (self-check OK → `esp_ota_mark_app_valid_cancel_rollback` → `EMBEWI_RUNNING`) | Core ✔ ; agent ✔ |
| §3 Séquence OTA | `internal/controller/mcudeployment_controller.go:29` (`ConfirmTimeout`), `:74-114` (dispatch des phases), `:464-490` (`phaseActivating`) ; `internal/agent/client.go` (`OTAPrepare:175-188`, `OTAWrite`, `OTAActivate:367-379`) | ✔ (vérifié 2026-07-27) `esp_ota_set_boot_partition` (`main/embewi_ota.c:230`), `esp_ota_mark_app_valid_cancel_rollback` (`main/embewi_selfcheck.c:89`). ⚠ correction : le contrat cite un hardware watchdog (TWDT) pour la deadline `pending_verify` — l'agent utilise en réalité un `esp_timer` logiciel (`main/embewi_selfcheck.c:115-121`) → `esp_restart()` (`:51`), choisi précisément parce qu'il survit à une task qui hang (contrairement au TWDT qui watchdogue des tasks, pas un délai applicatif) | Core ✔ ; agent ✔ |
| §4 Endpoints inbound `/info /health /config /reboot` | `internal/agent/client.go` (`GetInfo:127`, `GetHealth:145`, `GetConfig:317`, `PostConfig:331`, `PostReboot:348`) | ✔ `main/embewi_http.c` : `h_info:113-145`, `h_health:148-162`, `h_config_get:441-458`, `h_config_post:472-497`, `h_reboot:500-507` — routes enregistrées `:572-586` | Core ✔ (implémentés) ; ⚠ `GetHealth` n'est appelé **nulle part** côté Core hors tests (contrat le dit optionnel, donc pas bloquant) ; agent ✔ |
| §4 `POST /ota/prepare`, `/ota/activate` | `internal/agent/client.go` (`OTAPrepare:175-188`, `OTAActivate:367-379`) ; mapping Events conforme (`mcudeployment_controller.go:390-404`) | ✔ `main/embewi_http.c` (`h_ota_prepare:165-192`, `h_ota_activate:510-546`) ; logique de compat dans `main/embewi_ota.c:103-126` (`embewi_ota_prepare` — chip/layout/idf/size, `idf_incompatible` via `embewi_idf_version_compatible` depuis 2026-07-28) | Core ✔ ; agent ✔ |
| §4 `PUT /ota/write` + Content-Range | ✔ (2026-07-27) `internal/agent/client.go` (`OTAWrite`/`putOTAChunk`) : chunke en plages de 64 KiB (`otaChunkSize`), une coupure réseau sur une plage retente jusqu'à 3 fois la même plage bufferisée (sans retransmettre les plages déjà confirmées, sans retoucher au flux OCI source), gère le resync 416 (`written` reporté par le device) en ré-émettant uniquement le reliquat de la plage courante | ✔ `main/embewi_http.c:199-288` (`h_ota_write` : lit `Content-Range`, décide BEGIN/RESYNC/CONTINUE) ; logique pure testée sur host dans `main/embewi_parse.c:120-128` (`embewi_ota_plan`, `embewi_ota_is_final`) — handle OTA + SHA-256 incrémental en statiques, survivent à une déconnexion TCP | Core ✔ ; agent ✔ |
| §4 `POST /token` (rotation) | ✔ `internal/controller/mcunode_controller.go` (`reconcileTokenRotation`, appelle `RotateToken()` tant que `previousToken` est présent) | ✔ `main/embewi_http.c:408-438` (`h_token`) — commit NVS avant la réponse, bascule runtime immédiate (`authorized()` exige le nouveau token dès la réponse envoyée) | Core ✔ ; agent ✔ |
| §4 `api_versions` (issue 4, nouveau) | ✔ `internal/agent/client.go` (`InfoResponse.ApiVersions`, `NegotiateAPIVersion` — plus haute version commune, absent → `v1alpha1` supposé) ; `internal/controller/mcudeployment_controller.go` (`persistNodeInfo` négocie à chaque `GET /info`, stocke `McuNode.Status.ApiVersion`, échec → `fail("APIVersionUnsupported", …)` + Event) | ✔ (2026-07-27) `main/embewi_http.c:129` (`h_info`) émet `"api_versions":["v1alpha1"]` (`EMBEWI_API_VERSION`, `main/embewi_agent.h:8`) | Core ✔ ; agent ✔ |
| §4 Rotation token — rétention `previousToken` (issue 1, nouveau) | ✔ `internal/heartbeat/server.go` (`validateToken` accepte `token`/`previousToken`, `clearPreviousToken` sur confirmation) ; `internal/controller/mcunode_controller.go` (`reconcileTokenRotation` rejoue `POST /token` tant que non confirmé). Déclencheur = écriture atomique `token`+`previousToken` dans le Secret par l'opérateur/GitOps (pas d'auto-génération périodique côté Core) | — (aucun changement d'ordre côté agent : reçoit toujours un seul `POST /token`) | Core ✔ |
| §4 `POST /app/port`, `POST /tls/cert` | ✔ (2026-07-28) Réconciliation câblée. `McuDeployment.Spec.AppPort` (`api/v1alpha1/mcudeployment_types.go`) — `reconcileAppPort` (`mcudeployment_controller.go`) compare au port observé (`McuNode.Status.AppPort`), push si divergent, pas de reboot requis (agent redémarre à chaud), `Status.AppPort` mis à jour immédiatement après push confirmé. `McuNode.Spec.TLSSecretRef` (`SecretRef` vers un Secret `kubernetes.io/tls`, `tls.crt`/`tls.key` — compatible cert-manager) — `reconcileTLSCert` (`mcunode_controller.go`) compare un sha256(cert+key) à `Status.TLSCertDigest` (suivi Core-side, pas d'équivalent generation/active_generation côté agent pour le cert), push + reboot si divergent, digest mis à jour seulement après reboot confirmé. Tests : `TestReconcileDeployed_AppPort*`, `TestReconcileTLSCert_*` | ✔ `main/embewi_http.c` : `h_app_port:291-316` (valide 1024-65535, sauvegarde NVS, redémarre le service app immédiatement sans reboot device) ; `h_tls_cert:344-402` (accepte `cert_pem`/`key_pem`, désescape les `\n` littéraux, sauvegarde NVS, effectif au prochain `embewi_http_start()`) | Core ✔ ; agent ✔ |
| §4a Modèle de config en couches | `internal/controller/mcudeployment_controller.go:237-240` (limites 15/63 caractères validées avant push), `:254` (clés `_` filtrées) | ✔ `main/embewi_config.c` : `embewi_cfg_boot_init:29-42` (snapshot NVS figé au boot = config "active"), `embewi_cfg_write:71-84` (`""` efface la clé — reset au défaut build, cf. §4a NORMATIF), `embewi_cfg_bump_generation:88-101` ; filtrage clés `_*` côté agent dans `main/embewi_http.c:463-469` (`cfg_set_cb`) — symétrique au filtrage Core | Core ✔ ; agent ✔ |
| §4b Codes d'erreur → Events K8s | `internal/controller/mcudeployment_controller.go:390-404` (prepare refusé), `:427-441` (write refusé) (`Recorder.Event`, vrais Events K8s) | ✔ Codes émis conformes à la table §4b : `chip_mismatch`/`layout_mismatch`/`idf_incompatible`/`busy`/`size_too_large` (`main/embewi_ota.c:110-121`), `digest_mismatch`/`write_failed`/`ota_begin_failed`/`range_mismatch` (`main/embewi_http.c:216-280`) | Core ✔ pour prepare/write ; ✔ `ConfigMapNotFound` distinct de `ConfigInvalid` (`errConfigMapNotFound`, `configFailReason()`, 2026-07-25) ; agent ✔ — tous les codes couverts |
| §5 Heartbeat / logs | `internal/heartbeat/server.go` (`handleHeartbeat`, `HeartbeatPayload:62-81`), filtrage `temp_celsius=-127.0` (`:332`, `internal/metrics/metrics.go:140-142`) | ✔ `main/embewi_heartbeat.c` : `heartbeat_task:152-181` (POST toutes les 5 s, tous les champs requis + optionnels — `temp_celsius` sentinelle `-127.0f` si capteur indispo, `:65-69`), `embewi_log_emit:189-197` (POST `/v1alpha1/logs`), `main/embewi_time.c` (SNTP) | Core ✔ ; agent ✔ |
| §5 Canal de détresse NTP (issue 2, nouveau) | ✔ `internal/heartbeat/server.go` : `HeartbeatPayload.Reason`, `ready` forcé à `false` si `reason=="clock_unsynced"` (même si `state=running`+`ota_validated=true`), condition `Ready/ClockUnsynced` dédiée, `LastHeartbeat` mis à jour quand même (pas de silence, §2) | ✔ (2026-07-27) `main/embewi_heartbeat.c:177` émet `reason:"clock_unsynced"` tant que `!embewi_time_is_set()` ; `:106-110` bascule `emit_to()` sur `embewi_tls_relaxed_post()` (nouveau fichier `main/embewi_tls_relaxed.c`) — mbedTLS bas niveau, `MBEDTLS_SSL_VERIFY_OPTIONAL` + inspection manuelle post-handshake : seuls `BADCERT_EXPIRED`/`BADCERT_FUTURE` tolérés, chaîne/CN restent bloquants (`embewi_ssl_get_verify_result`). Nécessaire car `esp_http_client`/esp-tls force `VERIFY_REQUIRED` dès qu'une CA est configurée, sans hook pour ne relâcher que la date. Contrepartie : `CONFIG_MBEDTLS_HAVE_TIME_DATE=y` activé en prod (`sdkconfig.defaults.prod:57`) — **écart pré-existant découvert pendant l'implémentation** : cette vérif était jusque-là silencieusement désactivée dans TOUS les états (comportement par défaut ESP-IDF), donc la vérification stricte post-synchro n'existait pas non plus avant ce correctif. **Portée limitée, assumée** : le canal de détresse couvre le heartbeat et `embewi_log_emit()` (events OTA/lifecycle via HTTPS, tous deux via `emit_to()`) mais **pas** le streaming `ESP_LOGx` → WebSocket (`embewi_log.c`, `esp_websocket_client`) — pas de hook `VERIFY_OPTIONAL` équivalent côté client WS, et ce flux est déjà best-effort/lossy par conception (cf. commentaire en tête de `embewi_log.c`). Le heartbeat (§2, jamais silencieux) est garanti ; ce flux logs, non, pendant la fenêtre `clock_unsynced` | Core ✔ ; agent ✔ (portée : heartbeat + logs HTTPS, pas le flux WS) |
| §6 Idempotence (reprise sur crash Core, OTA) | `internal/controller/mcudeployment_controller.go:339-375` (`phasePreparing` relit `staged.state`), `:464-490` (`phaseActivating` anti-double-activate) | ✔ `staged` exposé par `h_info` (`main/embewi_http.c:113-145`, lu via `embewi_staged_load`, `main/embewi_ota.c:30`) — `none/written/activating` conformes | Core ✔ ; agent ✔ |
| §6 Idempotence config (`generation` vs `active_generation`) | ✔ (2026-07-25) `pushConfigIfNeeded` compare aussi `ActiveGeneration < Generation` quand le nvs est déjà conforme → `needsReboot=true` sans repush (`mcudeployment_controller.go:262-270`). `reconcileConfigOnly` reboote dans ce cas comme après un push classique. | — | Core ✔ |
| §7 Politique de binding | `internal/controller/mcudeployment_controller.go:117-158` (`NoDeviceMatched`, `AmbiguousBinding`), `:165-179` (`checkNotBusy`, first-bound-wins) | — (résolution Core) | Core ✔ |
| §7a McuConfigMap | `api/v1alpha1/mcuconfigmap_types.go`, `internal/controller/mcudeployment_controller.go` (`pushConfigIfNeeded:225-278`, `:315-336` watch `configMapToDeployments`) | ✔ `main/embewi_config.c` (namespace NVS `embewi_cfg`), merge-on-key dans `h_config_post`/`cfg_set_cb` (`main/embewi_http.c:463-497`) | Core ✔ ; agent ✔ |
| §8 EndpointSlice (`heartbeat.ip` → `addresses`, `ready`) | `internal/controller/mcunode_controller.go:202-255` (`reconcileEndpointSlice`) | ✔ `main/embewi_heartbeat.c:44-51` (`current_ip_str`, IP STA courante lue depuis le netif à chaque heartbeat — rend le DHCP transparent pour le Core, cf. commentaire en tête de fonction) | Core ✔ ; agent ✔ |
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
5. ✔ (2026-07-27, réconciliation câblée le 2026-07-28) Méthodes clientes
   `PostAppPort`/`PostTLSCert` — voir ligne §4 ci-dessus, désormais appelées
   par `reconcileAppPort`/`reconcileTLSCert`. Tests : `TestPostAppPort_*`,
   `TestPostTLSCert_SendsBody` (`internal/agent/client_test.go`),
   `TestReconcileDeployed_AppPort*`, `TestReconcileTLSCert_*`
   (`internal/controller/*_test.go`).
6. ✔ (2026-07-27) `PUT /ota/write` chunké (64 KiB) avec retry par plage — voir
   ligne §4 ci-dessus. Tests : `TestOTAWrite_MultiChunk_*`,
   `TestOTAWrite_ChunkResync416_*`, `TestOTAWrite_ChunkStalls416_*`
   (`internal/agent/client_test.go`).

## Écarts complémentaires identifiés à l'audit (2026-07-27, agent)

Trouvés en vérifiant la colonne Agent contre `embewi-agent-esp` :

1. ✔ (2026-07-27) Ligne §3 : le contrat cite TWDT (watchdog matériel), le
   code utilise un `esp_timer` logiciel — corrigé ci-dessus (pas de travail
   de code, doc seule ; le mécanisme réel est équivalent ou plus robuste,
   cf. commentaire `embewi_selfcheck.c`).
2. ✔ (2026-07-27) `CONFIG_MBEDTLS_HAVE_TIME_DATE` n'était activé dans aucun
   des deux profils de build (`sdkconfig.defaults` / `sdkconfig.defaults.prod`)
   — défaut ESP-IDF = désactivé. Conséquence : la validité temporelle
   (`notBefore`/`notAfter`) du cert Core n'était vérifiée dans **aucun**
   état, pas seulement pendant la fenêtre `clock_unsynced`. Activé en prod
   en même temps que l'implémentation de l'issue 2 (`sdkconfig.defaults.prod:57`)
   — sans quoi le canal de détresse n'aurait rien eu à « détresser » : la
   vérification stricte qu'il est censé temporairement assouplir n'existait
   pas. Pas d'entrée séparée dans `issues-cross-repo.md` : rattaché à
   l'issue 2 (même ligne §5 ci-dessus), le correctif code est le même commit.

## Écarts complémentaires identifiés à l'audit (2026-07-28, agent — balayage complet)

Trouvé en finissant la vérification des lignes de la colonne Agent restées
non vérifiées après la passe ciblée du 2026-07-27 (comparaison ligne à ligne
du texte déjà écrit contre le code réel de `embewi-agent-esp` @ `467feb3`) :

1. ✔ (2026-07-28) `idf_incompatible` (table §4b) jamais émis — `embewi_ota_prepare`
   (`main/embewi_ota.c:103-123`) validait `chip`/`partition_layout`/`size`
   mais ne comparait jamais `req->idf_version` (parsé dans
   `main/embewi_http.c:174`, jamais lu ensuite). Corrigé : `embewi_idf_version_compatible`
   (`main/embewi_parse.c:131-137`) compare le major IDF déclaré au major du
   device, câblé dans `embewi_ota_prepare` (`main/embewi_ota.c:117-119`).
   Tests : `test_idf_version_compatible` (`test/host/test_parse.c`).
   Pas d'entrée dans `issues-cross-repo.md` (pas de contre-partie Core à
   toucher — le Core mappait déjà `idf_incompatible` → `OTARejectedIdf`).

Toutes les autres lignes vérifiées lors de ce balayage correspondaient
exactement au texte déjà écrit (aucune autre divergence trouvée) : `#1
Token Bearer`, `§1a Enrôlement`, `§2 États`, `§4 endpoints /info /health
/config /reboot`, `§4 ota/prepare /ota/activate`, `§4 PUT /ota/write`,
`§4 POST /token`, `§4 POST /app/port /tls/cert`, `§4a config`, `§4b events`,
`§5 heartbeat/logs`, `§6 idempotence`, `§7a McuConfigMap`, `§8 EndpointSlice
ip`, `§1 digest incrémental agent`.

## Écarts complémentaires identifiés à l'audit (2026-07-28, manifestes K8s Core)

Cette matrice couvre la conformité **contrat ↔ code Go**, mais pas les
manifestes K8s eux-mêmes (`config/`) — angle mort qui a laissé passer trois
bugs indépendants du code Go, invisibles aux tests (le fake client
`controller-runtime` ne fait pas de *pruning* de schéma CRD comme un vrai
apiserver) :

1. ✔ **CRD `mcunodes` : `spec.tokenRef` absent du schéma OpenAPI**
   (`config/crd/bases/embewi.io_mcunodes.yaml`). Un CRD structural sans
   `x-kubernetes-preserve-unknown-fields` fait *pruner* silencieusement par
   l'apiserver tout champ non déclaré à chaque écriture — `tokenRef` aurait
   été supprimé de tout McuNode appliqué sur un vrai cluster, cassant
   l'auth/la rotation de token/le push TLS cert (tout ce qui dépend de
   `Spec.TokenRef`). Invisible dans nos tests car le fake client ne
   prune pas. Corrigé, ainsi que `status.configGeneration`/`tempCelsius`/
   `taskHwmMin` (même CRD, même cause).
2. ✔ **CRD `mcudeployments` : `spec.configMapRef` absent du schéma** —
   même mécanisme, aurait cassé silencieusement toute la fonctionnalité
   McuConfigMap (§7a) en cluster réel malgré un code Core entièrement
   fonctionnel et testé. Corrigé.
3. ✔ **RBAC** (`config/rbac/role.yaml`) : `secrets` n'avait que
   `get/list/watch` — `clearPreviousToken` (confirmation de rotation, §4)
   patch le Secret, aurait échoué en 403.
4. ✔ **ServiceMonitor** (`config/monitoring/servicemonitor.yaml`) :
   namespace `embewi` au lieu de `embewi-system` (Deployment/Service/RBAC),
   et aucun Service n'exposait de port nommé `metrics` — le pipeline §8b,
   pourtant entièrement fonctionnel côté code, n'aurait rien eu à scraper.

Vérifié par comparaison systématique champ-à-champ (script Python, tags JSON
Go vs propriétés OpenAPI des 3 CRD) — les trois schémas correspondent
maintenant exactement aux types Go (hors champs de machinerie K8s
`metadata`/`items` et champs internes à `metav1.Condition`, absents des
structs Go top-level mais présents dans le schéma imbriqué `conditions[]`).

**Recommandation** : ces CRD sont maintenues à la main (`controller-gen`
indisponible dans cet environnement — pas d'accès réseau pour
`go get sigs.k8s.io/controller-tools`). Regénérer via `make manifests` dès
que l'outil est disponible, et traiter cette page comme la référence de
vérité en attendant plutôt que de re-dériver champ par champ à chaque
changement de type Go.

## Comment l'utiliser

- Avant de merger un changement de contrat marqué `[NORMATIF]` : chercher la
  ligne correspondante ici, vérifier qu'un ⬜ n'est pas resté après
  l'implémentation.
- Après avoir implémenté un morceau (Core ou agent) : mettre à jour le
  statut de la ligne dans le même PR que le code — cette page dérive vite si
  elle n'est mise à jour qu'a posteriori.
- Une divergence entre cette page et `embewi-contract-v2.md` §10 (Ordre de
  réalisation) est un signal que l'un des deux documents est périmé.
