"""Durable local intake for operator-declared research questions.

The intake deliberately stores research *requests*, not source evidence.  It
has no network client and never turns a declared reference into a source,
claim, insight, or admissible root.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any, Callable, Mapping
from uuid import uuid4

from .common import ContractViolation
from .intelligence_layers import KNOWN_TOPICS, TOPIC_CATALOG


RESEARCH_INTAKE_SCOPE = "BLOCK1_LOCAL_OPERATOR_RESEARCH_INTAKE"
RESEARCH_INTAKE_VERSION = 1
MAX_RESEARCH_DRAFTS = 100
_INPUT_FIELDS = frozenset((
    "title", "question", "level", "geography", "industry", "actor",
    "mode", "period", "topic_keys", "source_reference",
))
_LEVELS = frozenset(("GLOBAL", "REGIONAL", "LOCAL"))


class ResearchIntakeViolation(ContractViolation):
    """Raised when an operator research request is malformed or unsafe."""


def _text(name: str, value: object, *, minimum: int, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ResearchIntakeViolation(f"{name} must be text")
    normalized = value.strip()
    if not normalized and allow_empty:
        return ""
    if not minimum <= len(normalized) <= maximum:
        raise ResearchIntakeViolation(f"{name} must contain {minimum} to {maximum} characters")
    if any(ord(character) < 32 and character not in "\n\t" for character in normalized):
        raise ResearchIntakeViolation(f"{name} contains a control character")
    return normalized


def _topic_keys(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= 5:
        raise ResearchIntakeViolation("topic_keys requires one to five controlled topics")
    topics = tuple(_text("topic_key", item, minimum=2, maximum=80).lower() for item in value)
    if len(set(topics)) != len(topics) or not set(topics).issubset(KNOWN_TOPICS):
        raise ResearchIntakeViolation("topic_keys contains an unknown or duplicate topic")
    return tuple(sorted(topics))


def _created_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_research_intake(
    payload: Mapping[str, Any], *, draft_id: str, created_at: str,
) -> dict[str, Any]:
    """Create an explicitly evidence-free research draft from operator input."""

    if not isinstance(payload, Mapping) or frozenset(payload) != _INPUT_FIELDS:
        raise ResearchIntakeViolation("research intake fields do not match contract")
    level = payload["level"]
    if level not in _LEVELS:
        raise ResearchIntakeViolation("level must be GLOBAL, REGIONAL, or LOCAL")
    industry = _text("industry", payload["industry"], minimum=2, maximum=80).lower()
    if industry not in TOPIC_CATALOG["INDUSTRIES"]:
        raise ResearchIntakeViolation("industry must be a controlled industry topic")
    title = _text("title", payload["title"], minimum=3, maximum=160)
    question = _text("question", payload["question"], minimum=12, maximum=600)
    geography = _text("geography", payload["geography"], minimum=2, maximum=120)
    actor = _text("actor", payload["actor"], minimum=2, maximum=100)
    mode = _text("mode", payload["mode"], minimum=2, maximum=100)
    period = _text("period", payload["period"], minimum=2, maximum=60)
    source_reference = _text(
        "source_reference", payload["source_reference"], minimum=5, maximum=500,
        allow_empty=True,
    )
    topics = _topic_keys(payload["topic_keys"])
    normalized_id = _text("draft_id", draft_id, minimum=8, maximum=100)
    normalized_created_at = _text("created_at", created_at, minimum=20, maximum=40)
    declaration = None if not source_reference else {
        "kind": "USER_DECLARED_UNBOUND_REFERENCE",
        "reference": source_reference,
        "status": "NOT_FETCHED_NOT_EVIDENCE",
    }
    return {
        "investigation_id": normalized_id,
        "record_type": "OPERATOR_RESEARCH_DRAFT",
        "created_at": normalized_created_at,
        "title": title,
        "question": question,
        "question_id": f"INTAKE-{normalized_id.upper()}",
        "status": "DRAFT",
        "certainty": "INSUFFICIENT EVIDENCE",
        "confidence": "E",
        "scope": {
            "level": level,
            "geography": geography,
            "industry": industry,
            "actor": actor,
            "mode": mode,
            "period": period,
            "scope_key": f"{level}|{geography}|{industry}|{period}",
        },
        "topic_keys": list(topics),
        "signal": "Sin insight generado: la pregunta requiere evidencia admitida y validación.",
        "limitations": [
            "Entrada declarada por operador; no es evidencia.",
            "Sin fuente BOUND ni claim verificable.",
            "No se consultó internet ni se ejecutó una recolección.",
        ],
        "sources": [],
        "claims": [],
        "strategies": [],
        "watchlist": [
            {"horizon": "7D", "observable": "Definir primer source bundle", "trigger": "Revisión de fuente"},
            {"horizon": "30D", "observable": "Resolver primera contradicción", "trigger": "Dos raíces independientes"},
            {"horizon": "90D", "observable": "Reevaluar alcance y estrategia", "trigger": "Evidencia admisible"},
        ],
        "operator_declaration": declaration,
    }


class ResearchIntakeStore:
    """Bounded JSON store with atomic replacement for local operator drafts."""

    def __init__(
        self, path: str | Path, *, clock: Callable[[], str] = _created_at,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.path = Path(path)
        if not self.path.name:
            raise ResearchIntakeViolation("research intake path is invalid")
        self._clock = clock
        self._id_factory = id_factory or (lambda: f"draft-{uuid4().hex}")
        self._lock = Lock()

    def _load_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ResearchIntakeViolation("research intake store cannot be read") from error
        if not isinstance(raw, dict) or set(raw) != {"version", "records"} or raw["version"] != RESEARCH_INTAKE_VERSION or not isinstance(raw["records"], list) or len(raw["records"]) > MAX_RESEARCH_DRAFTS:
            raise ResearchIntakeViolation("research intake store has an unsupported schema")
        records: list[dict[str, Any]] = []
        for record in raw["records"]:
            if not isinstance(record, Mapping):
                raise ResearchIntakeViolation("research intake store contains an invalid record")
            expected = normalize_research_intake({
                "title": record.get("title"), "question": record.get("question"),
                "level": record.get("scope", {}).get("level") if isinstance(record.get("scope"), Mapping) else None,
                "geography": record.get("scope", {}).get("geography") if isinstance(record.get("scope"), Mapping) else None,
                "industry": record.get("scope", {}).get("industry") if isinstance(record.get("scope"), Mapping) else None,
                "actor": record.get("scope", {}).get("actor") if isinstance(record.get("scope"), Mapping) else None,
                "mode": record.get("scope", {}).get("mode") if isinstance(record.get("scope"), Mapping) else None,
                "period": record.get("scope", {}).get("period") if isinstance(record.get("scope"), Mapping) else None,
                "topic_keys": record.get("topic_keys"),
                "source_reference": (record.get("operator_declaration") or {}).get("reference", "") if isinstance(record.get("operator_declaration"), Mapping) or record.get("operator_declaration") is None else None,
            }, draft_id=record.get("investigation_id"), created_at=record.get("created_at"))
            if set(record) != set(expected) or record != expected:
                raise ResearchIntakeViolation("research intake store record failed integrity validation")
            records.append(expected)
        if len({record["investigation_id"] for record in records}) != len(records):
            raise ResearchIntakeViolation("research intake store contains duplicate identities")
        return records

    def _save_unlocked(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, delete=False,
            ) as temporary:
                temporary_name = temporary.name
                json.dump({"version": RESEARCH_INTAKE_VERSION, "records": records}, temporary, ensure_ascii=False, separators=(",", ":"))
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, self.path)
        except OSError as error:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise ResearchIntakeViolation("research intake store cannot be written") from error

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self._load_unlocked())

    def create(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            records = self._load_unlocked()
            identities = {record["investigation_id"] for record in records}
            for _ in range(4):
                draft_id = self._id_factory()
                if draft_id not in identities:
                    break
            else:
                raise ResearchIntakeViolation("research intake identity collision")
            draft = normalize_research_intake(payload, draft_id=draft_id, created_at=self._clock())
            records.append(draft)
            self._save_unlocked(records)
            return deepcopy(draft)
