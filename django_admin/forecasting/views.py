import json
from urllib.error import URLError, HTTPError
from urllib.request import urlopen
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

FASTAPI_BASE_URL = "http://127.0.0.1:8000"

def dashboard(request):
    return render(request, "forecasting/dashboard.html", {"api_url": FASTAPI_BASE_URL})

@require_GET
def forecast_proxy(request):
    horizon = request.GET.get("horizon", "12")
    if not horizon.isdigit() or not 1 <= int(horizon) <= 36:
        return JsonResponse({"detail": "horizon must be an integer from 1 to 36"}, status=400)
    try:
        with urlopen(f"{FASTAPI_BASE_URL}/forecast?horizon={horizon}", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return JsonResponse(payload)
    except HTTPError as exc:
        return JsonResponse({"detail": f"Forecast service returned HTTP {exc.code}"}, status=502)
    except (URLError, TimeoutError):
        return JsonResponse({"detail": "Forecast service unavailable. Start FastAPI on port 8000."}, status=503)
