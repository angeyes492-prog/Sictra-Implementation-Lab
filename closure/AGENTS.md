# Closure and Gate Layer Rules

Inherits the root `AGENTS.md` rules.

## Gate ledger

Maintain each gate with: `GATE`, `STATUS`, `EVIDENCE`, `TEST`, `DATE`, `VERSION`, `DEPENDENCIES`, `CONTRADICTIONS`, `CONFIDENCE`, `REVIEWER/VALIDATOR`, and `NEXT REASSESSMENT`.

Each material work cycle records a closure delta and updates only the claims directly supported by the new evidence.

## Status definitions

- `GREEN`: acceptance criteria demonstrably met; required tests executed; independent validation exists; contradictions resolved or explicitly accepted; no material blocker remains.
- `YELLOW`: partial evidence, bounded uncertainty, incomplete integration, or additional validation required.
- `RED`: critical failure, contradiction, unauthorized implementation, false-verification risk, no reliable evidence, or an unresolved material blocker.

`UNKNOWN` and `INSUFFICIENT EVIDENCE` are valid outcomes, never implicit passes.

## Promotion requirements

Never infer global closure from local closure. A gate changes only after its acceptance criteria and all required evidence are demonstrated. Before promotion, perform adversarial review: challenge evidence independence, source quality, alternative explanations, temporal context, causality, stale evidence, governance leakage, circular validation, and design/runtime divergence.

If a material weakness is found: do not promote. Repair, retest, reassess, and preserve the prior evidence and contradiction.

## Final closure

Before declaring SICTrA complete, run a pre-flight covering scope, provenance, evidence, independence, epistemic separation, contradictions, red team, dates/context, confidence, neutrality, gaps, handoff, reproducibility, rollback, regression, cross-engine integration, governance, and memory synchronization. A final closure manifest must report claims, facts, interpretations, hypotheses, implementation and validation states, gates, evidence, contradictions, uncertainties, limitations, watchlist, remaining gaps, source artifacts, tests, and red-team results.
