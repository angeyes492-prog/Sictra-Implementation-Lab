# Block 1 — Local operator workspace preflight v0.1

Date: 2026-09-06. Evidence class: local implementation test.

Verified: first initialization, exact 32-byte key creation, manifest without
key material, idempotent reuse, empty verified dossier store, rejection of
non-empty unknown state, incompatible manifest, truncated key, invalid dossier
JSON and injected partial initialization failure. The launcher contains the
mandatory initialization and `--operator-state` binding.

Focused result: 20/20 tests; full local regression: 268/268. Exact-SHA CI is
pending for this increment. Backup/restore and ACL validation remain outside
this slice.
