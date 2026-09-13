"""Deterministic, evidence-bounded execution planner for SICTrA closure work.

The planner deliberately does not infer that a human or architecture gate has
passed.  It ranks technical closure work and separately reports the next human
action, so a visible approval dependency cannot be hidden behind lower-risk
implementation work.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable


HUMAN_STATES = {"HUMAN_REVIEW_REQUIRED", "ARCHITECTURE_DECISION_REQUIRED"}
BLOCKED_STATES = {"BLOCKED_BY_DEPENDENCY", "DONE"}


@dataclass(frozen=True)
class ClosureItem:
    identifier: str
    title: str
    state: str
    risk: int
    dependency_impact: int
    evidence_gap: int
    irreversibility: int
    next_action: str
    evidence: str
    dependencies: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "ClosureItem":
        dimensions = ("risk", "dependency_impact", "evidence_gap", "irreversibility")
        for dimension in dimensions:
            number = value.get(dimension)
            if not isinstance(number, int) or not 1 <= number <= 5:
                raise ValueError(f"{value.get('identifier', '<unknown>')}: {dimension} must be an integer from 1 to 5")
        state = value.get("state")
        if not isinstance(state, str):
            raise ValueError("state is required")
        return cls(
            identifier=str(value["identifier"]), title=str(value["title"]), state=state,
            risk=value["risk"], dependency_impact=value["dependency_impact"],
            evidence_gap=value["evidence_gap"], irreversibility=value["irreversibility"],
            next_action=str(value["next_action"]), evidence=str(value["evidence"]),
            dependencies=tuple(str(item) for item in value.get("dependencies", [])),
        )

    @property
    def score(self) -> int:
        return self.risk * 4 + self.dependency_impact * 3 + self.evidence_gap * 3 + self.irreversibility * 2

    @property
    def lane(self) -> str:
        if self.state in HUMAN_STATES:
            return "HUMAN_GATE"
        if self.state in BLOCKED_STATES:
            return "BLOCKED"
        return "TECHNICAL"


def plan(items: Iterable[ClosureItem]) -> dict[str, list[ClosureItem]]:
    """Return deterministic, score-descending lanes without promoting any gate."""
    result = {"TECHNICAL": [], "HUMAN_GATE": [], "BLOCKED": []}
    for item in items:
        result[item.lane].append(item)
    for lane in result.values():
        lane.sort(key=lambda item: (-item.score, item.identifier))
    return result


def render_markdown(items: Iterable[ClosureItem]) -> str:
    lanes = plan(items)
    lines = [
        "# SICTrA closure execution queue v0.1",
        "",
        "This queue is deterministic: `risk×4 + dependency impact×3 + evidence gap×3 + irreversibility×2`. ",
        "It prioritizes work but never converts a human, independent-review, or architecture gate into a technical pass.",
        "",
    ]
    labels = {"TECHNICAL": "Technical execution", "HUMAN_GATE": "Human / architecture gates", "BLOCKED": "Blocked or completed"}
    for lane in ("TECHNICAL", "HUMAN_GATE", "BLOCKED"):
        lines.extend([f"## {labels[lane]}", "", "| Priority | Item | State | Evidence | Next action |", "| --- | --- | --- | --- | --- |"])
        if not lanes[lane]:
            lines.append("| — | — | — | — | — |")
        else:
            for item in lanes[lane]:
                lines.append(f"| {item.score} | `{item.identifier}` — {item.title} | `{item.state}` | {item.evidence} | {item.next_action} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = root / "closure" / "closure_queue_v0.1.json"
    output = root / "closure" / "closure_execution_queue_v0.1.md"
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("closure queue must be a JSON list")
    output.write_text(render_markdown(ClosureItem.from_mapping(item) for item in data) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
