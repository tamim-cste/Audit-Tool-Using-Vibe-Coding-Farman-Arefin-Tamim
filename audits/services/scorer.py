"""
Turns a flat list of rules.base.Issue objects into a single 0-100 overall
score. Each category is weighted, and within a category each non-pass
issue deducts points proportional to its severity. informational_only
issues (the accessibility category) are excluded before this ever runs -
see views.py - so they never affect the score.
"""

CATEGORY_WEIGHTS = {
    "meta": 20,
    "content": 15,
    "technical": 20,
    "images": 10,
    "links": 15,
    "social": 10,
    "structured_data": 10,
    "best_practices": 5,
}

SEVERITY_PENALTY = {"critical": 1.0, "warning": 0.5, "info": 0.15}


def calculate_score(issues: list) -> int:
    """issues: list of rules.base.Issue (informational_only ones already filtered out)."""
    if not issues:
        return 100

    by_category: dict[str, list] = {}
    for issue in issues:
        by_category.setdefault(issue.category, []).append(issue)

    total_weight = 0
    weighted_sum = 0.0

    for category, cat_issues in by_category.items():
        weight = CATEGORY_WEIGHTS.get(category, 5)
        total_weight += weight

        deduction = 0.0
        per_issue_share = 100 / len(cat_issues)
        for issue in cat_issues:
            if issue.status == "pass":
                continue
            deduction += SEVERITY_PENALTY.get(issue.severity, 0.5) * per_issue_share

        category_score = max(0.0, 100.0 - deduction)
        weighted_sum += category_score * weight

    if total_weight == 0:
        return 100

    overall = weighted_sum / total_weight
    return int(round(max(0.0, min(100.0, overall))))
