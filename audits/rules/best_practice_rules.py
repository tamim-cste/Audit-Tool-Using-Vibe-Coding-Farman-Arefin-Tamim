"""
Best-practice checks inspired by Google Lighthouse's SEO category.

Running real Lighthouse would mean shelling out to a Node.js + Chrome CLI
subprocess - a second heavy toolchain alongside Playwright. Instead, this
module re-implements the checks Lighthouse's SEO audit runs, using facts
already extracted in parser.py. Checks that would just duplicate Meta/
Technical categories (document-title, meta-description, viewport,
canonical) are intentionally left out here to avoid redundant rows in the
report - only the genuinely new checks live in this module.
"""

import re

from .base import Issue

_HREFLANG_RE = re.compile(r"^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})?$")


def run(page: dict) -> list[Issue]:
    issues = []
    links = page["links"]
    real_links = [l for l in links if l["href"]]
    uncrawlable = [
        l for l in real_links
        if l["href"] == "#" or l["href"].lower().startswith("javascript:")
    ]

    if real_links:
        if uncrawlable:
            sample = uncrawlable[0]
            issues.append(Issue(
                category="best_practices", status="warning",
                title="Some links are not crawlable",
                description="Search engine crawlers cannot follow links with empty, \"#\", or javascript: href values.",
                current_value=f"{len(uncrawlable)} of {len(real_links)} links are not crawlable",
                affected_element=f'<a href="{sample["href"]}">{sample["text"]}</a>',
                recommendation="Use real URLs in href attributes; if a link triggers JS behavior, "
                                "still point href at a working fallback URL.",
            ))
        else:
            issues.append(Issue(
                category="best_practices", status="pass",
                title="Links are crawlable",
                description="All links use real href values that search engine crawlers can follow.",
                current_value=f"{len(real_links)} crawlable link(s)", affected_element="<a>",
                recommendation="No action needed.",
            ))

    hreflang_links = page["hreflang_links"]
    if hreflang_links:
        invalid = [h for h in hreflang_links if not _is_valid_hreflang(h["hreflang"])]
        if invalid:
            sample = invalid[0]
            issues.append(Issue(
                category="best_practices", status="warning",
                title="Invalid hreflang value found",
                description="One or more hreflang attributes do not match a valid language/region code format.",
                current_value=f'Invalid hreflang="{sample["hreflang"]}"',
                affected_element=f'<link rel="alternate" hreflang="{sample["hreflang"]}">',
                recommendation='Use valid ISO language codes (and optional region), e.g. "en", "en-us", "fr-fr".',
            ))
        else:
            issues.append(Issue(
                category="best_practices", status="pass",
                title="hreflang values are valid",
                description="All hreflang attributes match a valid language/region code format.",
                current_value=f"{len(hreflang_links)} hreflang link(s) checked",
                affected_element='<link rel="alternate" hreflang="...">',
                recommendation="No action needed.",
            ))

    return issues


def _is_valid_hreflang(value: str) -> bool:
    value = (value or "").strip()
    return value.lower() == "x-default" or bool(_HREFLANG_RE.match(value))
