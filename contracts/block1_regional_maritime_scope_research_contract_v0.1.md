# Block 1 regional maritime scope research v0.1

Status: CANDIDATE / AGENT-ONLY LABORATORY. Producer: Block 1 fixed official
research acquisition and read-only regional methodology reviewer. Consumer:
construction agent's explicit source-scope review. No installed-runtime import,
automatic network access, source admission, binding, task or dossier mutation.

The only new acquisition recipe is `EUROSTAT_REGIONAL_MAR_METADATA` for the
exact official HTTPS URL `https://ec.europa.eu/eurostat/cache/metadata/en/tran_r_esms.htm`.
It uses the existing pinned public-address TLS, bounds, no-redirect rule,
immutable candidate schema and current Eurostat reuse-notice lineage. Generic
maritime and Belgian national methodology recipes cannot substitute for it.

The reviewer accepts one exact 64-hex regional candidate ID, its quarantine
root and a clock. It reopens the original data and terms bytes, requires exact
recipe/hash/identity/currentness, extracts only the unique named
`data_descr` section from bounded UTF-8 HTML and retains its exact text and
hash. Missing, duplicate, malformed or empty section rejects. A double read
and final-clock fence reject changed input, expired rights/data, clock rollback
and partial work. A restart with unchanged current bytes reproduces the report.

The regional-scope label is `EXPLICIT_MAIN_PORTS_ONLY` only if the publisher's
selected section contains a standalone exact paragraph connecting regional maritime
aggregation, exclusion of double counting, main ports only, and the detailed-data
threshold. Isolated terms, a prefixed denial, strike markup or an explicit
retraction in the selected section are insufficient. Otherwise it is
`UNCONFIRMED`. This is a literal publisher-statement label, not a general
natural-language proof that later prose cannot contradict the statement.
The label describes the regional series, not Statbel's port universe or a
release-specific reason for the 2023/2024 numeric gaps. A current official
methodology statement may challenge comparability; it is not an independent
measurement root. Output remains `QUARANTINED_NOT_ADMITTED`, `NOT_RESOLVED`,
`NOT_ACCEPTED`, runtime `NONE`, publication `BLOCKED`, and gap cause
`UNCONFIRMED`. Its fingerprint detects accidental change, not authenticated
authority. `verify_current` must recompute from original current bytes before
handoff. Historical expired material cannot be promoted by replay.

Rollback removes this standalone recipe/reviewer without modifying prior
candidate formats, existing sources, journals or operational services. Runtime
connection and any revised source-admission or comparison semantics require
their own accepted contract and MAR. Tests use an independent literal section
fixture and positive/rejection cases; real acquisition separately proves access
and retention, not semantic or gate acceptance.
