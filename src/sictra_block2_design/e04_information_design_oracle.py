"""Independent declarative oracle for the bounded E04 validator."""

from __future__ import annotations

from .e04_information_design import InformationBlueprintAssessment


def expected_information_blueprint(envelope, profile, profile_state, payload, target, blueprint):
    if not payload.contract_version.startswith("0.1.") or not blueprint.contract_version.startswith("0.1."):
        return InformationBlueprintAssessment("UNSUPPORTED_VERSION", ("CONTRACT_VERSION_UNSUPPORTED",))

    reasons = []
    if profile_state != "SYSTEM_PROFILE_READY_FOR_BLUEPRINT": reasons.append("PROFILE_NOT_READY")
    if profile.profile_id != blueprint.profile_id: reasons.append("PROFILE_ID_MISMATCH")
    if envelope != profile.envelope_fingerprint or envelope != blueprint.envelope_fingerprint: reasons.append("ENVELOPE_FINGERPRINT_MISMATCH")
    if (target.channel, target.artifact_type, target.audience_path) != (blueprint.channel, blueprint.artifact_type, blueprint.audience_path): reasons.append("CHANNEL_TARGET_MUTATED")
    if reasons: return InformationBlueprintAssessment("RETURN_TO_PREVIOUS", tuple(reasons))
    if target.channel not in profile.supported_channels:
        return InformationBlueprintAssessment("UNSUPPORTED_CHANNEL", ("CHANNEL_NOT_SUPPORTED_BY_PROFILE",))

    reasons = []
    if not payload.claims: reasons.append("CLAIMS_MISSING")
    if not payload.approved_copy: reasons.append("APPROVED_COPY_MISSING")
    if len({claim.claim_id for claim in payload.claims}) != len(payload.claims): reasons.append("DUPLICATE_CLAIM_ID")
    for claim in payload.claims:
        if not claim.evidence_refs: reasons.append(f"CLAIM_{claim.claim_id}_EVIDENCE_MISSING")
        if not claim.attribution_ids: reasons.append(f"CLAIM_{claim.claim_id}_ATTRIBUTION_MISSING")
    if reasons: return InformationBlueprintAssessment("RETURN_UPSTREAM", tuple(reasons))

    reasons = []
    if blueprint.executable_artifacts: reasons.append("EXECUTABLE_ARTIFACT_PRESENT")
    if blueprint.publication_state != "NOT_PUBLISHED": reasons.append("PUBLICATION_STATE_OUT_OF_SCOPE")
    if reasons: return InformationBlueprintAssessment("SCOPE_VIOLATION", tuple(reasons))

    required = {
        "NEWSLETTER": {"PLAIN_TEXT"}, "MULTIMEDIA": {"TRANSCRIPT", "MATERIAL_DESCRIPTION"},
        "VIDEO": {"TRANSCRIPT", "MATERIAL_DESCRIPTION"}, "GRAPHIC": {"ALT_TEXT", "LEGEND"},
        "INFOGRAPHIC": {"ALT_TEXT", "LEGEND"},
    }.get(target.artifact_type)
    if required is None: return InformationBlueprintAssessment("UNSUPPORTED_CHANNEL", ("ARTIFACT_TYPE_NOT_CONTRACTED",))
    missing = required - set(blueprint.accessibility_fallbacks)
    if missing: return InformationBlueprintAssessment("UNSUPPORTED_CHANNEL", tuple(f"FALLBACK_{x}_MISSING" for x in sorted(missing)))

    claims = {x.claim_id: x for x in payload.claims}
    mapped = set()
    reasons = []
    ids = {x.element_id for x in blueprint.elements}
    if len(ids) != len(blueprint.elements): reasons.append("DUPLICATE_ELEMENT_ID")
    if set(blueprint.reading_order) != ids or len(blueprint.reading_order) != len(ids): reasons.append("READING_ORDER_INCOMPLETE_OR_DUPLICATED")
    for element in blueprint.elements:
        if element.decorative and (element.claim_ids or element.evidence_refs or element.limitation_ids): reasons.append(f"ELEMENT_{element.element_id}_DECORATIVE_AS_EVIDENCE")
        if not element.decorative and not element.claim_ids: reasons.append(f"ELEMENT_{element.element_id}_CLAIM_MAP_MISSING")
        for claim_id in element.claim_ids:
            if claim_id not in claims:
                reasons.append(f"ELEMENT_{element.element_id}_UNKNOWN_CLAIM")
            else:
                mapped.add(claim_id)
                claim = claims[claim_id]
                if not set(element.evidence_refs).issubset(claim.evidence_refs): reasons.append(f"ELEMENT_{element.element_id}_EVIDENCE_MUTATED")
                if element.element_type == "CTA" and not set(claim.limitation_ids).issubset(element.limitation_ids): reasons.append(f"ELEMENT_{element.element_id}_CTA_LIMITATION_MISSING")
    reasons.extend(f"CLAIM_{x}_NOT_MAPPED" for x in sorted(set(claims) - mapped))
    if reasons: return InformationBlueprintAssessment("RETURN_TO_PREVIOUS", tuple(reasons))

    reasons = []
    if len({item.encoding_id for item in blueprint.encodings}) != len(blueprint.encodings): reasons.append("DUPLICATE_ENCODING_ID")
    for item in blueprint.encodings:
        claim = claims.get(item.claim_id)
        if claim is None:
            reasons.append(f"ENCODING_{item.encoding_id}_UNKNOWN_CLAIM"); continue
        allowed = False
        if claim.relationship == "TREND": allowed = item.chart_type == "LINE"
        elif claim.relationship == "COMPARISON": allowed = item.chart_type in {"BAR", "HORIZONTAL_BAR", "DOT"}
        elif claim.relationship == "RANKING": allowed = item.chart_type in {"HORIZONTAL_BAR", "DOT"}
        elif claim.relationship == "PART_TO_WHOLE": allowed = item.chart_type in {"STACKED_BAR", "PIE"}
        elif claim.relationship == "DISTRIBUTION": allowed = item.chart_type in {"HISTOGRAM", "BOX", "VIOLIN", "STRIP"}
        elif claim.relationship == "CORRELATION": allowed = item.chart_type == "SCATTER"
        elif claim.relationship == "FLOW": allowed = item.chart_type in {"SANKEY", "FUNNEL"}
        elif claim.relationship == "NETWORK": allowed = item.chart_type == "NETWORK"
        elif claim.relationship == "PERFORMANCE_TARGET": allowed = item.chart_type == "BULLET"
        elif claim.relationship == "MULTI_KPI": allowed = item.chart_type == "SMALL_MULTIPLES"
        elif claim.relationship == "GEOGRAPHIC": allowed = item.chart_type in {"CHOROPLETH", "BUBBLE_MAP", "HEX_MAP"}
        if item.relationship != claim.relationship: reasons.append(f"ENCODING_{item.encoding_id}_RELATIONSHIP_MUTATED")
        if item.unit != claim.unit or item.polarity != claim.polarity: reasons.append(f"ENCODING_{item.encoding_id}_MEANING_MUTATED")
        if not set(claim.attribution_ids).issubset(item.attribution_ids): reasons.append(f"ENCODING_{item.encoding_id}_ATTRIBUTION_MISSING")
        if not allowed: reasons.append(f"ENCODING_{item.encoding_id}_CHART_RELATIONSHIP_MISMATCH")
        if item.is_3d: reasons.append(f"ENCODING_{item.encoding_id}_THREE_D_FORBIDDEN")
        if item.dual_axis: reasons.append(f"ENCODING_{item.encoding_id}_DUAL_AXIS_FORBIDDEN")
        if item.color_only: reasons.append(f"ENCODING_{item.encoding_id}_COLOR_ONLY")
        if item.chart_type in {"BAR", "HORIZONTAL_BAR"} and not item.baseline_at_zero: reasons.append(f"ENCODING_{item.encoding_id}_ZERO_BASELINE_MISSING")
        if item.chart_type == "PIE" and item.series_count > 5: reasons.append(f"ENCODING_{item.encoding_id}_PIE_TOO_MANY_SERIES")
        if claim.uncertainty_required and not item.uncertainty_visible: reasons.append(f"ENCODING_{item.encoding_id}_UNCERTAINTY_HIDDEN")
    if reasons: return InformationBlueprintAssessment("CONTRADICTED", tuple(reasons))
    return InformationBlueprintAssessment("BLUEPRINT_READY_FOR_PRODUCTION_REVIEW", ())
