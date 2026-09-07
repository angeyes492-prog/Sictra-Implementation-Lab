# Block 1 — Local operator workspace preflight v0.1

Date: 2026-09-06. Evidence class: local implementation test.

Verified: first initialization, exact 32-byte key creation, manifest without
key material, idempotent reuse, empty verified dossier store, rejection of
non-empty unknown state, incompatible manifest, truncated key, invalid dossier
JSON and injected partial initialization failure. The launcher contains the
mandatory initialization and `--operator-state` binding.

Data recovery tests additionally verify a real signed synthetic dossier backup
and restore under the original keys, no-overwrite behavior, no keys in the
backup, empty-state behavior, rejection of an in-state destination and digest
tamper rejection without residual restored data.

Focused result: 22/22 tests; full local regression: 270/270. Startup/key
configuration is on SHA `7849ac66aff882c180b62ea7ffa4473688ea5f3d`
with successful GitHub Actions run #348. Exact-SHA CI for the backup extension
is pending. Concurrent online backup, off-device/key recovery and ACL
validation remain outside this slice.
