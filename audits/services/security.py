"""
SSRF guard.

The app fetches whatever URL a visitor submits using a server-side headless
browser. Without validation, that's a classic SSRF vector (e.g. someone
pointing the tool at http://169.254.169.254/... to probe cloud metadata, or
at an internal service on the same network as the server).

validate_url() is called twice per audit:
  1. Before the crawler ever runs, against the submitted URL.
  2. After the crawl completes, against the final URL (in case a redirect
     took the browser somewhere different than what was submitted).

It is also reused by the broken-link checker in rules/link_rules.py before
issuing outbound HEAD/GET requests to links found on the page.
"""

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}

_BLOCKED_HOSTNAMES = {"localhost"}


class URLSecurityError(Exception):
    """Raised when a submitted URL fails the SSRF/scheme safety checks."""


def validate_url(url: str) -> None:
    """Raises URLSecurityError if the URL is unsafe to fetch server-side.
    Returns None (no value) on success."""

    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise URLSecurityError("Only http:// and https:// URLs are allowed.")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise URLSecurityError("The URL must include a valid hostname.")

    if hostname in _BLOCKED_HOSTNAMES:
        raise URLSecurityError("Local addresses cannot be audited.")

    # If the hostname is itself a raw IP literal, ipaddress can parse it
    # directly. Otherwise we resolve it via DNS and check every returned
    # address (a hostname can resolve to multiple IPs).
    try:
        candidate_ips = [ipaddress.ip_address(hostname)]
    except ValueError:
        try:
            infos = socket.getaddrinfo(hostname, None)
        except socket.gaierror as exc:
            raise URLSecurityError(f"Could not resolve host: {hostname}") from exc
        candidate_ips = [ipaddress.ip_address(info[4][0]) for info in infos]

    for ip in candidate_ips:
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise URLSecurityError(
                "This URL resolves to a private or restricted network address "
                "and cannot be audited."
            )
