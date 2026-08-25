from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

from sictra.block2_e01_cascade import Failure


def expected_earliest_failure(claim_id: str, failures: Iterable[Failure]) -> tuple[str | None, tuple[str, ...], tuple[str, ...], str]:
    items = tuple(failures)
    scoped = {x.failure_id: x for x in items if claim_id in x.invalidates_claims}

    candidates = []
    for x in scoped.values():
        if not x.causally_sufficient:
            continue
        if not x.required_predecessors.issubset(scoped.keys()):
            continue
        candidates.append(x)

    if not candidates:
        return None, (), tuple(sorted(x.failure_id for x in items)), "NO_SUFFICIENT_FAILURE"

    children = defaultdict(set)
    indegree = {fid: 0 for fid in scoped}
    for x in scoped.values():
        for p in x.required_predecessors:
            if p in scoped:
                children[p].add(x.failure_id)
                indegree[x.failure_id] += 1

    depth = {fid: 0 for fid in scoped}
    queue = deque(sorted(fid for fid, n in indegree.items() if n == 0))
    while queue:
        fid = queue.popleft()
        for child in sorted(children[fid]):
            depth[child] = max(depth[child], depth[fid] + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    chosen = min(candidates, key=lambda x: (depth.get(x.failure_id, 10**6), x.observed_order, x.failure_id))
    contained = {chosen.failure_id}
    stack = list(chosen.required_predecessors)
    while stack:
        fid = stack.pop()
        if fid not in scoped or fid in contained:
            continue
        contained.add(fid)
        stack.extend(scoped[fid].required_predecessors)

    residual = tuple(sorted(x.failure_id for x in items if x.failure_id not in contained))
    return chosen.failure_id, tuple(sorted(contained)), residual, "CLAIM_BLOCKED"
