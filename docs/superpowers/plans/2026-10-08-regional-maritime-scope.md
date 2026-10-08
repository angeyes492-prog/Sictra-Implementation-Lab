# Regional maritime scope research implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retain and inspect the official Eurostat regional methodology that defines the coverage of `tran_r_mago_nm`, then use it to bound the existing Statbel/Eurostat comparison.

**Architecture:** Add one fixed Eurostat acquisition recipe to the agent-only quarantine and a read-only review of the named methodology section. The report retains exact data and rights identities and never enters the installed runtime or changes source admission. The existing same-chain numeric report remains separate.

**Tech Stack:** Python 3.12, standard-library `unittest`, existing quarantine and HTML section parser.

**Spec:** `contracts/block1_regional_maritime_scope_research_contract_v0.1.md` (candidate contract written with Task 1).

## Global Constraints

- Scope: `LABORATORY_INTERNAL_SUPERVISED` and agent-only research.
- Fixed official HTTPS URL, pinned public-address TLS, 8 MiB file / 100 MiB session / 100 attempts / 30-second request bounds; no redirects.
- Exact current Eurostat reuse-notice lineage and immutable original bytes.
- No source admission, independent-root claim, runtime network access, dossier resolution, publication or gate promotion.

## Review Focus

- A generic maritime or Belgian national metadata receipt must not substitute for the regional recipe.
- Missing, duplicated or empty named methodology section must reject rather than produce a scope conclusion.
- Terms or data expiry, changed bytes and clock rollback must withdraw the report.
- A self-sealed replacement report must not become source authority.
- A page wording change must yield unknown scope, not a guessed cause of the numeric gaps.

---

### Task 1: Contract and exact acquisition recipe

**Files:** Create `contracts/block1_regional_maritime_scope_research_contract_v0.1.md`; modify `src/sictra_block1/research_acquisition.py`; test `tests/test_agent_research_acquisition.py`.

**Interfaces:** Produces `REGIONAL_METADATA_RECIPE = "EUROSTAT_REGIONAL_MAR_METADATA"`, tied only to `https://ec.europa.eu/eurostat/cache/metadata/en/tran_r_esms.htm`. Consumes existing `ResearchAcquirer.acquire()` and `ResearchQuarantine.read()`.

- [x] Write a failing acquisition test: fixed URL, retained bytes, current terms lineage, no runtime authority; reject wrong recipe/host and expired terms before transport.
- [x] Run focused test and observe expected failure (`RECIPE_UNSUPPORTED`).
- [x] Add the minimal recipe and contract; preserve old receipt schemas and recipe behavior.
- [x] Run focused acquisition tests and inspect result (18/18).

### Task 2: Regional scope review

**Files:** Create `src/sictra_block1/regional_methodology.py`; test `tests/test_regional_methodology.py`.

**Interfaces:** `review_regional_methodology(quarantine, candidate_id, *, clock) -> dict`. Consumes a current `REGIONAL_METADATA_RECIPE` receipt and its exact current reuse-notice receipt; produces a hash-bound research report with the named `data_descr` text, source identity, acquisition and expiry times, scope status and blocked effect labels.

- [x] Write failing positive test using independently specified main-ports wording and source identity.
- [x] Run test and observe missing capability, then the real-source `data_descr` correction.
- [x] Implement exact anchor extraction, literal status assessment, double-read and final-clock fence.
- [x] Run positive test to green.
- [x] Add and run adverse tests for missing/duplicate anchor, recipe substitution, tamper, expiry, changed input and replay after restart; repair negated wording and reviewer-found prefixed-denial/strikeout false positives (7/7).

### Task 3: Real source evidence and closure

**Files:** Create `evidence/telecare_regional_maritime_scope_2026-10-08.md`; update `closure/closure_execution_queue_v0.1.md` only for claims supported by execution.

**Interfaces:** Explicit CLI acquisition and review of the official URL; original bytes stay in ignored quarantine. Report keeps `NOT_ADMITTED`, `NOT_RESOLVED`, `NONE` runtime and `BLOCKED` publication.

- [x] Acquire official terms and regional methodology within the session budget; record URL, times, candidate IDs, byte hashes and errors.
- [x] Run the read-only review over retained bytes; compare the literal regional-scope passage with the current Statbel/Eurostat report.
- [x] Repeat full Python and JavaScript regression, compile check and closure preflight after the final reviewer-driven repair: 1021/1021 Python, 18/18 JavaScript, 24/24 preflight and successful compile check.
- [ ] Commit and push the reviewed increment; verify hosted CI on the exact SHA; update the evidence ledger without promoting a product gate.

### Task 4: Second-capture version boundary

**Files:** Update `evidence/telecare_regional_maritime_scope_2026-10-08.md` and `closure/closure_execution_queue_v0.1.md`.

- [x] Recapture the exact official Eurostat and Statbel source slices with current terms into separate quarantine roots; record a bounded failed local rename and successful retry.
- [x] Compare original-byte hashes, publisher release markers and independently extracted 2023/2024 numerical rows against the previous capture.
- [x] Classify unchanged Eurostat data, changed Statbel page bytes but unchanged measured rows, and unavailable Statbel release marker without calling this a statistical revision or injecting research receipts into runtime watchlist.
