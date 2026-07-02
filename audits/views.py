"""
Three views, no background workers, no polling:

  index    - GET  the landing page with the search box
  analyze  - POST validates the URL, runs the full pipeline synchronously
             (Playwright -> parse -> rules -> score -> save), then redirects
             to the report page. This is the single request/response cycle
             described in the architecture: no Celery, no queue, no thread
             pool - the request simply waits the 3-15s it takes to crawl.
  report   - GET  the saved Audit + its AuditIssue rows, server-rendered.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from .forms import URLSubmissionForm
from .models import Audit, AuditIssue
from .rules import (
    accessibility_rules,
    best_practice_rules,
    content_rules,
    image_rules,
    link_rules,
    meta_rules,
    social_rules,
    structured_data_rules,
    technical_rules,
)
from .services import scorer
from .services.crawler import CrawlerError, PlaywrightCrawler
from .services.parser import parse_page
from .services.security import URLSecurityError, validate_url

RULE_MODULES = [
    meta_rules,
    content_rules,
    technical_rules,
    image_rules,
    link_rules,
    social_rules,
    structured_data_rules,
    accessibility_rules,
    best_practice_rules,
]


def index(request):
    form = URLSubmissionForm()
    return render(request, "audits/index.html", {"form": form})


def analyze(request):
    if request.method != "POST":
        return redirect("audits:index")

    form = URLSubmissionForm(request.POST)
    if not form.is_valid():
        return render(request, "audits/index.html", {"form": form}, status=400)

    url = form.cleaned_data["url"]

    # 1. SSRF guard, before the URL is ever handed to the browser.
    try:
        validate_url(url)
    except URLSecurityError as exc:
        form.add_error("url", str(exc))
        return render(request, "audits/index.html", {"form": form}, status=400)

    # 2. Load exactly this one page with Playwright.
    crawler = PlaywrightCrawler()
    screenshot_rel_path = f"screenshots/{uuid.uuid4().hex}.png"
    screenshot_abs_path = Path(settings.MEDIA_ROOT) / screenshot_rel_path
    screenshot_abs_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        crawl_result = crawler.fetch(url, screenshot_path=str(screenshot_abs_path))
    except CrawlerError as exc:
        form.add_error("url", str(exc))
        return render(request, "audits/index.html", {"form": form}, status=400)

    # 3. Re-check the final (post-redirect) host - a public URL could
    #    redirect to something internal.
    try:
        validate_url(crawl_result["final_url"])
    except URLSecurityError as exc:
        form.add_error("url", f"Blocked after redirect: {exc}")
        return render(request, "audits/index.html", {"form": form}, status=400)

    # 4. Parse the rendered DOM (post-JS), never the raw source.
    page_data = parse_page(crawl_result["html"], crawl_result["final_url"])
    page_data["http_status_code"] = crawl_result["status_code"]
    page_data["page_load_time_ms"] = crawl_result["load_time_ms"]

    schema_types = sorted({t for block in page_data["json_ld_blocks"] for t in block["types"]})

    audit = Audit.objects.create(
        submitted_url=url,
        final_url=page_data["final_url"],
        http_status_code=page_data["http_status_code"],
        page_load_time_ms=page_data["page_load_time_ms"],
        html_size_kb=page_data["html_size_kb"],
        screenshot=screenshot_rel_path if screenshot_abs_path.exists() else "",
        title=page_data["title"],
        meta_description=page_data["meta_description"],
        canonical_url=page_data["canonical_url"][:2000],
        robots_meta=page_data["robots_meta"],
        lang=page_data["lang"],
        charset=page_data["charset"],
        h1_count=page_data["h1_count"],
        heading_structure=page_data["headings"],
        word_count=page_data["word_count"],
        text_html_ratio=page_data["text_html_ratio"],
        image_count=page_data["image_count"],
        images_missing_alt=len(page_data["images_missing_alt"]),
        internal_link_count=len(page_data["internal_links"]),
        external_link_count=len(page_data["external_links"]),
        nofollow_link_count=len(page_data["nofollow_links"]),
        og_tags=page_data["og_tags"],
        twitter_tags=page_data["twitter_tags"],
        schema_types=schema_types,
    )

    # 5. Run every rule module against the rendered-page facts.
    issues = []
    for module in RULE_MODULES:
        issues.extend(module.run(page_data))

    AuditIssue.objects.bulk_create([
        AuditIssue(
            audit=audit,
            category=issue.category,
            status=issue.status,
            severity=issue.severity,
            title=issue.title,
            description=issue.description,
            current_value=issue.current_value,
            affected_element=issue.affected_element,
            recommendation=issue.recommendation,
            informational_only=issue.informational_only,
        )
        for issue in issues
    ])

    # 6. Score + summary counts, excluding informational-only (accessibility)
    #    rows so the same underlying signal is never counted twice.
    scoring_issues = [i for i in issues if not i.informational_only]
    audit.overall_score = scorer.calculate_score(scoring_issues)
    audit.passed_count = sum(1 for i in scoring_issues if i.status == "pass")
    audit.warning_count = sum(1 for i in scoring_issues if i.status == "warning")
    audit.error_count = sum(1 for i in scoring_issues if i.status == "fail")
    audit.save()

    return redirect("audits:report", audit_id=audit.id)


def report(request, audit_id):
    audit = get_object_or_404(Audit, id=audit_id)
    issues = audit.issues.all()
    form = URLSubmissionForm(initial={"url": audit.submitted_url})
    return render(request, "audits/report.html", {"audit": audit, "issues": issues, "form": form})
