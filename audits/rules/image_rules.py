from .base import Issue


def run(page: dict) -> list[Issue]:
    issues = []
    images = page["images"]
    total = page["image_count"]
    missing_alt = page["images_missing_alt"]

    if total == 0:
        issues.append(Issue(
            category="images", status="pass",
            title="No images on page",
            description="The page has no <img> elements, so there is nothing to check here.",
            current_value="0 images", affected_element="<img>",
            recommendation="No action needed.",
        ))
    elif not missing_alt:
        issues.append(Issue(
            category="images", status="pass",
            title="All images have alt text",
            description="Every image on the page has a non-empty alt attribute.",
            current_value=f"{total} of {total} images have alt text", affected_element="<img>",
            recommendation="No action needed.",
        ))
    else:
        sample = missing_alt[0]
        issues.append(Issue(
            category="images", status="warning",
            title="Images missing alt text",
            description="Some images have no alt attribute, which hurts both accessibility and image SEO.",
            current_value=f"{len(missing_alt)} of {total} images missing alt text",
            affected_element=f'<img src="{sample.get("src", "")}">',
            recommendation="Add descriptive alt text to every meaningful image; use alt=\"\" only for purely decorative images.",
        ))

    no_src = [img for img in images if not img.get("src")]
    if no_src:
        issues.append(Issue(
            category="images", status="fail",
            title="Images missing a src attribute",
            description="One or more <img> tags have no src attribute and will not render.",
            current_value=f"{len(no_src)} image(s) with no src", affected_element="<img>",
            recommendation="Provide a valid src for every image, or remove the empty tag.",
        ))

    return issues
