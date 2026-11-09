"""Public catalog request handling; queries and publication rules live in services."""
from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from loja import utils
from loja.catalog import services


@require_safe
@never_cache
def products(request):
    category = request.GET.get("categoria", "").strip()[:100]
    query = request.GET.get("q", "").strip()[:150]
    sort = request.GET.get("ordem", "destaques")
    if sort not in services.SORT_OPTIONS:
        sort = "destaques"
    products_list = services.filter_products(category=category, query=query, sort=sort)
    return render(request, "loja/catalog/products.html", {
        "products": products_list, "collections": services.get_collections(),
        "catalog_pending": not services.get_products(),
        "selected_category": next((c for c in services.get_categories()
                                   if utils.normalize(c) == utils.normalize(category)), category),
        "search_query": query, "product_count": len(products_list),
        "sort_options": services.SORT_OPTIONS, "selected_sort": sort,
        "meta_description": "Conheça a coleção Poedagar da VRAS Watches e encontre seu próximo relógio.",
        "noindex": bool(query or category or sort != "destaques"),
    })


@require_safe
@never_cache
def product_detail(request, id):
    if services.is_retired_product(id):
        messages.info(request, "O catálogo foi atualizado. Consulte a nova coleção VRAS Watches.")
        return redirect("loja:products")
    product = services.get_product(id)
    if not product:
        raise Http404("Produto nao encontrado")
    related = [p for p in services.get_products() if p["id"] != id]
    related.sort(key=lambda p: p["categoria"] != product["categoria"])
    structured = None
    if settings.SITE_URL and product["cover"] and product["can_purchase"]:
        structured = {"@context": "https://schema.org", "@type": "Product", "name": product["nome"],
                      "description": product["descricao"],
                      "image": [settings.SITE_URL + image["url"] for image in product["images"]],
                      "url": settings.SITE_URL + request.path,
                      "offers": {"@type": "Offer", "priceCurrency": "BRL", "price": str(product["preco"]),
                                 "url": settings.SITE_URL + request.path}}
    return render(request, "loja/catalog/product_detail.html", {
        "product": product, "related_products": related[:4], "product_schema": structured,
        "meta_description": product["descricao"], "og_image": product["cover"],
    })
