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

## Separate seven-recipe collection archive candidate — 2026-10-11

Producer/consumer: B1 `research_collection_recovery.backup_collection` and
`restore_collection`, explicit agent CLI only. New archive scope
`RESEARCH_COLLECTION_DATA_ONLY_V1`; original Eurostat archive0.1.0 remains
unchanged and cannot consume this type. No installed adoption or shared
acceptance is inferred. Purpose: restore the exact collection console input,
including Statbel and the spent-cycle boundary, not just Eurostat receipts.

Input: existing collection root, exact known selection ID, new destination,
trusted caller clock; restore additionally requires an externally held archive
manifest SHA256. Select only seven known recipes, their14 original/descriptor
files, selection.json, matching COLLECTED outcome and cycle-start marker:
17 files. Unselected histories/private files are not copied. Preserve raw
bytes, exact rights dependencies, source IDs, timestamps, expiry, publisher
versions, start marker and budget. No PDF, key, approval, attestation, operator
state, installed configuration or private payload may be added to this format.

The canonical archive manifest inventories every selected path/hash and binds
scope/version, selection ID, created_at and fixed non-admission boundary. Data
paths are reconstructed from validated IDs/recipes, never arbitrary manifest
path input. Validate canonical selection identity, exact durable outcome/start,
budget lineage, typed receipts and dependency graph using immutable bounded
snapshots. Apply existing metadata/statistical/table readers to those snapshots
at original collection creation time ONLY to validate historical consistency.
Do not return a historical validation as current evidence. Current consumers
use their real clock after restoration and must reject expired originals.

Bounds: exact17 files,8MiB/body,16KiB/receipt/start/outcome,32KiB/selection,
128KiB/archive manifest and100MiB total selected data. Reject duplicate keys,
unknown archive version/scope, missing/extra archive files, changed hashes,
foreign/missing terms, forged boundaries, malformed/ambiguous source bodies,
invalid chronology/budget, links/junctions, overlap, existing destination and
future archive creation. Digests identify known bytes, not authentic sources;
digest custody remains separate operator responsibility, never reconstructed
from the archive being trusted.

Before publication recheck source bytes, immutable snapshot conformance and
nondecreasing caller clock. Publish complete staged directories with existing
Windows/Linux no-replace primitive; other platforms reject. Failure leaves no
selectable final archive/root; staging cleanup errors retain primary cause and
explicit unpublished residue. No whole-machine power-loss durability or
concurrent post-fence atomic-source-snapshot guarantee is claimed.

Restoration never renews expiry, resets the spent-cycle marker, resumes workers,
recollects, admits data or claims restored publisher truth. Rollback removes
the separate tool, leaving old archives and all retained source history intact.
Closure: current/expired reopen,17 identical files, blocked reacquisition,
no network/secrets/source writes, tamper/digest/lineage/path/clock and injected
publication failure, actual original-byte restoration, full regression and
exact-SHA CI. All output retains NOT_ADMITTED/NOT_RESOLVED/NOT_ACCEPTED/NONE.
