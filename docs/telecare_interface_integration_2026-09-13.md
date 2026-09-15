# Telecare OS — interface integration and closure delta

Date: 2026-09-13. Target: LABORATORY_INTERNAL_SUPERVISED.
Implementation and local validation are separate from final acceptance.

## Design direction

The primary users are operators examining source-backed candidates. Each screen
must make its next available action and the associated evidence legible.
The Block 1 editorial reference informs hierarchy and density; the other blocks
retain their own functional structure.

| Block | Palette | Typography | Signature and purpose |
| --- | --- | --- | --- |
| Design | #252446 ink, #5845a2 violet, #f0edf8 tint, #f4f5f9 paper, #586078 labels | Bahnschrift display, Segoe UI body, Consolas identifiers | Dotted canvas between engine stages and evidence inspector; controlled edits remain in their existing flow |
| Precision | #153b48 harbor, #12796f teal, #eaf4f1 tint, #f7faf9 paper, #66727a labels | Bahnschrift display, Aptos body, Consolas identifiers | Account context strip, admission route and source limitations; no inferred commercial score |
| Orchestrator | #14243b slate rail, #172557 ink, #126e68 teal, #f2f5f8 paper, #875013 review | Bahnschrift display, Aptos body, Consolas identifiers | Searchable case queue with state-aware inspector and actual persisted event timeline |

No external fonts, image dependencies or remote requests are introduced.
Mobile retains block-to-block navigation. Focus, error and empty states remain
visible. Existing read-only boundaries and controlled Design editing remain.

## Implemented repairs

- Block 4 clears previous metrics and selected evidence on failed refresh.
- Inspector guidance now distinguishes active, returned, rejected, abstained
  and review-required cases. Expired evidence is labelled as historical.
- Search combines case/run identity and status. Event requests are cancelled
  when selection changes; stale responses cannot replace the current history.
- Evidence/dossier IDs and original uncertainty are exposed from the signed
  package. Synthetic fixtures are explicitly labelled in the inspector.
- Audit lookup decodes case identifiers and rejects unknown cases.
- Signed event verification now checks materialized checkpoints and package
  fingerprints/signatures; tampering blocks reads and transactional mutations.
- Retry does not erase contradictions, insufficiency, staleness or invalidation.
- Block 1 startup retries SQLite BUSY/LOCKED journal-mode contention with a
  bounded deadline; other database failures still propagate.
- Eurostat test workbooks use a fixed ZIP timestamp. Duplicate-release tests
  now use reproducible bytes; source verification rules are unchanged.

## Integration correction

Earlier conversation and the initial queue described PR #6 -> #5 as a mandatory
technical path. Git ancestry shows main 4536d1c already contains the earlier
Block 1 baseline via PR #12. Only four newer Block 1 commits through 21c9d36
were absent. They were merged into codex/block4-main-integration, preserving
the approved PR #14 history. This is branch integration, not new human approval.

## Validation and reproduction

Use PYTHONPATH pointing to this checkout's src, not another worktree.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -m unittest discover -s tests -q
node --test tests/console_state.test.cjs
python tools/console_review_probe.py
```

The browser probe requires an already installed Playwright package and browser.
It creates isolated synthetic stores, visits real local HTTP servers, tests
view changes, search/filter, audit, failure/recovery and page overflow at
1440/1024/390 px. Screenshots stay in ignored .runtime/console-review.

After merging the latest Block 1 UI: 707 Python tests passed in 45.076 seconds.
Browser checks passed for all three consoles at all three viewport widths.
Four JS state tests passed. Local output is retained in
`.runtime/regression-merged.log`; screenshots in `.runtime/console-review`.
Exact-SHA hosted CI must still pass for the resulting commit; its receipt is
reported on the integration PR and does not imply final acceptance.

The initial full run exposed a SQLite cold-start error. A subsequent run
exposed time-dependent ZIP fixture bytes. Both failure observations are
preserved here; a later success does not erase those findings.

## Remaining technical work

Real Block 1 export and B2/B3 execution adapters are still absent. Journal
coordination alone does not integrate producer runtimes. Sustained operation
also needs tested backup/restore, bounded scheduling and stop controls,
configured operator identity and secret rotation, deployment-specific access
controls, and end-to-end recovery evidence. Final independent review and owner
approval remain deferred to the final handoff requested by the owner.

No production-ready or complete-system claim follows from this UI increment.
GitHub/CI and local tests support this delta; no Slack, Notion or Wolfram
verification is claimed in this cycle.
