from .base import Issue


def run(page: dict) -> list[Issue]:
    issues = []
    blocks = page["json_ld_blocks"]

    if not blocks:
        issues.append(Issue(
            category="structured_data", status="warning",
            title="No structured data found",
            description="No JSON-LD structured data block was detected on the page.",
            current_value="0 JSON-LD blocks found",
            affected_element='<script type="application/ld+json">',
            recommendation="Add JSON-LD structured data relevant to the page (e.g. Organization, "
                            "Product, Article) to help search engines understand the content.",
        ))
        return issues

    invalid_blocks = [b for b in blocks if not b["valid"]]
    if invalid_blocks:
        issues.append(Issue(
            category="structured_data", status="fail",
            title="Invalid structured data found",
            description="One or more JSON-LD blocks could not be parsed as valid JSON.",
            current_value=f"{len(invalid_blocks)} of {len(blocks)} JSON-LD block(s) invalid",
            affected_element='<script type="application/ld+json">',
            recommendation="Fix the JSON syntax errors in the affected structured data block(s).",
        ))
    else:
        issues.append(Issue(
            category="structured_data", status="pass",
            title="Structured data is valid JSON",
            description="All JSON-LD blocks on the page are syntactically valid.",
            current_value=f"{len(blocks)} valid JSON-LD block(s)",
            affected_element='<script type="application/ld+json">',
            recommendation="No action needed.",
        ))

    all_types = sorted({t for b in blocks for t in b["types"]})
    if all_types:
        issues.append(Issue(
            category="structured_data", status="pass",
            title="Structured data types detected",
            description="The page declares one or more recognized schema.org types.",
            current_value=", ".join(all_types),
            affected_element='<script type="application/ld+json">',
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="structured_data", status="warning",
            title="No recognized schema type found",
            description="Structured data is present but no @type could be identified in it.",
            current_value="No @type found in JSON-LD",
            affected_element='<script type="application/ld+json">',
            recommendation='Ensure each JSON-LD block includes a valid @type (e.g. "Organization", "Product", "Article").',
        ))

    return issues
