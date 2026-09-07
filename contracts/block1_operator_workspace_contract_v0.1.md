# Contract — Local operator workspace v0.1

Version `0.1`; producer `sictra_block1.operator_workspace`, consumers the
Windows launcher and `sictra_block1.lab_web`. Scope
`BLOCK1_LOCAL_OPERATOR_WORKSPACE`. Authority: local integrity configuration
only.

`init ROOT` creates the exact manifest plus two 32-byte key files using
exclusive writes, or validates and reuses a complete existing state. `check
ROOT` validates the layout, keys and dossier ledger. The default launcher runs
`init`, then passes the validated root to `lab_web --operator-state`.

`backup ROOT DESTINATION` requires a new directory outside `ROOT`, verifies the
ledger, confirms it did not change during the copy, and writes only
`dossiers.json` plus an exact backup manifest/digest. `restore ROOT BACKUP`
requires the original key state, exact backup contents and an absent current
`dossiers.json`; after exclusive copy it re-verifies the ledger and removes a
failed restoration.

Reject: missing/truncated/substituted keys, symlinked controlled paths,
incompatible or unreadable manifest, tampered dossier history, non-directory
root, and non-empty uninitialized root. Initialization must not overwrite
unknown files or reveal key bytes in stdout, manifest, HTTP or Git.

Non-claims: confidentiality, Windows ACL proof, concurrent online snapshot,
encrypted/off-device backup, lost-key or disk-loss recovery, source
approval/binding setup, watchlist execution, human identity, multi-user access,
publication or gate promotion.
