# Quarantined Eurostat methodology review v0.1

Status: CANDIDATE / LOCAL RESEARCH ONLY. Producer:
`sictra_block1.research_methodology`; consumer: construction research, not the
runtime need-assessment contract. Depends on agent acquisition v0.1, current
quarantine receipt and its retained terms receipt. No source admission,
independent corroboration, dossier/task mutation or shared MAR acceptance.

## Observable objective

Read current retained Eurostat maritime HTML and extract exact publisher
paragraphs for metadata update, data description, sector/time coverage,
revision policy/practice, source data and collection frequency. Each section
retains its exact named heading anchor, candidate identity, content hash and
section hash. Do not replace an unknown methodology with a numeric comparison.

The parser accepts UTF-8 HTML up to 1 MiB, unique named anchors inside h3
headings and nonempty bounded paragraph text in all eight sections. Ignore
script/style/svg/template/noscript bodies; never execute HTML, follow links or
search text to manufacture a missing section. Missing, duplicated, malformed,
oversized or empty sections reject the whole candidate review.

Publisher metadata update text is distinct from acquisition time. This is
general domain methodology, not a release-specific explanation of a delta or
proof of independent national roots. Output remains REVIEW_REQUIRED,
NOT_RESOLVED, NOT_ACCEPTED, QUARANTINED_NOT_ADMITTED, publication BLOCKED and
runtime_effect NONE. Its fingerprint is integrity, not attestation.

Re-read both original descriptors and bytes after parsing using the final clock;
reject changed or expired data/terms before returning. Bind the terms hash and
both input expiries in the report. Effective report expiry is the earliest of
metadata and terms expiry, never the later metadata timestamp. Reads never write.
Future/stale/tampered/foreign recipe and a metadata receipt substituted for
terms fail closed. Restart reproduces the same report while inputs remain
current. No journal migration; rollback removes this standalone review tool.
Tests use independently declared paragraphs/anchors and injected read/time
changes; a real download/review separately establishes access/extraction, not
resolved Intelligence or system validation.
