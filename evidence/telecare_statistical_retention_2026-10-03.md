# Statistical retention and checkpoint recovery — candidate execution

Date: 2026-10-03 local / 2026-10-04 UTC. Windows / Python 3.12.
Base b813c8219d3085234a04ef68606a3ddb101b4eef; exact-SHA GitHub push
37165448705 and PR 37165451020 succeeded and were rechecked this turn.
Scope LABORATORY_INTERNAL_SUPERVISED, candidate/MAR item 12 OPEN.
Validator: implementation agent, not independent. VERIFIED / confidence B
only for executed local mechanisms; no source truth or acceptance claim.

## Concrete progress and independent expected behavior

statistical_retention now composes the existing AttestedEvidenceStore chain,
configuration check, fsync and atomic-write mechanism rather than duplicating
the HMAC plane or weakening its XLSX format validation. A private format
consumer reconstructs each historical packet from retained raw/metadata/terms
and signed source control at its integrity-protected admission time. Current
selection uses a complete independent admission verifier with the configured
live clock; public calls cannot supply a past time. Only exact IDs are selected.
Expired/changed reads yield no usable packet. Historical receipts expose
CURRENT/NOT_CURRENT and limits, never stale content as current evidence.

Head selection uses the greatest timezone-aware publisher update in UTC,
not collection order. Different raw hashes at the same greatest instant are
ambiguous; unordered time and stale/unapproved newest heads withhold selection.
Recollection of the same raw release selects only its newest collection.
This is a conservative candidate policy, not explanation or corroboration.
Fixtures independently state 2023=10.0 / 2024=12.5, publisher chronology and
the same UTC instant expressed with distinct offsets. No fictional actual
source/reviewer approval was minted; fixture identities remain FIXTURE_ONLY.

## Red-team findings, repairs and recovery

1. The new expired-rotation case failed: generic source control could fall
   back to an older still-live binding after its replacement expired.
   research_admission now checks the newest already-issued binding in verified
   history. Historical verification before the rotation remains possible;
   current admission after it cannot reinstate old authority. Fifteen focused
   bridge tests passed after this repair (5.675s).
2. Two new valid-signed-copy rollback tests failed in 24.955s: restoring an
   older evidence file or older source-control file could enable old selection.
   The facade now requires a trusted source-control head and a history head
   on reopening; it remembers newly observed signed heads. Verified chains
   must include those heads or descendants. Missing history with a known head
   cannot create a new genesis. Both targeted repairs passed in 15.635s;
   fresh-start cases additionally supply previously retained checkpoints.
   The caller must retain checkpoints outside the backup; the restored file
   itself is not authority for its recovery head. Custody is not demonstrated.
3. Initial focused runs spent excessive time repeating full historical
   reconstruction; diagnosed live stacks showed filesystem validation, not
   a deadlock. The two earlier test processes and one diagnostic run were
   explicitly stopped, not recorded as passes. A bounded in-memory historical
   memo uses exact packet/admission time plus freshly rehashed descriptors and
   verified source history. It skips no byte/hash/chain checks and authorizes
   no current selection. Tentative current projections are withheld until the
   full dedicated live verifier succeeds. The intermediate pre-checkpoint
   17-case suite completed in 149.861s; it does not prove the final repair.

Positive/rejection vectors cover replay/restart and defensive copy; raw/chain
tamper, missing dependencies and wrong keys; binding/terms/data expiry;
rotation and no resurrection; greatest publisher instant versus later old
downloads; timezone/ambiguity and stale-newest no fallback; final-return expiry;
pre-replace OSError preserving prior bytes and single-append retry; write-time
expiry retaining history without CURRENT; explicit selection and past-clock
rejection; capacity/path/key/legacy format isolation; signed rollback and
missing checkpoint/history; data-only restoration with original keys.

## Four-source reconciliation and actual scope

Notion 3c789f66-067b-8108-bb44-c13ac4b15ac0, retrieved this turn, remains
unverified historical reference scope (edited 2026-08-28). Public Slack query
Telecare found no results. Neither supplies source admission or MAR authority.
GitHub supplies the immutable base CI above and eventual new-SHA CI separately.
Wolfram enumerated 576 abstract two-record release/hash/collection/eligibility
cases: none selected unknown time, conflicting newest hashes, ineligible heads
or fresher older fallback. A second 1872-case recovery-prefix model accepted
no prefix below the supplied known head and rejected no head/descendant.
These bounded declared models do not validate parsing, signatures, custody,
Python effects or acceptance; concrete adversarial tests provide runtime evidence.

The original workspace retains owner changes; installed application remains
04dab5ff0d03c96ac1a1663bda7eac23d114321a. No downloads, installation,
runtime networking, approval, delivery/contact/CRM, gate or paused-heartbeat
activation occurred. Actual retained statistical review from the prior
increment remains PENDING / NOT_ADMITTED. No real statistical packet was
attested or persisted without its exact reviewed source grant.

Next safe route: integrate current statistical selection into candidate
same-period watchlist/fact production without pretending JSON is an XLSX
measurement. Source admission, checkpoint custody, independent comparable
input and accepted resolution/interpretation remain separate requirements.
The owner goal remains active; this mechanism alone does not complete a
product arista or change product_completion from NOT_DEMONSTRATED.

Final focused regression: 42/42 tests in 237.039s across the 21 new retention
vectors, 15 bridge vectors and six unchanged legacy evidence-store tests.
JavaScript 17/17, compileall, launcher-path validation and diff checks passed.
Full Python regression completed: 907/907 tests in 719.006 seconds on the
final implementation, 22 new Python cases over the base. Discovery confirmed
907 unique test identities; no duplicate imported test classes inflated it.
Final checkout preflight and exact new-SHA hosted CI remain separate execution
evidence, bound through PR #18/workflow history rather than inferred from counts.
