# Contract — Source Gateway v0.1

E02 accepts only manual bundles from a `BOUND` registration whose signed HMAC
binding is current and matches identity, scope, hosts, claims and byte limit.
Binding emission requires an `APPROVED` record with reviewer identity, date,
terms reference, source identity, hosts, claims and byte limit exactly matching
the registration. A rejected, future or mismatched review fails closed.
The output is an `OBSERVED` source attested by the existing evidence issuer.
The same registered source always has one provenance root.

No binding means no ingress. URLs must be HTTPS and in the registered DNS
allowlist; local/IP hosts, credentials, ports and fragments are rejected. The
gateway has no HTTP client, scraper, credential store or scheduling capability.
Attestation proves only controlled normalization, not truth, licensing,
independence, freshness beyond downstream validation, production or a gate.
