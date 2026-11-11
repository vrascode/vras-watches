"""Read-only provenance dashboard inside Django admin; no network calls on GET."""
import json

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.http import require_safe

from loja.catalog.presentation import model_groups
from loja.media.reference_inventory import csv_inventory


def read_inventory():
    path = settings.BASE_DIR / "data/reference_media_inventory.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"items": []}


@require_safe
def reference_dashboard(request):
    inventory = read_inventory()
    groups = model_groups()
    rows = []
    for model, products in groups.items():
        rows.append({"model": model, "count": len(products), "product": products[0],
                     "media_count": sum(item["product"] == model for item in inventory["items"]),
                     "published": sum(p["can_purchase"] for p in products)})
    return TemplateResponse(request, "admin/reference_catalog.html", {
        **admin.site.each_context(request), "title": "Catálogo e procedência Poedagar",
        "model_rows": rows, "inventory": inventory, "items": inventory["items"],
        "downloaded": sum(item["download_status"] == "downloaded" for item in inventory["items"]),
        "errors": sum(item["download_status"] == "error" for item in inventory["items"]),
    })


@require_safe
def reference_csv(request):
    response = HttpResponse(csv_inventory(read_inventory()["items"]), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="vras-inventario-midias.csv"'
    response["Cache-Control"] = "no-store"
    return response
