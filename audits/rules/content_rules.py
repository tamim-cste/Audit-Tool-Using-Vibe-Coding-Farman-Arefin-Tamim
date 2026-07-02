from .base import Issue, has_skipped_heading_level

THIN_CONTENT_THRESHOLD = 300


def run(page: dict) -> list[Issue]:
    issues = []

    h1_count = page["h1_count"]
    if h1_count == 1:
        issues.append(Issue(
            category="content", status="pass",
            title="Exactly one H1 found",
            description="The page has a single H1, which gives search engines a clear primary topic signal.",
            current_value="1 <h1>", affected_element="<h1>", recommendation="No action needed.",
        ))
    elif h1_count == 0:
        issues.append(Issue(
            category="content", status="fail",
            title="No H1 found",
            description="The page has no H1 heading, making it harder for search engines to identify the main topic.",
            current_value="0 <h1>", affected_element="<h1>",
            recommendation="Add exactly one H1 that describes the page's main topic.",
        ))
    else:
        issues.append(Issue(
            category="content", status="warning",
            title="Multiple H1 tags found",
            description="The page has more than one H1 heading, which can dilute the primary topic signal.",
            current_value=f"{h1_count} <h1> tags", affected_element="<h1>",
            recommendation="Keep exactly one H1 per page and demote the others to H2 or lower.",
        ))

    if has_skipped_heading_level(page["headings"]):
        issues.append(Issue(
            category="content", status="warning",
            title="Heading hierarchy skips a level",
            description="One or more heading levels are skipped (e.g. H2 followed directly by H4), "
                         "which breaks the logical outline of the page.",
            current_value="Skipped heading level detected", affected_element="<h1>-<h6>",
            recommendation="Use heading levels in sequential order without skipping.",
        ))
    else:
        issues.append(Issue(
            category="content", status="pass",
            title="Heading hierarchy is sequential",
            description="Heading levels increase in order without skipping a level.",
            current_value="No skipped heading levels", affected_element="<h1>-<h6>",
            recommendation="No action needed.",
        ))

    word_count = page["word_count"]
    if word_count >= THIN_CONTENT_THRESHOLD:
        issues.append(Issue(
            category="content", status="pass",
            title="Content length looks sufficient",
            description="The page has enough visible text content for search engines to evaluate topical relevance.",
            current_value=f"{word_count} words", affected_element="<body>",
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="content", status="warning",
            title="Thin content detected",
            description="The page has relatively little visible text, which can make it harder to rank for meaningful queries.",
            current_value=f"{word_count} words", affected_element="<body>",
            recommendation=f"Add more unique, useful content - aim for at least {THIN_CONTENT_THRESHOLD} words where relevant.",
        ))

    return issues
