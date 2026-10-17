# Belgian national maritime methodology research v0.1

Status CANDIDATE / LABORATORY_INTERNAL_SUPERVISED / MAR REQUIRED for adoption.
Producer research_acquisition fixed EUROSTAT_BE_MAR_METADATA recipe; consumer
national_methodology research review only. No accepted source or dossier input.

## Objective and compatibility

Retain the official national methodology linked from Eurostat's generic
maritime metadata and extract exact origin/scope/revision paragraphs for the
pending comparable-source research need. The chosen public URL is exactly
https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms_be.htm; no query,
redirect, other country or arbitrary path is allowed. It uses the existing
acquirer, quarantine schema, hosting publisher identity, current Eurostat
reuse-notice dependency and network/byte/deadline limits. Previous recipes,
generic extraction and format-specific admission remain unchanged. This new
recipe cannot substitute for the generic methodology required by admission.

The quarantine publisher/source ID describes the hosting/dissemination route,
not statistical origin. Keep contact_organisation text as a separate raw
compiling-agency claim, not a new independent root or a registry decision.
Publication URL, organisation name and number agreement do not prove origin
independence. The operator research exception grants collection, not approval.

## Review semantics and failure

Extract only the fixed named ESMS sections: contact_organisation,
meta_last_update, data_descr, stat_conc_def, stat_unit, stat_pop, ref_area,
unit_measure, ref_period, rev_policy, rev_practice, source_type, freq_coll,
coll_method, data_validation, data_comp. Each must have exactly one primary h3
anchor, except unit_measure/ref_period, which use the publisher's button/h2
section headers. Capture bounded paragraph/list text beneath those headers,
not the repeated short-summary anchors or navigation. Preserve unavailable/unspecified text
literally; do not convert it into a valid methodology or manufacturing values.
Ignore scripts, style, SVG, templates and noscript; never follow content links.
Wrong/missing/duplicate sections, media, recipe, changed bytes, broken terms,
unclosed paragraph, invalid encoding or expiry reject rather than guess.

Read all terms/metadata dependencies again after extraction; changed input,
clock regression or expiry at the final return fence yields no report.
Bind exact hashes, URLs/anchors, raw metadata update and raw compiling agency.
Acquisition time is not a new publisher release; a 2021 update cannot explain a
2023/2024 revision by being downloaded today. Metadata text does not establish
the data publication's coverage, a particular cause or independent provenance.

Review state REVIEW_REQUIRED; resolution NOT_RESOLVED; acceptance NOT_ACCEPTED;
independent corroboration INSUFFICIENT EVIDENCE; root provenance UNCONFIRMED;
runtime NONE; publication BLOCKED. No source control, attestation, task/dossier,
installed application, registry/gate or scheduling state is mutated.
Reopening/recovery with the exact quarantined bytes/terms reproduces the report
while current. Its fingerprint is content identity, never evidence authority.

## Observable closure and rollback

Positive fixture proves all exact sections, including raw agency/update/unit
and unavailable compilation. Adversarial fixtures reject duplicate/injected
anchors, missing scope, another national URL, stale/replaced terms or metadata,
clock regression and slow final expiry. Integration proves generic methodology
and admission still reject the new national recipe as a substitute. One real
bounded download separately proves access/retention/extraction, not approval.
Rollback removes this standalone recipe/consumer; old source histories remain.
