"""Three-layer logistics intelligence framing, deliberately without real accounts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .common import ContractViolation


LAYERS = frozenset(("GLOBAL", "SEGMENT", "ACCOUNT"))
CERTAINTIES = frozenset(("VERIFIED", "PROBABLE", "PLAUSIBLE", "UNCONFIRMED", "CONTRADICTED", "INSUFFICIENT EVIDENCE"))
CONFIDENCES = frozenset(("A", "B", "C", "D", "E"))

# Controlled topic vocabulary derived from the approved Block 1 thematic brief.
# A topic may appear in more than one domain when that overlap is intentional.
TOPIC_CATALOG: dict[str, frozenset[str]] = {
    "GEOPOLITICS_TRADE": frozenset("trade_tensions tariffs sanctions conflict_routes nearshoring friendshoring reshoring trade_fragmentation trade_blocs trade_agreements regulatory_change export_controls economic_security china_dependency supplier_diversification country_risk political_supply_chain".split()),
    "MARITIME": frozenset("ocean_freight_rates carrier_capacity blank_sailings port_congestion port_delays maritime_routes red_sea suez_canal panama_canal africa_diversions carrier_alliances carrier_concentration transshipment strategic_ports demurrage_detention empty_equipment container_availability container_types spot_vs_contract transit_time schedule_reliability vessel_capacity".split()),
    "AIR_FREIGHT": frozenset("air_freight_rates air_cargo_capacity belly_cargo integrators ecommerce_airfreight airport_capacity aviation_fuel emerging_air_routes airport_congestion critical_cargo air_security air_cargo_regulation air_hubs".split()),
    "CUSTOMS_TRADE_COMPLIANCE": frozenset("tariff_change tariff_classification customs_valuation rules_of_origin free_trade_agreements incoterms trade_compliance customs_audits special_regimes temporary_import export_controls electronic_documentation digital_customs inspections fine_risk de_minimis document_traceability".split()),
    "SUPPLY_CHAIN": frozenset("supply_chain_resilience inventory safety_stock lead_times supply_chain_visibility supplier_diversification dual_sourcing single_sourcing bullwhip_effect demand_forecasting sop risk_management business_continuity supply_chain_finance working_capital cost_to_serve total_landed_cost inventory_optimization".split()),
    "LOGISTICS_TECHNOLOGY": frozenset("logistics_ai machine_learning predictive_analytics digital_twins iot blockchain document_automation ocr edi apis visibility_platforms control_towers tms wms warehouse_automation robotics ai_agents ai_forecasting ai_procurement ai_documentation ai_compliance".split()),
    "COSTS_ECONOMY": frozenset("logistics_inflation fuel_price foreign_exchange interest_rates cost_of_capital inventory_cost freight_spend landed_cost port_costs airport_costs hidden_logistics_costs tco delay_cost stockout_cost excess_inventory_cost".split()),
    "SUSTAINABILITY": frozenset("imo maritime_decarbonization alternative_fuels saf emissions carbon_accounting scope_1_2_3 carbon_pricing green_corridors environmental_regulation supply_chain_esg reverse_logistics circular_economy".split()),
    "PORTS_INFRASTRUCTURE": frozenset("port_expansion terminals port_automation rail_infrastructure logistics_corridors intermodality inland_ports dry_ports warehousing regional_hubs border_infrastructure bottlenecks land_routes".split()),
    "RISK": frozenset("geopolitical_risk climate_risk supplier_risk cyber_risk port_disruption natural_disasters strike_risk political_risk trade_compliance_risk supplier_concentration route_dependency port_dependency".split()),
    "ECOMMERCE": frozenset("cross_border_ecommerce international_last_mile ecommerce_returns fulfillment micro_fulfillment international_d2c marketplace_logistics ecommerce_taxation de_minimis delivery_expectations reverse_logistics".split()),
    "INDUSTRIES": frozenset("automotive machinery electronics technology pharmaceuticals food beverages chemicals retail construction energy textiles manufacturing agriculture mining consumer_goods healthcare ecommerce".split()),
}
KNOWN_TOPICS = frozenset().union(*TOPIC_CATALOG.values())

_REQUIRED = frozenset(("frame_id", "layer", "topic_keys", "geographic_scope", "period", "industry", "account_id", "global_frame_ids", "segment_frame_ids", "evidence_ids", "certainty", "confidence"))


def _text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{name} must be non-empty text")
    return value.strip()


def _ids(name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, frozenset)):
        raise ContractViolation(f"{name} must be a collection of IDs")
    normalized = tuple(sorted({_text(name, item) for item in value}))
    if len(normalized) != len(value):
        raise ContractViolation(f"{name} must not contain duplicates")
    return normalized


def _industry(value: object) -> str:
    industry = _text("industry", value).lower()
    if industry not in TOPIC_CATALOG["INDUSTRIES"]:
        raise ContractViolation("industry must be a controlled industry topic")
    return industry


def normalize_research_frame(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one declared research frame; does not claim real-world truth."""

    if not isinstance(value, Mapping) or frozenset(value) != _REQUIRED:
        raise ContractViolation("research frame fields do not match contract")
    layer = value["layer"]
    if layer not in LAYERS:
        raise ContractViolation("research layer is invalid")
    topics = _ids("topic_keys", value["topic_keys"])
    if not topics or not set(topics).issubset(KNOWN_TOPICS):
        raise ContractViolation("research frame has an unknown topic")
    frame = {
        "frame_id": _text("frame_id", value["frame_id"]),
        "layer": layer,
        "topic_keys": topics,
        "geographic_scope": _text("geographic_scope", value["geographic_scope"]),
        "period": _text("period", value["period"]),
        "industry": value["industry"],
        "account_id": value["account_id"],
        "global_frame_ids": _ids("global_frame_ids", value["global_frame_ids"]),
        "segment_frame_ids": _ids("segment_frame_ids", value["segment_frame_ids"]),
        "evidence_ids": _ids("evidence_ids", value["evidence_ids"]),
        "certainty": value["certainty"],
        "confidence": value["confidence"],
    }
    if frame["certainty"] not in CERTAINTIES or frame["confidence"] not in CONFIDENCES:
        raise ContractViolation("research frame epistemic state is invalid")
    if layer == "GLOBAL":
        if frame["industry"] is not None or frame["account_id"] is not None or frame["global_frame_ids"] or frame["segment_frame_ids"]:
            raise ContractViolation("global frame cannot claim segment or account context")
    elif layer == "SEGMENT":
        if frame["account_id"] is not None or not frame["global_frame_ids"] or frame["segment_frame_ids"]:
            raise ContractViolation("segment frame requires industry and global context only")
        frame["industry"] = _industry(frame["industry"])
    else:
        if not isinstance(frame["account_id"], str) or not frame["account_id"].strip() or not frame["global_frame_ids"] or not frame["segment_frame_ids"]:
            raise ContractViolation("account frame requires industry, pseudonymous account, global and segment context")
        frame["industry"], frame["account_id"] = _industry(frame["industry"]), frame["account_id"].strip()
    if frame["frame_id"] in frame["global_frame_ids"] or frame["frame_id"] in frame["segment_frame_ids"]:
        raise ContractViolation("research frame cannot reference itself")
    return frame


def validate_research_frame_bundle(values: tuple[Mapping[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """Require Account frames to trace back to declared Global and Segment frames."""

    frames = tuple(normalize_research_frame(value) for value in values)
    by_id = {frame["frame_id"]: frame for frame in frames}
    if len(by_id) != len(frames):
        raise ContractViolation("research frame IDs must be unique")
    for frame in frames:
        global_parents = [by_id.get(item) for item in frame["global_frame_ids"]]
        segment_parents = [by_id.get(item) for item in frame["segment_frame_ids"]]
        if any(item is None or item["layer"] != "GLOBAL" for item in global_parents):
            raise ContractViolation("global context must reference declared GLOBAL frames")
        if any(item is None or item["layer"] != "SEGMENT" for item in segment_parents):
            raise ContractViolation("segment context must reference declared SEGMENT frames")
        if frame["layer"] == "ACCOUNT" and any(item["industry"] != frame["industry"] for item in segment_parents):
            raise ContractViolation("account industry must match every segment context")
    return deepcopy(frames)
