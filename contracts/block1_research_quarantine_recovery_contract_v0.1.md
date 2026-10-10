# Quarantined research recovery — candidate contract v0.1

Status: candidate, laboratory agent-only. No installed-runtime adoption or gate promotion.
Producer: `sictra_block1.research_recovery.backup`; consumer: explicit offline
`restore` caller and the unchanged `ResearchQuarantine` reader. Archive version
0.1.0 is additive: no existing receipt, key, journal or state is migrated.

Recover original Eurostat quarantine bytes and descriptors using explicit candidate IDs,
including their exact reuse-notice dependency. Preserve acquisition, expiry, URLs,
hashes and `NOT_ADMITTED` boundary. Expired candidates may be archived as history;
they must remain rejected by current-evidence readers after recovery.

An archive is a new directory containing `archive-manifest.json` and `data/<id>/`
with only `manifest.json` and `content.bin`. Its canonical manifest inventories every
file SHA-256. The operator must retain the returned manifest digest separately and
supply it at restore: a digest stored beside an altered archive is not authentication.
This establishes known-byte identity, not publisher authenticity or admission.

Bound: 100 candidates including dependencies, 8 MiB each body, 16,000-byte candidate
descriptors, 128 KiB archive manifest and 100 MiB total retained files. Reject malformed
IDs, duplicate JSON fields, extra/missing files, altered bytes, invalid lineage,
symlinks/junctions, path overlap, existing destination and changed inputs before
publication. Validate all selected data before copying and again before publication.
Stage in the destination parent; publish only a complete validated directory.
Failure must not expose a selectable partial final destination. No network, secret,
approval, attestation or runtime authority is copied or generated.
If staging cleanup itself fails, report the unpublished residual directory and
preserve the primary error as the cause; never treat that residue as a complete
archive/quarantine. Windows and Linux support no-replace publication; other
platforms reject. Atomic visibility is not a whole-machine power-loss durability
guarantee or substitute for separately protected backups/digest custody.

Scope: existing Eurostat `ResearchQuarantine` recipes only. Statbel and approved
attestation stores have distinct contracts and are not implicitly supported.

Closure: executable positive, tamper, expiry, dependency, path, failure/recovery
and CLI tests; actual retained-byte recovery; regression and CI on exact SHA.
