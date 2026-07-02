"""
SEO-relevant accessibility checks.

These deliberately re-surface signals already scored under Meta/Content/
Links (alt text, lang attribute, heading order, link text) with an
accessibility framing, rather than inventing new "padding" checks -
accessibility and SEO share a lot of the same underlying signals. To avoid
double-counting the same fact in the summary totals and overall score,
every Issue here is marked informational_only=True.
"""

from .base import GENERIC_ANCHOR_TEXTS, Issue, has_skipped_heading_level


def run(page: dict) -> list[Issue]:
    issues = []
    total_images = page["image_count"]
    missing_alt = len(page["images_missing_alt"])

    if total_images == 0:
        issues.append(Issue(
            category="accessibility", status="pass", informational_only=True,
            title="No images to evaluate",
            description="The page has no <img> elements, so there is no image alt-text context for screen readers to miss.",
            current_value="0 images", affected_element="<img>", recommendation="No action needed.",
        ))
    elif missing_alt == 0:
        issues.append(Issue(
            category="accessibility", status="pass", informational_only=True,
            title="All images have alt text",
            description="Every image has a non-empty alt attribute, helping screen reader users understand image content.",
            current_value=f"{total_images} of {total_images} images have alt text",
            affected_element="<img>", recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="accessibility", status="warning", informational_only=True,
            title="Some images are missing alt text",
            description="Screen readers cannot describe images with no alt attribute.",
            current_value=f"{missing_alt} of {total_images} images missing alt text",
            affected_element="<img>",
            recommendation="Add descriptive alt text to every meaningful image.",
        ))

    if page["lang"]:
        issues.append(Issue(
            category="accessibility", status="pass", informational_only=True,
            title="Page language declared",
            description="The <html> element declares a language, letting screen readers use correct pronunciation rules.",
            current_value=f'lang="{page["lang"]}"', affected_element="<html>",
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="accessibility", status="fail", informational_only=True,
            title="Page language not declared",
            description="The <html> element has no lang attribute, so screen readers may mispronounce content.",
            current_value="Not found", affected_element="<html>",
            recommendation='Add a lang attribute to the <html> tag, e.g. <html lang="en">.',
        ))

    if has_skipped_heading_level(page["headings"]):
        issues.append(Issue(
            category="accessibility", status="warning", informational_only=True,
            title="Heading levels are skipped",
            description="Screen reader users navigate by heading level; skipping levels makes the outline harder to follow.",
            current_value="Heading levels skip at least one step", affected_element="<h1>-<h6>",
            recommendation="Use heading levels in order without skipping a level.",
        ))
    else:
        issues.append(Issue(
            category="accessibility", status="pass", informational_only=True,
            title="Heading levels are sequential",
            description="Heading levels increase in order without skipping, supporting screen-reader navigation.",
            current_value="No skipped heading levels", affected_element="<h1>-<h6>",
            recommendation="No action needed.",
        ))

    generic_links = [l for l in page["links"] if l["text"].strip().lower() in GENERIC_ANCHOR_TEXTS]
    if generic_links:
        issues.append(Issue(
            category="accessibility", status="warning", informational_only=True,
            title="Some links use non-descriptive text",
            description="Screen reader users often navigate by pulling up a list of links out of context; "
                         'generic text like "click here" gives them no information about the destination.',
            current_value=f"{len(generic_links)} link(s) with generic text",
            affected_element="<a>",
            recommendation="Use descriptive link text that makes sense out of context.",
        ))
    else:
        issues.append(Issue(
            category="accessibility", status="pass", informational_only=True,
            title="Link text is descriptive",
            description="No generic placeholder link text was found.",
            current_value="No generic anchor text detected", affected_element="<a>",
            recommendation="No action needed.",
        ))

    return issues
