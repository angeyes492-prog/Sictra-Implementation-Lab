# Federated Block Interfaces — Implementation Plan

Status: `ACTIVE`

1. Baseline existing Block 1 and Block 2 UI tests and record their preserved boundaries.
2. Build the Block 3 loopback-only Precision Console on port 8767 with deterministic synthetic evidence, four operator views, hostile-request rejection, and explicit non-authority.
3. Add positive, adversarial, markup, accessibility, and JavaScript contract tests for Block 3; run focused and full regression.
4. Align Block 2 with the SICTrA Operational profile and add navigation-only links to Blocks 1 and 3 without cross-origin data access; preserve every existing API and test.
5. Add navigation-only links to the completed Block 1 interface in its existing worktree; preserve runtime/API behavior and rerun its focused and full suites.
6. Inspect all primary and failure states at desktop and narrow widths, repair defects, and verify no console errors.
7. Commit and push coherent increments, obtain CI for each exact SHA, and update closure evidence without promoting human or external gates.

Each increment requires at least one positive and one fail-closed vector. User-owned `AGENTS.md` changes and unrelated worktrees remain excluded from commits.
