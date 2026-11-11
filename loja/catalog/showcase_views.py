"""Commercial collection pages disclose availability and never bypass cart gates."""
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from loja.catalog.presentation import model_groups, model_slug, present_product
from loja.catalog.print_catalog import catalog_context


@require_safe
@never_cache
def printable_catalog(request):
    return render(request, "loja/catalog/print_catalog.html", catalog_context(request.GET.get("modelo", "")))


@require_safe
@never_cache
def collection_model(request, slug):
    groups = model_groups()
    siblings = next((items for model, items in groups.items() if model_slug(model) == slug), None)
    if not siblings:
        raise Http404("Modelo não encontrado.")
    selected = request.GET.get("cor", "")
    product = next((p for p in siblings if p["reference_color"].casefold() == selected.casefold()), siblings[0])
    product = present_product(product, siblings)
    related = []
    for model, items in groups.items():
        if model != product["modelo"]:
            candidate = items[0].copy()
            candidate["showcase_url"] = "/colecao/" + model_slug(model) + "/"
            related.append(candidate)
    return render(request, "loja/catalog/product_detail.html", {
        "product": product, "related_products": related[:4], "meta_description": product["descricao"],
        "og_image": product["cover"], "noindex": not product["can_purchase"],
    })
