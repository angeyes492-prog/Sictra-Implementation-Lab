# Test and Validation Layer Rules

Inherits the root `AGENTS.md` rules.

## Evidence standard

Tests must establish behavior, not merely coverage. A test file or a passing happy-path test is not system validation.

For every material capability, select the applicable classes: unit, integration, contract, regression, property, adversarial, mutation, failure-injection, boundary, compatibility, and end-to-end.

## Required negative-path considerations

Test, where relevant: malformed input, absent/contradictory/stale evidence, authority violations, partial failure, retries, rollback, idempotency, concurrency, state transitions, replay, recovery, and compatibility boundaries.

## Oracle independence

The oracle must not depend on the assumptions or implementation logic it validates. Reject circular tests, self-confirming fixtures, hard-coded conclusions, copied logic, source laundering, and false precision. If test and implementation could share the same defect, the result is not correctness evidence.

## Execution and reporting

Record test identity, version, environment, inputs/fixtures, date, result, evidence location, limitations, failure mode, and independent reviewer/oracle where applicable. On failure: preserve the evidence, diagnose cause, repair, retest from a clean state, reassess affected claims, and add a reusable prevention rule. Never weaken tests solely to create a pass.

## Promotion boundary

Fixture/model results, bounded SUT results, integration results, runtime observations, and independent validation are separate evidence classes. Do not promote across them without the required evidence and gate criteria.
