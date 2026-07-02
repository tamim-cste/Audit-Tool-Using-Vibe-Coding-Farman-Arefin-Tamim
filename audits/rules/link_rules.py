"""
Link checks, including an optional broken-link scan.

The broken-link check makes lightweight HEAD (falling back to GET) requests
to a bounded number of unique hrefs found ON the submitted page. This is
NOT crawling: we never render, parse, or follow links from those pages -
we only check their HTTP status, the same category of operation as
checking an image's dimensions. Each candidate URL is re-validated through
the same SSRF guard used for the main submitted URL before we request it,
since a malicious page could otherwise use this feature to probe internal
network addresses through our server.
"""

from django.conf import settings

from .base import GENERIC_ANCHOR_TEXTS, Issue
from ..services.security import URLSecurityError, validate_url


def run(page: dict) -> list[Issue]:
    issues = []
    links = page["links"]
    internal = page["internal_links"]
    external = page["external_links"]
    nofollow = page["nofollow_links"]
    total_links = len(links)

    issues.append(Issue(
        category="links", status="pass",
        title="Internal and external links counted",
        description="Counted links pointing within the site versus links pointing to other domains.",
        current_value=f"{len(internal)} internal, {len(external)} external",
        affected_element="<a>", recommendation="No action needed.",
    ))

    if total_links and len(nofollow) / total_links > 0.5:
        issues.append(Issue(
            category="links", status="warning",
            title="A large share of links are nofollow",
            description='More than half of the links on the page carry rel="nofollow", '
                         "which can limit how link equity flows through the site.",
            current_value=f"{len(nofollow)} of {total_links} links are nofollow",
            affected_element='<a rel="nofollow">',
            recommendation="Review whether nofollow is intentional for each of these links.",
        ))
    else:
        issues.append(Issue(
            category="links", status="pass",
            title="Nofollow usage looks reasonable",
            description="Nofollow links make up a normal share of the total link count.",
            current_value=f"{len(nofollow)} of {total_links} links are nofollow",
            affected_element='<a rel="nofollow">', recommendation="No action needed.",
        ))

    generic_links = [l for l in links if l["text"].strip().lower() in GENERIC_ANCHOR_TEXTS]
    if generic_links:
        sample = generic_links[0]
        issues.append(Issue(
            category="links", status="warning",
            title="Generic anchor text found",
            description='Some links use non-descriptive text like "click here", which is less useful '
                         "for SEO and for screen reader users navigating by link.",
            current_value=f'{len(generic_links)} link(s) with generic text, e.g. "{sample["text"]}"',
            affected_element=f'<a href="{sample["href"]}">{sample["text"]}</a>',
            recommendation='Rewrite link text to describe the destination, e.g. "Download the pricing guide" '
                            'instead of "click here".',
        ))
    else:
        issues.append(Issue(
            category="links", status="pass",
            title="Link text is descriptive",
            description='No generic placeholder link text (like "click here") was found.',
            current_value="No generic anchor text detected", affected_element="<a>",
            recommendation="No action needed.",
        ))

    if links:
        broken = _check_broken_links(links)
        if broken:
            sample = broken[0]
            issues.append(Issue(
                category="links", status="fail",
                title="Broken links detected",
                description="One or more links on the page point to URLs that returned an error when checked.",
                current_value=f'{len(broken)} broken link(s), e.g. {sample["url"]} ({sample["status"]})',
                affected_element=f'<a href="{sample["url"]}">',
                recommendation="Fix or remove links that return 4xx/5xx errors.",
            ))
        else:
            issues.append(Issue(
                category="links", status="pass",
                title="No broken links detected",
                description="All checked links returned a successful response.",
                current_value="0 broken links found among checked links", affected_element="<a>",
                recommendation="No action needed.",
            ))

    return issues


def _check_broken_links(links: list[dict]) -> list[dict]:
    import requests

    limit = getattr(settings, "SEO_AUDIT_MAX_LINKS_TO_CHECK", 20)
    timeout = getattr(settings, "SEO_AUDIT_LINK_CHECK_TIMEOUT_S", 4)

    seen = set()
    candidates = []
    for link in links:
        resolved = link["resolved"]
        if resolved and resolved.startswith(("http://", "https://")) and resolved not in seen:
            seen.add(resolved)
            candidates.append(resolved)
        if len(candidates) >= limit:
            break

    broken = []
    for url in candidates:
        try:
            validate_url(url)
        except URLSecurityError:
            continue  # skip links pointing at internal/restricted addresses

        try:
            resp = requests.head(url, allow_redirects=True, timeout=timeout)
            if resp.status_code >= 400:
                # Some servers don't implement HEAD correctly - retry with GET.
                resp = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
            if resp.status_code >= 400:
                broken.append({"url": url, "status": resp.status_code})
        except requests.RequestException:
            broken.append({"url": url, "status": "unreachable"})

    return broken
