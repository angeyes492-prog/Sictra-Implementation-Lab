"""Shared validation primitives for source-governance boundaries."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from .common import ContractViolation


MAX_SOURCE_REGISTRATIONS = 50


def required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{name} must be a non-empty string")
    return value.strip()


def normalized_dns_host(value: str) -> str:
    try:
        parsed = urlsplit(f"//{value}")
        port = parsed.port
    except ValueError as error:
        raise ContractViolation("source host is invalid") from error
    if parsed.username or parsed.password or port is not None or parsed.path or parsed.query or parsed.fragment:
        raise ContractViolation("source host must not include credentials or port")
    host = parsed.hostname
    if not host:
        raise ContractViolation("source host is required")
    host = host.rstrip(".").casefold()
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ContractViolation("source host must be a DNS name, not an IP address")
    if host == "localhost" or host.endswith(".localhost"):
        raise ContractViolation("source host must not be localhost")
    return host
