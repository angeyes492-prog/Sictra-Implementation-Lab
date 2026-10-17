# Block 1 same-chain research comparison v0.1

Status: CANDIDATE / AGENT-ONLY LABORATORY. Producer: Block 1 retained official
research readers. Consumer: construction agent's explicit read-only review.
No installed-runtime import, automatic selection, network acquisition, source
admission, dossier resolution, editorial acceptance or cross-block effect.

Input is one exact current Statbel data candidate and one exact current
Eurostat fixed maritime statistical candidate, each with its own current
publisher-specific terms receipt. The caller supplies both quarantine roots
and both 64-hex candidate IDs. Re-read all original bytes, descriptors and
terms before returning; reject tamper, substitution, stale/future clock,
missing or malformed measurements and changed inputs. Reopen must reproduce
the same result while all dependencies are current. The earliest dependency
expiry governs the report. A final `verify_current` fence is required before
any display or handoff.

Output retains literal publisher values separately, computes the arithmetic
Statbel loaded+unloaded sum and its numeric gap from Eurostat's fixed
`FR_LD_NLD` observation by year using decimal arithmetic. Exact data/terms
candidate IDs and SHA-256 values, UTC check time and boundary labels remain
attached. Numeric proximity or difference has no causal or methodological
meaning: comparability and release-specific revision explanation remain
`UNCONFIRMED`; independence is `NOT_ESTABLISHED`. Never classify this pair as
independent corroboration. `NOT_ADMITTED`, `NOT_RESOLVED`, `NOT_ACCEPTED`,
runtime `NONE` and publication `BLOCKED` are invariant.

Exact Eurostat JSON decimals are reparsed from the hash-bound original bytes;
binary-float projection must not determine the arithmetic gap. The fixed
reader accepts at most 64 significant decimal digits and an exponent from
-64 through +64, then subtracts with a bounded 256-digit local context.
Larger numeric scales or precision, including underflow-to-float-zero, reject
instead of rounding or allocating unbounded arithmetic work.

This schema does not accept arbitrary countries, years, metrics, units or
publishers. New scopes, runtime connection or interpretation require a new
contract and applicable architecture review. Rollback removes this standalone
reader without modifying quarantined originals or operations state.
