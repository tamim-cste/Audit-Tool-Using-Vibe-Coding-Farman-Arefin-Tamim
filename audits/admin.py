from django.contrib import admin

from .models import Audit, AuditIssue


class AuditIssueInline(admin.TabularInline):
    model = AuditIssue
    extra = 0
    fields = ("category", "status", "severity", "title", "current_value", "informational_only")
    readonly_fields = fields


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("id", "submitted_url", "overall_score", "http_status_code", "created_at")
    list_filter = ("http_status_code",)
    search_fields = ("submitted_url", "final_url", "title")
    inlines = [AuditIssueInline]


@admin.register(AuditIssue)
class AuditIssueAdmin(admin.ModelAdmin):
    list_display = ("id", "audit", "category", "status", "severity", "title")
    list_filter = ("category", "status", "severity", "informational_only")
