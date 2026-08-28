"""Bounded logistics-intelligence workspace models and synthetic field fixtures.

This module deliberately contains no network client, scraper, credential reader, or
production source adapter.  Its fixtures exercise the Block 1 research workflow
without presenting generated observations as real-world facts.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
from typing import Any, Mapping


WORKSPACE_SCOPE = "BLOCK1_LOGISTICS_INTELLIGENCE_WORKSPACE"
FIXTURE_CLASS = "SYNTHETIC_FIELD_TEST"

_PERCENT_METRICS = {
    "coverage_pct",
    "freshness_pct",
    "uncertainty_reduction_pct",
}
_MAXIMIZE_METRICS = (
    "coverage_pct",
    "independent_roots",
    "freshness_pct",
    "uncertainty_reduction_pct",
    "contradictions_resolved",
)
_MINIMIZE_METRICS = (
    "unresolved_contradictions",
    "elapsed_minutes",
    "source_cost_units",
)


class LogisticsContractViolation(ValueError):
    """Raised when a logistics object violates the bounded workspace contract."""


@dataclass(frozen=True, slots=True)
class StrategyObservation:
    strategy_id: str
    name: str
    question_id: str
    scope_key: str
    metrics: Mapping[str, float]
    red_team: str
    stability: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "StrategyObservation":
        required = {
            "strategy_id", "name", "question_id", "scope_key", "metrics",
            "red_team", "stability",
        }
        if set(value) != required:
            raise LogisticsContractViolation("strategy fields do not match contract")
        text_fields = ("strategy_id", "name", "question_id", "scope_key")
        if any(not isinstance(value[field], str) or not value[field].strip() for field in text_fields):
            raise LogisticsContractViolation("strategy identity fields must be non-empty text")
        metrics = value["metrics"]
        expected_metrics = set(_MAXIMIZE_METRICS + _MINIMIZE_METRICS)
        if not isinstance(metrics, Mapping) or set(metrics) != expected_metrics:
            raise LogisticsContractViolation("strategy metrics do not match contract")
        normalized: dict[str, float] = {}
        for key, raw in metrics.items():
            if (
                isinstance(raw, bool)
                or not isinstance(raw, (int, float))
                or not math.isfinite(raw)
                or raw < 0
            ):
                raise LogisticsContractViolation(f"metric {key} must be non-negative")
            number = float(raw)
            if key in _PERCENT_METRICS and number > 100:
                raise LogisticsContractViolation(f"metric {key} cannot exceed 100")
            normalized[key] = number
        if value["red_team"] not in {"PASS", "FAIL", "UNKNOWN"}:
            raise LogisticsContractViolation("unsupported red-team state")
        if value["stability"] not in {"STABLE", "AT_RISK", "DEGRADED", "UNKNOWN"}:
            raise LogisticsContractViolation("unsupported stability state")
        return cls(
            strategy_id=value["strategy_id"], name=value["name"],
            question_id=value["question_id"], scope_key=value["scope_key"],
            metrics=normalized, red_team=value["red_team"],
            stability=value["stability"],
        )


def _no_worse(left: StrategyObservation, right: StrategyObservation) -> bool:
    maximized = all(left.metrics[key] >= right.metrics[key] for key in _MAXIMIZE_METRICS)
    minimized = all(left.metrics[key] <= right.metrics[key] for key in _MINIMIZE_METRICS)
    return maximized and minimized


def _strictly_better(left: StrategyObservation, right: StrategyObservation) -> bool:
    maximized = any(left.metrics[key] > right.metrics[key] for key in _MAXIMIZE_METRICS)
    minimized = any(left.metrics[key] < right.metrics[key] for key in _MINIMIZE_METRICS)
    return maximized or minimized


def compare_strategies(
    left_value: Mapping[str, Any], right_value: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare compatible observed strategies without collapsing metrics to a score."""

    left = StrategyObservation.from_mapping(left_value)
    right = StrategyObservation.from_mapping(right_value)
    if left.strategy_id == right.strategy_id:
        raise LogisticsContractViolation("a strategy cannot be compared with itself")
    if left.question_id != right.question_id or left.scope_key != right.scope_key:
        return {
            "verdict": "SCOPE_MISMATCH",
            "preferred_strategy_id": None,
            "reason": "Las estrategias no comparten pregunta y alcance; no se comparan.",
            "metric_observations": [],
            "method": "PARETO_V0.1",
        }
    observations = []
    for key in _MAXIMIZE_METRICS + _MINIMIZE_METRICS:
        direction = "MAXIMIZE" if key in _MAXIMIZE_METRICS else "MINIMIZE"
        if left.metrics[key] == right.metrics[key]:
            advantage = "TIE"
        elif (direction == "MAXIMIZE" and left.metrics[key] > right.metrics[key]) or (
            direction == "MINIMIZE" and left.metrics[key] < right.metrics[key]
        ):
            advantage = left.strategy_id
        else:
            advantage = right.strategy_id
        observations.append({
            "metric": key, "direction": direction,
            "left": left.metrics[key], "right": right.metrics[key],
            "advantage": advantage,
        })
    if left.red_team != "PASS" or right.red_team != "PASS" or (
        left.stability != "STABLE" or right.stability != "STABLE"
    ):
        verdict, preferred = "INSUFFICIENT_EVIDENCE", None
        reason = "Ambas estrategias requieren red team PASS y estabilidad STABLE."
    elif _no_worse(left, right) and _strictly_better(left, right):
        verdict, preferred = "PREFER_LEFT", left.strategy_id
        reason = "La estrategia izquierda domina sin empeorar ninguna métrica observada."
    elif _no_worse(right, left) and _strictly_better(right, left):
        verdict, preferred = "PREFER_RIGHT", right.strategy_id
        reason = "La estrategia derecha domina sin empeorar ninguna métrica observada."
    else:
        verdict, preferred = "INCOMPARABLE", None
        reason = "Existen ventajas cruzadas; se preserva el trade-off sin fabricar un ranking."
    return {
        "verdict": verdict,
        "preferred_strategy_id": preferred,
        "reason": reason,
        "metric_observations": observations,
        "method": "PARETO_V0.1",
    }


def _strategy(
    strategy_id: str, name: str, question_id: str, scope_key: str,
    coverage: int, roots: int, freshness: int, uncertainty: int,
    resolved: int, unresolved: int, minutes: int, cost: int,
    *, red_team: str = "PASS", stability: str = "STABLE",
) -> dict[str, Any]:
    return {
        "strategy_id": strategy_id, "name": name, "question_id": question_id,
        "scope_key": scope_key,
        "metrics": {
            "coverage_pct": coverage, "independent_roots": roots,
            "freshness_pct": freshness, "uncertainty_reduction_pct": uncertainty,
            "contradictions_resolved": resolved,
            "unresolved_contradictions": unresolved,
            "elapsed_minutes": minutes, "source_cost_units": cost,
        },
        "red_team": red_team, "stability": stability,
    }


_INVESTIGATIONS: tuple[dict[str, Any], ...] = (
    {
        "investigation_id": "global-components-001",
        "title": "Resiliencia de abastecimiento de componentes",
        "question": "¿Qué señales deberían vigilarse para anticipar presión sobre una ruta Asia–Américas?",
        "question_id": "Q-GLOBAL-001",
        "status": "DELIVERABLE_BOUNDED",
        "certainty": "PLAUSIBLE", "confidence": "C",
        "scope": {"level": "GLOBAL", "geography": "Asia–Américas", "industry": "Electrónica", "actor": "Importador / fabricante", "mode": "Marítimo + aéreo", "period": "90 días", "scope_key": "GLOBAL|ASIA-AMERICAS|ELECTRONICS|90D"},
        "signal": "La concentración de nodos y la sustitución modal merecen vigilancia conjunta.",
        "limitations": ["Datos sintéticos", "No predice disrupciones", "No identifica proveedores reales"],
        "sources": [
            {"source_id": "SRC-G-01", "name": "Boletín portuario simulado", "tier": "PRIMARY_SIMULATED", "root": "ROOT-PORT", "freshness": "CURRENT", "supports": ["CLM-G-01"]},
            {"source_id": "SRC-G-02", "name": "Serie de tránsito simulada", "tier": "PRIMARY_SIMULATED", "root": "ROOT-TRANSIT", "freshness": "CURRENT", "supports": ["CLM-G-01", "CLM-G-02"]},
            {"source_id": "SRC-G-03", "name": "Nota sectorial simulada", "tier": "SECONDARY_SIMULATED", "root": "ROOT-SECTOR", "freshness": "CURRENT", "supports": ["CLM-G-02"]},
            {"source_id": "SRC-G-04", "name": "Copia correlacionada de tránsito", "tier": "SECONDARY_SIMULATED", "root": "ROOT-TRANSIT", "freshness": "CURRENT", "supports": ["CLM-G-01"]},
        ],
        "claims": [
            {"claim_id": "CLM-G-01", "type": "HYPOTHESIS", "state": "PLAUSIBLE", "confidence": "C", "text": "Una variación simultánea de tránsito y disponibilidad modal puede justificar revalidación temprana.", "source_ids": ["SRC-G-01", "SRC-G-02", "SRC-G-04"], "independent_roots": 2, "contradiction": None},
            {"claim_id": "CLM-G-02", "type": "INTERPRETATION", "state": "PROBABLE", "confidence": "B", "text": "La diversificación modal reduce dependencia de una sola señal, no necesariamente el riesgo total.", "source_ids": ["SRC-G-02", "SRC-G-03"], "independent_roots": 2, "contradiction": "El costo puede anular la viabilidad de sustitución."},
        ],
        "strategies": [
            _strategy("STR-G-A", "Triangulación por nodo", "Q-GLOBAL-001", "GLOBAL|ASIA-AMERICAS|ELECTRONICS|90D", 82, 3, 90, 37, 2, 0, 42, 3),
            _strategy("STR-G-B", "Barrido sectorial", "Q-GLOBAL-001", "GLOBAL|ASIA-AMERICAS|ELECTRONICS|90D", 74, 3, 80, 29, 1, 0, 58, 5),
            _strategy("STR-G-C", "Profundidad de corredor", "Q-GLOBAL-001", "GLOBAL|ASIA-AMERICAS|ELECTRONICS|90D", 88, 2, 72, 42, 1, 0, 64, 2),
        ],
        "watchlist": [
            {"horizon": "7D", "observable": "Cambio coincidente en dos raíces independientes", "trigger": "2 señales"},
            {"horizon": "30D", "observable": "Persistencia de presión modal", "trigger": "3 cortes"},
            {"horizon": "90D", "observable": "Cambio estructural de corredor", "trigger": "Revalidación completa"},
        ],
    },
    {
        "investigation_id": "regional-ca-electronics-002",
        "title": "Continuidad regional de importación electrónica",
        "question": "¿Qué combinación de señales regionales reduce mejor la incertidumbre de reposición?",
        "question_id": "Q-REGIONAL-002",
        "status": "RESEARCH_NEEDED", "certainty": "UNCONFIRMED", "confidence": "D",
        "scope": {"level": "REGIONAL", "geography": "Centroamérica", "industry": "Electrónica de consumo", "actor": "Importadores", "mode": "Marítimo + terrestre", "period": "30 días", "scope_key": "REGIONAL|CENTRAL-AMERICA|CONSUMER-ELECTRONICS|30D"},
        "signal": "La evidencia regional aún no separa retraso portuario de fricción terrestre.",
        "limitations": ["Datos sintéticos", "Contradicción abierta", "Cobertura aduanera incompleta"],
        "sources": [
            {"source_id": "SRC-R-01", "name": "Registro aduanero simulado", "tier": "PRIMARY_SIMULATED", "root": "ROOT-CUSTOMS", "freshness": "CURRENT", "supports": ["CLM-R-01"]},
            {"source_id": "SRC-R-02", "name": "Reporte terrestre simulado", "tier": "PRIMARY_SIMULATED", "root": "ROOT-LAND", "freshness": "STALE", "supports": ["CLM-R-01"]},
        ],
        "claims": [
            {"claim_id": "CLM-R-01", "type": "HYPOTHESIS", "state": "CONTRADICTED", "confidence": "D", "text": "La variación observada parece originarse en el tramo terrestre.", "source_ids": ["SRC-R-01", "SRC-R-02"], "independent_roots": 2, "contradiction": "La fuente terrestre está vencida y no confirma causalidad."},
        ],
        "strategies": [
            _strategy("STR-R-A", "Aduana primero", "Q-REGIONAL-002", "REGIONAL|CENTRAL-AMERICA|CONSUMER-ELECTRONICS|30D", 61, 2, 55, 18, 0, 1, 35, 2, red_team="FAIL", stability="AT_RISK"),
            _strategy("STR-R-B", "Ruta terrestre primero", "Q-REGIONAL-002", "REGIONAL|CENTRAL-AMERICA|CONSUMER-ELECTRONICS|30D", 66, 2, 42, 22, 0, 1, 29, 2, red_team="UNKNOWN", stability="AT_RISK"),
        ],
        "watchlist": [
            {"horizon": "7D", "observable": "Nueva raíz terrestre vigente", "trigger": "1 fuente admisible"},
            {"horizon": "30D", "observable": "Separación puerto / frontera", "trigger": "Serie comparable"},
            {"horizon": "90D", "observable": "Patrón regional repetido", "trigger": "3 ciclos"},
        ],
    },
    {
        "investigation_id": "local-dc-003",
        "title": "Señales locales para continuidad de distribución",
        "question": "¿Qué observables locales justificarían investigar un riesgo de disponibilidad?",
        "question_id": "Q-LOCAL-003",
        "status": "DRAFT", "certainty": "INSUFFICIENT EVIDENCE", "confidence": "E",
        "scope": {"level": "LOCAL", "geography": "Área metropolitana de prueba", "industry": "Distribución electrónica", "actor": "Centro de distribución", "mode": "Terrestre", "period": "7 días", "scope_key": "LOCAL|TEST-METRO|ELECTRONICS-DISTRIBUTION|7D"},
        "signal": "La pregunta está acotada, pero todavía no posee dos raíces independientes.",
        "limitations": ["Datos sintéticos", "Una sola raíz", "Insight no entregable"],
        "sources": [
            {"source_id": "SRC-L-01", "name": "Bitácora operativa simulada", "tier": "PRIMARY_SIMULATED", "root": "ROOT-OPS", "freshness": "CURRENT", "supports": ["CLM-L-01"]},
        ],
        "claims": [
            {"claim_id": "CLM-L-01", "type": "HYPOTHESIS", "state": "INSUFFICIENT EVIDENCE", "confidence": "E", "text": "Un cambio local de reposición podría requerir investigación adicional.", "source_ids": ["SRC-L-01"], "independent_roots": 1, "contradiction": None},
        ],
        "strategies": [
            _strategy("STR-L-A", "Bitácora operativa", "Q-LOCAL-003", "LOCAL|TEST-METRO|ELECTRONICS-DISTRIBUTION|7D", 38, 1, 92, 8, 0, 0, 12, 1, red_team="UNKNOWN", stability="UNKNOWN"),
            _strategy("STR-L-B", "Validación de inventario", "Q-LOCAL-003", "LOCAL|TEST-METRO|ELECTRONICS-DISTRIBUTION|7D", 0, 0, 0, 0, 0, 0, 0, 0, red_team="UNKNOWN", stability="UNKNOWN"),
        ],
        "watchlist": [
            {"horizon": "7D", "observable": "Segunda raíz independiente", "trigger": "Obligatorio"},
            {"horizon": "30D", "observable": "Tendencia persistente", "trigger": "No evaluable"},
            {"horizon": "90D", "observable": "Cambio estructural", "trigger": "No evaluable"},
        ],
    },
)


def validate_investigation(investigation: Mapping[str, Any]) -> None:
    """Validate a complete fixture and its bidirectional lineage."""

    if investigation["status"] not in {
        "DRAFT", "RESEARCH_NEEDED", "DELIVERABLE_BOUNDED", "QUARANTINED", "SUPERSEDED"
    }:
        raise LogisticsContractViolation("unsupported investigation state")
    source_ids = {source["source_id"] for source in investigation["sources"]}
    if len(source_ids) != len(investigation["sources"]):
        raise LogisticsContractViolation("duplicate source identity")
    sources = {source["source_id"]: source for source in investigation["sources"]}
    claim_ids = {claim["claim_id"] for claim in investigation["claims"]}
    if len(claim_ids) != len(investigation["claims"]):
        raise LogisticsContractViolation("duplicate claim identity")
    for source in investigation["sources"]:
        if not isinstance(source.get("supports"), list) or not set(source["supports"]).issubset(claim_ids):
            raise LogisticsContractViolation("source references an unknown claim")
    for claim in investigation["claims"]:
        if not set(claim["source_ids"]).issubset(source_ids):
            raise LogisticsContractViolation("claim references an unknown source")
        roots = {sources[source_id]["root"] for source_id in claim["source_ids"]}
        if claim["independent_roots"] != len(roots):
            raise LogisticsContractViolation("claim independent-root count does not match lineage")
        for source_id in claim["source_ids"]:
            if claim["claim_id"] not in sources[source_id]["supports"]:
                raise LogisticsContractViolation("claim-source lineage is not bidirectional")
    for source in investigation["sources"]:
        for claim_id in source["supports"]:
            claim = next(item for item in investigation["claims"] if item["claim_id"] == claim_id)
            if source["source_id"] not in claim["source_ids"]:
                raise LogisticsContractViolation("source-claim lineage is not bidirectional")
    available_roots = len({source["root"] for source in investigation["sources"]})
    strategy_ids = set()
    for strategy in investigation["strategies"]:
        observation = StrategyObservation.from_mapping(strategy)
        if observation.strategy_id in strategy_ids:
            raise LogisticsContractViolation("duplicate strategy identity")
        strategy_ids.add(observation.strategy_id)
        if observation.question_id != investigation["question_id"]:
            raise LogisticsContractViolation("strategy question does not match investigation")
        if observation.scope_key != investigation["scope"]["scope_key"]:
            raise LogisticsContractViolation("strategy scope does not match investigation")
        if observation.metrics["independent_roots"] > available_roots:
            raise LogisticsContractViolation("strategy claims more roots than its investigation")


for _fixture in _INVESTIGATIONS:
    validate_investigation(_fixture)


def workspace_catalog() -> dict[str, Any]:
    """Return a defensive JSON-ready workspace snapshot."""

    investigations = deepcopy(_INVESTIGATIONS)
    for investigation in investigations:
        investigation["evidence_summary"] = {
            "sources": len(investigation["sources"]),
            "independent_roots": len({source["root"] for source in investigation["sources"]}),
            "claims": len(investigation["claims"]),
            "contradictions": sum(bool(claim["contradiction"]) for claim in investigation["claims"]),
        }
    return {
        "scope": WORKSPACE_SCOPE,
        "fixture_class": FIXTURE_CLASS,
        "identity": {"product": "Telecare OS", "block": "01", "name": "Intelligence"},
        "non_claims": [
            "No consulta internet ni fuentes externas.",
            "No contiene perfiles de empresas ni datos personales reales.",
            "No promueve el gate global ni demuestra producción.",
        ],
        "investigations": investigations,
    }


def get_investigation(investigation_id: str) -> dict[str, Any] | None:
    if not isinstance(investigation_id, str):
        return None
    catalog = workspace_catalog()
    return next(
        (item for item in catalog["investigations"] if item["investigation_id"] == investigation_id),
        None,
    )


def compare_investigation_strategies(
    investigation_id: str, left_id: str, right_id: str
) -> dict[str, Any]:
    investigation = get_investigation(investigation_id)
    if investigation is None:
        raise LogisticsContractViolation("unknown investigation")
    strategies = {item["strategy_id"]: item for item in investigation["strategies"]}
    if left_id not in strategies or right_id not in strategies:
        raise LogisticsContractViolation("unknown strategy")
    result = compare_strategies(strategies[left_id], strategies[right_id])
    return {
        "investigation_id": investigation_id,
        "left": deepcopy(strategies[left_id]),
        "right": deepcopy(strategies[right_id]),
        "comparison": result,
        "fixture_class": FIXTURE_CLASS,
    }
