from .base import Issue

REQUIRED_OG_TAGS = ["og:title", "og:description", "og:image"]


def run(page: dict) -> list[Issue]:
    issues = []
    og = page["og_tags"]
    twitter = page["twitter_tags"]

    missing_og = [tag for tag in REQUIRED_OG_TAGS if not og.get(tag)]
    if not missing_og:
        issues.append(Issue(
            category="social", status="pass",
            title="Open Graph tags present",
            description="og:title, og:description, and og:image are all set, so shared links "
                         "will render a rich preview on social platforms.",
            current_value=f"{len(REQUIRED_OG_TAGS)} of {len(REQUIRED_OG_TAGS)} required OG tags present",
            affected_element='<meta property="og:*">', recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="social", status="warning",
            title="Open Graph tags incomplete",
            description="Some Open Graph tags are missing, which can produce a broken or plain "
                         "preview when the page is shared on social platforms.",
            current_value=f"Missing: {', '.join(missing_og)}",
            affected_element='<meta property="og:*">',
            recommendation=f"Add the missing tag(s): {', '.join(missing_og)}.",
        ))

    if twitter.get("twitter:card"):
        issues.append(Issue(
            category="social", status="pass",
            title="Twitter Card type set",
            description="A twitter:card meta tag is present, controlling how the page appears "
                         "when shared on X/Twitter.",
            current_value=f"twitter:card={twitter.get('twitter:card')}",
            affected_element='<meta name="twitter:card">', recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="social", status="warning",
            title="Twitter Card type missing",
            description="No twitter:card meta tag was found, so shares on X/Twitter may fall "
                         "back to a generic link preview.",
            current_value="Not found", affected_element='<meta name="twitter:card">',
            recommendation='Add <meta name="twitter:card" content="summary_large_image"> (or another valid type).',
        ))

    return issues
