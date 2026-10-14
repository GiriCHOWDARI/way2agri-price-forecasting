from django.contrib import admin
from django.urls import path
from forecasting.views import dashboard, forecast_proxy

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("api/forecast-proxy/", forecast_proxy, name="forecast-proxy"),
]
