# Block 1 Intelligence — Technical completion manifest v0.1

Date: 2026-09-06. Target boundary: `LABORATORY_INTERNAL_SUPERVISED`.
Overall status: `YELLOW / NOT YET COMPLETE`.

This manifest applies the persistent eight-step completion protocol. It does
not convert local implementation evidence into production or independent
acceptance.

| Step | Current evidence | State | Remaining condition |
| --- | --- | --- | --- |
| 1. Retained approved source | Durable source-control and attested-evidence stores; Eurostat workbook validated in a temporary real-data exercise. | `YELLOW` | Reproducibly configure the complete source pipeline and retain the approved real workbook as an operator baseline. |
| 2. Watchlist comparison | Signed watchlist bridge distinguishes baseline, delta and rejection; version transition tested. | `VERIFIED / B` | A second real release is required only to exercise a real delta. |
| 3. Intelligence dossier | Atomic HMAC dossier store separates literal facts from empty interpretations/hypotheses. | `VERIFIED / B` synthetic delta | A real dossier cannot exist until a second governed release changes. |
| 4. E01–E08 integration | Current attested evidence reaches the runtime; stale, ambiguous and altered evidence rejects. | `VERIFIED / B` | No open local implementation blocker. |
| 5. Editorial bridge | Verified dossier composes only as `RESEARCH_NEEDED` / `BLOCKED`, no handoff. | `VERIFIED / B` | Independent root and human interpretation remain external inputs, not bypassable code tasks. |
| 6. Laboratory UI | Signed dossier reader exposes integrity, facts, uncertainty and editorial blocking with no fixture fallback. | `VERIFIED / B` | No open local implementation blocker. |
| 7. Local operation | Windows startup initializes keys outside OneDrive/Git; data-only local backup/restore verifies under original keys. | `VERIFIED / B` bounded reader | Extend the same operator configuration to source control, evidence and watchlist stores. |
| 8. Closure | 270/270 local tests; CI #350 succeeded on backup implementation SHA `1458fc0d1618c62f3f6ef16663d177b88e48d01f`. | `YELLOW` | Complete Step 1/7 integration, rerun adversarial/full tests and CI on final exact SHA. |

## Highest-priority technical blocker

One operator command must take an explicitly supplied Eurostat workbook and
COUNTRY selection through the retained chain:

`approved binding → manual bundle → gateway attestation → evidence store →
E01–E08 check → baseline/delta watchlist → optional dossier → UI`.

It must keep network acquisition disabled, bind to the exact approved dataset,
refuse ambiguous/current duplicates, preserve all keys outside Git/OneDrive,
and return `BASELINE_ESTABLISHED_NOT_EVIDENCE` for the first real release.

## External, non-code dependencies

- A second newer Eurostat workbook is required to demonstrate a real delta;
  the absence of that release must remain `AWAIT_NEWER_SOURCE`, not failure or
  fabricated change.
- A second independent source and human interpretation are required before an
  editorial candidate can become ready.
- Independent review is deferred by owner choice and cannot be represented as
  completed.

