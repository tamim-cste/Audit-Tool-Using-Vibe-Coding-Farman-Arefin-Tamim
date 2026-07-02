"""
Shared Issue dataclass + small helpers used by every rule module.

Each rules/*_rules.py module exposes a single `run(page: dict) -> list[Issue]`
function. `page` is the dict produced by services.parser.parse_page(),
merged with a couple of crawl-metadata fields (http_status_code,
page_load_time_ms) added by the view before the rule engine runs.
"""

from dataclasses import dataclass
from typing import Optional

GENERIC_ANCHOR_TEXTS = {
    "click here", "here", "read more", "more", "link",
    "this page", "learn more", "more info", "details",
}


@dataclass
class Issue:
    category: str
    status: str  # "pass" | "warning" | "fail"
    title: str
    description: str
    current_value: str
    affected_element: str
    recommendation: str
    severity: Optional[str] = None  # "critical" | "warning" | "info"
    informational_only: bool = False

    def __post_init__(self):
        if self.severity is None:
            self.severity = {"fail": "critical", "warning": "warning", "pass": "info"}[self.status]


def has_skipped_heading_level(headings: list[dict]) -> bool:
    """True if the heading sequence jumps by more than one level at any
    point (e.g. h2 straight to h4), which breaks the document outline for
    both SEO crawlers and screen readers."""
    seen_max = 0
    for h in headings:
        level = int(h["tag"][1])
        if seen_max and level > seen_max + 1:
            return True
        seen_max = max(seen_max, level)
    return False
