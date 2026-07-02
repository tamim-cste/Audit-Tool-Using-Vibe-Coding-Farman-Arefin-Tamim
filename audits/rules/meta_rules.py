from urllib.parse import urlparse

from .base import Issue


def run(page: dict) -> list[Issue]:
    issues = []

    title = page["title"]
    title_len = len(title)
    if not title:
        issues.append(Issue(
            category="meta", status="fail",
            title="Title tag missing",
            description="The page has no <title> element.",
            current_value="Not found", affected_element="<title>",
            recommendation="Add a unique, descriptive <title> tag between 30 and 60 characters.",
        ))
    elif 30 <= title_len <= 60:
        issues.append(Issue(
            category="meta", status="pass",
            title="Title tag length is good",
            description="The page title is present and within the recommended length range.",
            current_value=f"\"{title}\" ({title_len} characters)", affected_element="<title>",
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="meta", status="warning",
            title="Title tag length is not optimal",
            description="The title is present but outside the recommended 30-60 character range, "
                         "which can cause it to be truncated or lack detail in search results.",
            current_value=f"\"{title}\" ({title_len} characters)", affected_element="<title>",
            recommendation="Adjust the title to fall between 30 and 60 characters.",
        ))

    description = page["meta_description"]
    desc_len = len(description)
    if not description:
        issues.append(Issue(
            category="meta", status="fail",
            title="Meta description missing",
            description="The page has no meta description, so search engines will generate their own snippet.",
            current_value="Not found", affected_element='<meta name="description">',
            recommendation="Add a unique meta description between 120 and 160 characters.",
        ))
    elif 120 <= desc_len <= 160:
        issues.append(Issue(
            category="meta", status="pass",
            title="Meta description length is good",
            description="The meta description is present and within the recommended length range.",
            current_value=f"\"{description}\" ({desc_len} characters)",
            affected_element='<meta name="description">', recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="meta", status="warning",
            title="Meta description length is not optimal",
            description="The meta description is present but outside the recommended 120-160 character range.",
            current_value=f"\"{description}\" ({desc_len} characters)",
            affected_element='<meta name="description">',
            recommendation="Adjust the description to fall between 120 and 160 characters.",
        ))

    canonical = page["canonical_url"]
    if not canonical:
        issues.append(Issue(
            category="meta", status="warning",
            title="Canonical tag missing",
            description="No canonical link was found, which can lead to duplicate content issues.",
            current_value="Not found", affected_element='<link rel="canonical">',
            recommendation="Add a self-referencing canonical tag pointing to the preferred URL for this page.",
        ))
    elif _same_url(canonical, page["final_url"]):
        issues.append(Issue(
            category="meta", status="pass",
            title="Canonical tag is self-referencing",
            description="The canonical tag correctly points to this page's own URL.",
            current_value=canonical, affected_element='<link rel="canonical">',
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="meta", status="warning",
            title="Canonical tag points elsewhere",
            description="The canonical tag points to a different URL than the one audited.",
            current_value=canonical, affected_element='<link rel="canonical">',
            recommendation="Verify this is intentional; otherwise point the canonical tag at this page's own URL.",
        ))

    robots = page["robots_meta"]
    if robots and "noindex" in robots.lower():
        issues.append(Issue(
            category="meta", status="fail",
            title="Page is blocked from indexing",
            description='The robots meta tag includes "noindex", which tells search engines not to index this page.',
            current_value=robots, affected_element='<meta name="robots">',
            recommendation='Remove "noindex" from the robots meta tag if this page should appear in search results.',
        ))
    else:
        issues.append(Issue(
            category="meta", status="pass",
            title="Page is not blocked from indexing",
            description="No noindex directive was found in the robots meta tag.",
            current_value=robots or "Not present (defaults to indexable)",
            affected_element='<meta name="robots">', recommendation="No action needed.",
        ))

    if page["lang"]:
        issues.append(Issue(
            category="meta", status="pass",
            title="Language attribute set",
            description="The <html> tag declares a language.",
            current_value=f'lang="{page["lang"]}"', affected_element="<html>",
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="meta", status="warning",
            title="Language attribute missing",
            description="The <html> tag has no lang attribute.",
            current_value="Not found", affected_element="<html>",
            recommendation='Add a lang attribute, e.g. <html lang="en">.',
        ))

    if page["charset"]:
        issues.append(Issue(
            category="meta", status="pass",
            title="Character encoding declared",
            description="The page declares a character encoding.",
            current_value=page["charset"], affected_element="<meta charset>",
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="meta", status="warning",
            title="Character encoding not declared",
            description="No charset declaration was found, which can lead to rendering issues in some browsers.",
            current_value="Not found", affected_element="<meta charset>",
            recommendation='Add <meta charset="UTF-8"> near the top of the <head>.',
        ))

    return issues


def _same_url(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    domain_a = pa.netloc.lower().removeprefix("www.")
    domain_b = pb.netloc.lower().removeprefix("www.")
    return domain_a == domain_b and pa.path.rstrip("/") == pb.path.rstrip("/")
