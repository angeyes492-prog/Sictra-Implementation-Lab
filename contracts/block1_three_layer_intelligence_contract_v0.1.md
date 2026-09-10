# Contract — Three-Layer Intelligence v0.1

## Identity and authority

E02 owns this controlled framing contract. It represents the user-approved
research model: `GLOBAL`, `SEGMENT`, and `ACCOUNT`. It does not authorize
source acquisition, create facts, access personal data, or promote a gate.

Geographic scale (`GLOBAL`/`REGIONAL`/`LOCAL` in the Workspace Scope Lens) is
orthogonal to these interpretation layers and must never be substituted for
them.

## Frame schema

Every frame has exactly: identity, layer, controlled `topic_keys`, geographic
scope, period, industry, pseudonymous `account_id`, global and segment parent
IDs, evidence IDs, certainty and confidence.

- A `GLOBAL` frame has no industry, account or parents.
- A `SEGMENT` frame requires a controlled industry key and at least one declared `GLOBAL`
  parent; it has no account or segment parent.
- An `ACCOUNT` frame requires industry, a pseudonymous account identifier, at
  least one declared `GLOBAL` parent and one declared `SEGMENT` parent.
- A bundle resolves parent identities and their exact layer. Unknown, duplicate
  or self-referential parents fail closed.
- Every Account frame uses the same controlled industry key as each referenced
  Segment frame.
- Only the controlled vocabulary in `TOPIC_CATALOG` is accepted. It covers the
  twelve domains in the thematic brief: geopolítica/comercio, marítimo, aéreo,
  aduanas, supply chain, tecnología, economía, sostenibilidad, infraestructura,
  riesgo, e-commerce e industrias.

## Epistemic and privacy limits

`evidence_ids` are references, not proof. Certainty remains one of the master
labels and confidence A–E. An Account frame contains only a pseudonymous ID;
company names, contacts, messages, credentials, products, routes or personal
data require their own future contract and authorization.

## Compatibility and non-claims

This is an additive v0.1 local contract. It does not migrate existing fixtures,
does not create persistent account profiles, does not fetch Internet content,
and does not make the UI production-ready.
