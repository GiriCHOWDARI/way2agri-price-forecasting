from django.db import models
class ForecastAudit(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    horizon_months = models.PositiveSmallIntegerField(default=12)
    model_name = models.CharField(max_length=100, default="Naive baseline")
    last_observation_date = models.DateField(null=True, blank=True)
    is_stale = models.BooleanField(default=True)
    note = models.CharField(max_length=500, blank=True)
    def __str__(self):
        return f"{self.model_name} · {self.created_at:%Y-%m-%d %H:%M}"
