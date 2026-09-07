# Block 1 — Local operator workspace v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. The Windows launcher now creates
and reuses one local state directory at
`%LOCALAPPDATA%\TelecareOS\Intelligence\operator`, outside the OneDrive-backed
repository. Two independent 32-byte random keys remain in
its `keys/` subtree and configure the dossier store and watchlist-bridge
verification. The manifest contains paths and identities only, never key
material. This placement reduces accidental Git and OneDrive synchronization;
it is not a confidentiality guarantee.

Initialization is exclusive and fail-closed: it never overwrites a non-empty
unknown directory, an existing key, an incompatible manifest or an invalid
dossier ledger. Partial first-time creation removes only files it created. The
launcher validates the state before binding the reader to `lab_web`; startup
stops if validation fails.

This provides reproducible single-user integrity configuration, not a secret
manager. Files are excluded from Git and created with restrictive mode where
the operating system honors it, but v0.1 does not prove Windows ACL isolation,
encryption at rest, credential recovery, backup/restore, multi-user identity or
production security. Losing either key makes the corresponding ledger
unverifiable by design.
