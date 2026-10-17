"""Conservative, versioned routing labels for current Block 1 dossier needs."""

from .common import ContractViolation


class NeedClassificationViolation(ContractViolation):
    pass


_KNOWN_NEEDS = {
    "eurostat": {
        "Independent corroborating source for the same geography and period.": "INDEPENDENT_CORROBORATION",
        "Source metadata explaining revisions and coverage changes.": "SOURCE_METHODOLOGY",
        "Company-specific exposure data before estimating impact.": "COMPANY_EXPOSURE",
    },
    "HN_ADUANAS_BULLETINS": {
        "Detalle por producto, país de origen y régimen para los mismos periodos.": "SOURCE_GRANULARITY",
        "Una fuente independiente o espejo bilateral con identidad de raíz distinta.": "INDEPENDENT_CORROBORATION",
        "Nota metodológica que explique revisiones y la brecha de reconciliación.": "SOURCE_METHODOLOGY",
    },
}


def classify_data_need(source_id: str, requirement: str) -> str:
    """Unknown wording stays visible but gets no inferred autonomous route."""
    if (not isinstance(source_id, str) or not source_id
            or not isinstance(requirement, str) or not requirement.strip()
            or len(requirement) > 1000):
        raise NeedClassificationViolation("NEED_INPUT_INVALID")
    return _KNOWN_NEEDS.get(source_id, {}).get(requirement, "UNCLASSIFIED")


def route_data_need(source_id: str, requirement: str) -> dict:
    """Describe evidence type and next action without accepting or resolving it."""
    kind = classify_data_need(source_id, requirement)
    routes = {
        "INDEPENDENT_CORROBORATION": (
            "INDEPENDENT_DOSSIER", "MUST_DIFFER_FROM",
            ["REGISTER_APPROVED_LOCAL_SOURCE", "LINK_CURRENT_CANDIDATE_DOSSIER"],
            "REQUEST_COMPARABLE_APPROVED_SOURCE"),
        "SOURCE_METHODOLOGY": (
            "OFFICIAL_SOURCE_METHODOLOGY", "OFFICIAL_METADATA_FOR_SOURCE",
            ["RETAIN_QUARANTINED_OFFICIAL_METADATA", "REQUEST_BLOCK1_REASSESSMENT"],
            "REQUEST_SOURCE_SPECIFIC_METHODOLOGY"),
        "COMPANY_EXPOSURE": (
            "AUTHORIZED_ACCOUNT_CONTEXT", "AUTHORIZED_ACCOUNT_CONTEXT_REQUIRED",
            ["REGISTER_AUTHORIZED_ACCOUNT_CONTEXT", "REQUEST_BLOCK1_REASSESSMENT"],
            "REQUEST_AUTHORIZED_COMPANY_EXPOSURE"),
        "SOURCE_GRANULARITY": (
            "SOURCE_SCOPE_DETAIL", "APPROVED_DETAIL_FOR_SOURCE",
            ["REGISTER_APPROVED_SOURCE_DETAIL", "REQUEST_BLOCK1_REASSESSMENT"],
            "REQUEST_SAME_PERIOD_PRODUCT_ORIGIN_REGIME_DETAIL"),
    }
    route, root, actions, next_action = routes.get(kind, (
        "MANUAL_CLASSIFICATION", "MANUAL_EVIDENCE_ROUTE_REQUIRED",
        ["CLASSIFY_NEED_MANUALLY"], "CLASSIFY_NEED_MANUALLY"))
    return {"kind": kind, "id": route, "required_evidence_root": root,
            "allowed_actions": actions, "next_action": next_action}
