"""Append-only SQLite Project Graph for the traceable Block 2 slice."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

from .canonical_document import DesignDocumentVersion, canonical_json, document_from_mapping


RELATIONS = frozenset({
    "DERIVED_FROM", "SUPPORTS", "CONTRADICTS", "REPRESENTS", "GENERATED_BY",
    "TRANSFORMED_FROM", "USED_IN", "VALIDATED_BY", "SUPERSEDES", "EXPORTED_AS",
})
_HASH = re.compile(r"^[0-9a-f]{64}$")


class ProjectGraphViolation(ValueError):
    """Graph mutation was malformed or contradicted append-only identity."""


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProjectGraphViolation(f"{name} must be a non-empty string")


def _timestamp(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ProjectGraphViolation("created_at must be timezone-aware")
    return value.isoformat()


def _payload(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class GraphNode:
    project_id: str
    node_id: str
    node_type: str
    content_hash: str
    payload: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class GraphEdge:
    project_id: str
    source_id: str
    relation: str
    target_id: str
    evidence_ref: str
    created_at: datetime

    @property
    def edge_id(self) -> str:
        material = "\x1f".join((self.project_id, self.source_id, self.relation, self.target_id, self.evidence_ref))
        return "EDGE-" + sha256(material.encode("utf-8")).hexdigest()


class ProjectGraphStore:
    """Durable local graph with WAL, idempotency, and collision rejection."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, timeout=5.0)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._create_schema()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "ProjectGraphStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS graph_nodes (
                project_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                node_type TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (project_id, node_id)
            );
            CREATE TABLE IF NOT EXISTS graph_edges (
                project_id TEXT NOT NULL,
                edge_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                target_id TEXT NOT NULL,
                evidence_ref TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (project_id, edge_id),
                FOREIGN KEY (project_id, source_id) REFERENCES graph_nodes(project_id, node_id),
                FOREIGN KEY (project_id, target_id) REFERENCES graph_nodes(project_id, node_id)
            );
            CREATE TABLE IF NOT EXISTS design_document_versions (
                project_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                version_id TEXT NOT NULL,
                parent_version_id TEXT,
                content_hash TEXT NOT NULL,
                canonical_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (project_id, version_id)
            );
            """
        )
        self._connection.commit()

    def append_node(self, node: GraphNode) -> str:
        for name, value in (("project_id", node.project_id), ("node_id", node.node_id), ("node_type", node.node_type), ("content_hash", node.content_hash)):
            _text(value, name)
        if not _HASH.fullmatch(node.content_hash):
            raise ProjectGraphViolation("node content_hash must be a lowercase SHA-256 identity")
        payload_json = _payload(node.payload)
        existing = self._connection.execute(
            "SELECT node_type, content_hash, payload_json FROM graph_nodes WHERE project_id=? AND node_id=?",
            (node.project_id, node.node_id),
        ).fetchone()
        identity = (node.node_type, node.content_hash, payload_json)
        if existing is not None:
            if tuple(existing) == identity:
                return "IDEMPOTENT"
            raise ProjectGraphViolation("node identity collision")
        self._connection.execute(
            "INSERT INTO graph_nodes VALUES (?, ?, ?, ?, ?, ?)",
            (node.project_id, node.node_id, node.node_type, node.content_hash, payload_json, _timestamp(node.created_at)),
        )
        return "APPENDED"

    def append_edge(self, edge: GraphEdge) -> str:
        for name, value in (("project_id", edge.project_id), ("source_id", edge.source_id), ("target_id", edge.target_id), ("evidence_ref", edge.evidence_ref)):
            _text(value, name)
        if edge.relation not in RELATIONS:
            raise ProjectGraphViolation("edge relation is not contracted")
        existing = self._connection.execute(
            "SELECT source_id, relation, target_id, evidence_ref FROM graph_edges WHERE project_id=? AND edge_id=?",
            (edge.project_id, edge.edge_id),
        ).fetchone()
        identity = (edge.source_id, edge.relation, edge.target_id, edge.evidence_ref)
        if existing is not None:
            if tuple(existing) == identity:
                return "IDEMPOTENT"
            raise ProjectGraphViolation("edge identity collision")
        try:
            self._connection.execute(
                "INSERT INTO graph_edges VALUES (?, ?, ?, ?, ?, ?, ?)",
                (edge.project_id, edge.edge_id, edge.source_id, edge.relation, edge.target_id, edge.evidence_ref, _timestamp(edge.created_at)),
            )
        except sqlite3.IntegrityError as error:
            raise ProjectGraphViolation("edges must bind existing nodes in the same project") from error
        return "APPENDED"

    def append_document(self, document: DesignDocumentVersion) -> str:
        material = canonical_json(document)
        existing = self._connection.execute(
            "SELECT document_id, parent_version_id, content_hash, canonical_json FROM design_document_versions WHERE project_id=? AND version_id=?",
            (document.project_id, document.version_id),
        ).fetchone()
        identity = (document.document_id, document.parent_version_id, document.content_hash, material)
        if existing is not None:
            if tuple(existing) == identity:
                return "IDEMPOTENT"
            raise ProjectGraphViolation("document version identity collision")
        if document.parent_version_id is not None:
            parent = self._connection.execute(
                "SELECT document_id FROM design_document_versions WHERE project_id=? AND version_id=?",
                (document.project_id, document.parent_version_id),
            ).fetchone()
            if parent is None or parent["document_id"] != document.document_id:
                raise ProjectGraphViolation("document parent is missing or belongs to another document")
        self._connection.execute(
            "INSERT INTO design_document_versions VALUES (?, ?, ?, ?, ?, ?, ?)",
            (document.project_id, document.document_id, document.version_id, document.parent_version_id, document.content_hash, material, _timestamp(document.created_at)),
        )
        return "APPENDED"

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def node_ids(self, project_id: str) -> tuple[str, ...]:
        rows = self._connection.execute(
            "SELECT node_id FROM graph_nodes WHERE project_id=? ORDER BY created_at, node_id", (project_id,),
        ).fetchall()
        return tuple(row["node_id"] for row in rows)

    def edges(self, project_id: str) -> tuple[tuple[str, str, str], ...]:
        rows = self._connection.execute(
            "SELECT source_id, relation, target_id FROM graph_edges WHERE project_id=? ORDER BY created_at, edge_id", (project_id,),
        ).fetchall()
        return tuple((row["source_id"], row["relation"], row["target_id"]) for row in rows)

    def document_hash(self, project_id: str, version_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT content_hash FROM design_document_versions WHERE project_id=? AND version_id=?", (project_id, version_id),
        ).fetchone()
        return None if row is None else row["content_hash"]

    def load_document(self, project_id: str, version_id: str) -> DesignDocumentVersion | None:
        row = self._connection.execute(
            "SELECT canonical_json FROM design_document_versions WHERE project_id=? AND version_id=?",
            (project_id, version_id),
        ).fetchone()
        return None if row is None else document_from_mapping(json.loads(row["canonical_json"]))

    def latest_document_version_id(self, project_id: str, document_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT version_id FROM design_document_versions WHERE project_id=? AND document_id=? "
            "ORDER BY created_at DESC, version_id DESC LIMIT 1",
            (project_id, document_id),
        ).fetchone()
        return None if row is None else row["version_id"]

    def project_ids(self) -> tuple[str, ...]:
        rows = self._connection.execute(
            "SELECT DISTINCT project_id FROM graph_nodes ORDER BY project_id"
        ).fetchall()
        return tuple(row["project_id"] for row in rows)

    def snapshot(self, project_id: str) -> dict[str, Any] | None:
        """Return a JSON-ready read model; it carries no mutation authority."""

        _text(project_id, "project_id")
        node_rows = self._connection.execute(
            "SELECT node_id, node_type, content_hash, payload_json, created_at "
            "FROM graph_nodes WHERE project_id=? ORDER BY created_at, node_id",
            (project_id,),
        ).fetchall()
        if not node_rows:
            return None
        edge_rows = self._connection.execute(
            "SELECT edge_id, source_id, relation, target_id, evidence_ref, created_at "
            "FROM graph_edges WHERE project_id=? ORDER BY created_at, edge_id",
            (project_id,),
        ).fetchall()
        document_rows = self._connection.execute(
            "SELECT document_id, version_id, parent_version_id, content_hash, canonical_json, created_at "
            "FROM design_document_versions WHERE project_id=? ORDER BY created_at, version_id",
            (project_id,),
        ).fetchall()
        return {
            "project_id": project_id,
            "nodes": [
                {
                    "node_id": row["node_id"], "node_type": row["node_type"],
                    "content_hash": row["content_hash"], "payload": json.loads(row["payload_json"]),
                    "created_at": row["created_at"],
                }
                for row in node_rows
            ],
            "edges": [dict(row) for row in edge_rows],
            "documents": [
                {
                    "document_id": row["document_id"], "version_id": row["version_id"],
                    "parent_version_id": row["parent_version_id"], "content_hash": row["content_hash"],
                    "document": json.loads(row["canonical_json"]), "created_at": row["created_at"],
                }
                for row in document_rows
            ],
            "authority": {
                "publication": "NOT_PUBLISHED", "acceptance": "NOT_ACCEPTED",
                "read_model": "NO_MUTATION_AUTHORITY",
            },
        }
