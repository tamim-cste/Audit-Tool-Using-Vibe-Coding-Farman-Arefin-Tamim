from .base import Issue

SLOW_LOAD_THRESHOLD_MS = 3000


def run(page: dict) -> list[Issue]:
    issues = []

    final_url = page["final_url"]
    if final_url.startswith("https://"):
        issues.append(Issue(
            category="technical", status="pass",
            title="Page is served over HTTPS",
            description="The page loads over a secure HTTPS connection.",
            current_value=final_url, affected_element="URL scheme",
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="technical", status="fail",
            title="Page is not served over HTTPS",
            description="The page loads over plain HTTP, which browsers flag as not secure and which can affect rankings.",
            current_value=final_url, affected_element="URL scheme",
            recommendation="Serve the page over HTTPS with a valid SSL certificate.",
        ))

    status = page.get("http_status_code")
    if status == 200:
        issues.append(Issue(
            category="technical", status="pass",
            title="Page returns a 200 OK response",
            description="The server responded with a successful status code.",
            current_value=str(status), affected_element="HTTP response",
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="technical", status="fail",
            title="Page does not return a 200 OK response",
            description="The server responded with a non-success status code, which can prevent proper indexing.",
            current_value=str(status) if status else "Unknown", affected_element="HTTP response",
            recommendation="Investigate why this page returns a non-200 status and fix the underlying issue.",
        ))

    if page["viewport"]:
        issues.append(Issue(
            category="technical", status="pass",
            title="Viewport meta tag present",
            description="A viewport meta tag is present, which is required for proper mobile rendering.",
            current_value=page["viewport"], affected_element='<meta name="viewport">',
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="technical", status="fail",
            title="Viewport meta tag missing",
            description="No viewport meta tag was found, which can cause the page to render poorly on mobile devices.",
            current_value="Not found", affected_element='<meta name="viewport">',
            recommendation='Add <meta name="viewport" content="width=device-width, initial-scale=1">.',
        ))

    if page["favicon"]:
        issues.append(Issue(
            category="technical", status="pass",
            title="Favicon present",
            description="A favicon link was found in the page head.",
            current_value=page["favicon"], affected_element='<link rel="icon">',
            recommendation="No action needed.",
        ))
    else:
        issues.append(Issue(
            category="technical", status="warning",
            title="Favicon missing",
            description="No favicon link was found, which can affect brand presentation in browser tabs and search results.",
            current_value="Not found", affected_element='<link rel="icon">',
            recommendation='Add a <link rel="icon" href="..."> pointing to a favicon file.',
        ))

    load_time = page.get("page_load_time_ms")
    if load_time is not None:
        if load_time <= SLOW_LOAD_THRESHOLD_MS:
            issues.append(Issue(
                category="technical", status="pass",
                title="Page load time is good",
                description="The page finished loading within an acceptable time.",
                current_value=f"{load_time} ms", affected_element="Page load",
                recommendation="No action needed.",
            ))
        else:
            issues.append(Issue(
                category="technical", status="warning",
                title="Page load time is slow",
                description=f"The page took longer than {SLOW_LOAD_THRESHOLD_MS / 1000:.0f} seconds to finish loading, "
                             "which can affect both user experience and rankings.",
                current_value=f"{load_time} ms", affected_element="Page load",
                recommendation="Investigate render-blocking resources, large assets, or slow server response time.",
            ))

    return issues
