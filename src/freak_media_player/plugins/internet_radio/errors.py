"""User-facing classification for common public-stream failures."""

from __future__ import annotations


def describe_stream_error(message: str | None) -> str:
    detail = (message or "").strip()
    folded = detail.casefold()
    if any(token in folded for token in ("timed out", "timeout")):
        return "Connection timed out."
    if any(token in folded for token in ("name or service", "getaddrinfo", "dns")):
        return "The station host could not be resolved (DNS)."
    if any(token in folded for token in ("certificate", "ssl", "tls")):
        return "The station's secure connection failed (TLS)."
    if "playlist" in folded:
        return detail or "The station playlist is invalid."
    if any(token in folded for token in ("codec", "decoder", "invalid data")):
        return "The stream codec or format is not supported."
    if any(token in folded for token in ("403", "forbidden")):
        return "The station refused the connection (HTTP 403)."
    if any(token in folded for token in ("404", "not found")):
        return "The station stream was not found (HTTP 404)."
    return detail or "The station is not reachable."
