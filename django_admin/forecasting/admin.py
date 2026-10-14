from django.contrib import admin
from .models import ForecastAudit
@admin.register(ForecastAudit)
class ForecastAuditAdmin(admin.ModelAdmin):
    list_display = ("created_at", "model_name", "horizon_months", "last_observation_date", "is_stale")
    list_filter = ("model_name", "is_stale")
    readonly_fields = ("created_at",)
