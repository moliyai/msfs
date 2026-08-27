from django.contrib import admin
from .models import VerificationItem, VerificationReport


class VerificationItemInline(admin.TabularInline):
    model = VerificationItem
    extra = 0
    readonly_fields = ("title", "value_display", "status")
    can_delete = False
    show_change_link = False


@admin.register(VerificationReport)
class VerificationReportAdmin(admin.ModelAdmin):
    list_display = ("pinfl", "check_type", "created_at", "total_items")
    list_filter = ("check_type", "created_at")
    search_fields = ("pinfl",)
    readonly_fields = ("pinfl", "check_type", "created_at")
    inlines = [VerificationItemInline]
    ordering = ("-created_at",)

    def total_items(self, obj):
        return obj.items.count()

    total_items.short_description = "Количество проверок"
