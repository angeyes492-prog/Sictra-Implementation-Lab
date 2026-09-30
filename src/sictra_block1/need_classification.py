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
