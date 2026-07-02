from django.db import models


class Audit(models.Model):
    """One row per analyzed URL. Holds the extracted facts about the page
    plus the rolled-up score/counters. The row-level SEO findings live in
    AuditIssue (see below)."""

    # --- Request / crawl metadata -----------------------------------------
    submitted_url = models.URLField(max_length=2000)
    final_url = models.URLField(max_length=2000, blank=True)
    http_status_code = models.IntegerField(null=True, blank=True)
    page_load_time_ms = models.IntegerField(null=True, blank=True)
    html_size_kb = models.FloatField(null=True, blank=True)
    screenshot = models.ImageField(upload_to="screenshots/", null=True, blank=True)

    # --- Meta tags -----------------------------------------------------------
    title = models.CharField(max_length=1000, blank=True)
    meta_description = models.TextField(blank=True)
    canonical_url = models.URLField(max_length=2000, blank=True)
    robots_meta = models.CharField(max_length=255, blank=True)
    lang = models.CharField(max_length=20, blank=True)
    charset = models.CharField(max_length=50, blank=True)

    # --- Content ---------------------------------------------------------------
    h1_count = models.IntegerField(default=0)
    heading_structure = models.JSONField(default=list, blank=True)
    word_count = models.IntegerField(default=0)
    text_html_ratio = models.FloatField(default=0)

    # --- Images ------------------------------------------------------------------
    image_count = models.IntegerField(default=0)
    images_missing_alt = models.IntegerField(default=0)

    # --- Links -----------------------------------------------------------------
    internal_link_count = models.IntegerField(default=0)
    external_link_count = models.IntegerField(default=0)
    nofollow_link_count = models.IntegerField(default=0)

    # --- Social ---------------------------------------------------------------
    og_tags = models.JSONField(default=dict, blank=True)
    twitter_tags = models.JSONField(default=dict, blank=True)

    # --- Structured data --------------------------------------------------
    schema_types = models.JSONField(default=list, blank=True)

    # --- Rollup ----------------------------------------------------------------
    overall_score = models.IntegerField(default=0)
    passed_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    # If the crawl/audit failed entirely, the reason is recorded here (the
    # Audit row is still created for traceability, but issues will be empty).
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.final_url or self.submitted_url

    @property
    def title_length(self):
        return len(self.title or "")

    @property
    def meta_description_length(self):
        return len(self.meta_description or "")

    @property
    def score_color(self):
        """Hex color for the score gauge, matching the severity bands used
        throughout the dashboard (emerald / amber / rose)."""
        if self.overall_score >= 80:
            return "#10b981"
        if self.overall_score >= 50:
            return "#f59e0b"
        return "#f43f5e"


class AuditIssue(models.Model):
    """One row per individual SEO check performed against an Audit.
    Every row carries the five fields required by the report: status,
    description, current value, affected element, and recommendation."""

    STATUS_CHOICES = [
        ("pass", "Pass"),
        ("warning", "Warning"),
        ("fail", "Fail"),
    ]
    SEVERITY_CHOICES = [
        ("critical", "Critical"),
        ("warning", "Warning"),
        ("info", "Info"),
    ]
    CATEGORY_CHOICES = [
        ("meta", "Meta Tags"),
        ("content", "Content"),
        ("technical", "Technical"),
        ("images", "Images"),
        ("links", "Links"),
        ("social", "Social"),
        ("structured_data", "Structured Data"),
        ("accessibility", "Accessibility"),
        ("best_practices", "Best Practices"),
    ]

    audit = models.ForeignKey(Audit, related_name="issues", on_delete=models.CASCADE)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)

    title = models.CharField(max_length=255)
    description = models.TextField()
    current_value = models.CharField(max_length=1000, blank=True)
    affected_element = models.CharField(max_length=1000, blank=True)
    recommendation = models.TextField()

    # Accessibility checks intentionally re-surface signals already scored
    # under Meta/Content/Links with an accessibility framing. To avoid
    # double-counting the same underlying fact in the summary totals and
    # score, those rows are marked informational_only and excluded from
    # both the pass/warning/error tallies and the score calculation.
    informational_only = models.BooleanField(default=False)

    class Meta:
        ordering = ["category", "id"]

    def __str__(self):
        return f"[{self.status}] {self.title}"
