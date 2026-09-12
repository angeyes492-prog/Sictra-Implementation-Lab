# Blocks 2 and 3 Interface Polish — Implementation Plan

Status: `OWNER-APPROVED / IMPLEMENTATION ACTIVE`

## Scope boundary

Implement the approved balanced polish for the existing Block 2 Design
Console and Block 3 Precision Console. Preserve endpoints, schemas, DOM hooks
used by existing tests, loopback-only operation, block-owned data, and the
`LABORATORY_INTERNAL_SUPERVISED` promotion ceiling.

## Increment 1 — Presentation contracts and tests

1. Extend Block 2 interface tests to require an evidence route, mode guidance,
   atomic refresh status, busy state, retry path, and stable raw dispositions.
2. Extend Block 3 interface tests to require an account context strip,
   evidence class, explicit admission next step, categorized controls, atomic
   refresh status, busy state, retry path, and empty-collection handling.
3. Add JavaScript execution probes for navigation, refresh success, refresh
   failure, stale-content suppression, empty states, and hostile text escaping.

Required negative vectors: failed API response, failed health response,
missing CDD, empty signals/controls, and untrusted text.

## Increment 2 — Block 2 operational polish

1. Add the block-owned evidence route and mode guidance below the authority
   boundary.
2. Refine Spanish operator labels while preserving canonical codes.
3. Make refresh expose busy, success, and recovery states without changing
   API semantics.
4. Improve empty and failure messages with a valid next step and explicit
   non-action.
5. Refine focus, selected, disabled, responsive, forced-color, and
   reduced-motion presentation.

## Increment 3 — Block 3 operational polish

1. Add persistent account/evidence context sourced from the existing read
   model.
2. Expand admission presentation with evidence state and a human next step.
3. Separate signals and controls by semantic role without adding a score.
4. Add actionable empty states and stale-content suppression on refresh
   failure.
5. Refine focus movement, status announcements, responsive context, forced
   colors, and reduced motion.

## Increment 4 — Verification and evidence

1. Run Block 2 and Block 3 focused tests after each implementation increment.
2. Run JavaScript syntax and behavior probes.
3. Start both loopback servers and inspect desktop and narrow layouts,
   keyboard navigation, primary states, and failure states; capture evidence.
4. Run the complete clean regression suite.
5. Update closure evidence with environment, test identities, limitations,
   SHA, and promotion boundary.
6. Commit coherent changes, push the branch, create a pull request, and obtain
   GitHub CI on the exact final SHA.

## Non-claims

This plan does not authorize publication, CRM mutation, contact, delivery,
provider acquisition, remote deployment, automatic acceptance, production
promotion, or a global completion claim.
