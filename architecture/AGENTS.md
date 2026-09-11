# Architecture Layer Rules

Inherits the root `AGENTS.md`.

## Purpose

Maintain the canonical SICTrA architecture: engine boundaries, ownership, dependencies, interfaces, authority, failure domains, observability, rollback, and cross-engine consequences.

## Before changing architecture

1. Read the affected engine specifications, accepted contracts, dependency graph, gate ledger, and related tests.
2. Classify the proposal as a clarification, incremental methodological change, or architectural change.
3. Identify direct, second-order, and third-order effects on reliability, latency, observability, security, governance, memory consistency, regression surface, human review, and migration cost.
4. Record ambiguity rather than inventing missing semantics.

## Canonical rules

- An engine owns only its explicitly assigned semantics; it may not mint authority for another engine or the runtime.
- Common architecture owns shared primitives and cross-engine semantics. Do not duplicate a shared authority, state machine, or enforcement plane locally.
- A candidate contract, model, or fixture is not a runtime implementation or acceptance proof.
- Local evidence does not promote global gates. Shared implications require a Master Architecture Review.
- Preserve explicit ownership, version, status, source, confidence, validation state, supersession links, and decision rationale for every material artifact.

## Architecture handoff minimum

Every material architecture change must state: purpose, scope, inputs/outputs, invariants, authority, dependencies, failure and recovery semantics, observability, validation plan, contradictions, version, evidence, confidence, and downstream impacts.
