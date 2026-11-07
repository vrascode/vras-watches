from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.cache import patch_cache_control
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_safe, require_POST
from django.views.decorators.cache import never_cache

from loja import media, services


@require_safe
@never_cache
def home(request):
    manifest = media.load_media()
    catalog = services.get_products()
    return render(request, "loja/home.html", {
        "featured_products": services.get_featured_products(catalog),
        "new_products": services.get_new_products(catalog),
        "collections": services.get_collections(catalog),
        "style_edits": services.get_style_edits(catalog),
        "hero_media": media.section_media(manifest, "hero"),
        "editorial_media": media.section_media(manifest, "editorial"),
        "campaign_media": media.section_media(manifest, "campaign"),
        "instagram_posts": media.instagram_posts(manifest),
        "og_image": media.section_media(manifest, "hero")["image"] or (
            media.section_media(manifest, "hero")["video"] or {}).get("poster"),
        "meta_description": "VRAS Watches. O tempo \u00e9 seu. O estilo tamb\u00e9m. Conhe\u00e7a os modelos e encontre seu pr\u00f3ximo rel\u00f3gio.",
    })


@require_safe
@never_cache
def products(request):
    category = request.GET.get("categoria", "").strip()[:100]
    query = request.GET.get("q", "").strip()[:150]
    sort = request.GET.get("ordem", "destaques")
    if sort not in services.SORT_OPTIONS:
        sort = "destaques"
    products_list = services.filter_products(category=category, query=query, sort=sort)
    return render(request, "loja/products.html", {
        "products": products_list, "collections": services.get_collections(),
        "selected_category": next((c for c in services.get_categories()
                                   if services.normalize(c) == services.normalize(category)), category),
        "search_query": query, "product_count": len(products_list),
        "sort_options": services.SORT_OPTIONS, "selected_sort": sort,
        "meta_description": "Explore o cat\u00e1logo VRAS Watches: Cl\u00e1ssicos, Maestro, Seleção VRAS, Lan\u00e7amentos e Esportivos.",
        "noindex": bool(query or category or sort != "destaques"),
    })


@require_safe
@never_cache
def product_detail(request, id):
    product = services.get_product(id)
    if not product:
        raise Http404("Produto nao encontrado")
    related = [p for p in services.get_products() if p["id"] != id]
    related.sort(key=lambda p: p["categoria"] != product["categoria"])
    structured = None
    if settings.SITE_URL and product["cover"]:
        structured = {"@context": "https://schema.org", "@type": "Product", "name": product["nome"],
                      "description": product["descricao"],
                      "image": [settings.SITE_URL + image["url"] for image in product["images"]],
                      "url": settings.SITE_URL + request.path,
                      "offers": {"@type": "Offer", "priceCurrency": "BRL", "price": str(product["preco"]),
                                 "url": settings.SITE_URL + request.path}}
    return render(request, "loja/product_detail.html", {
        "product": product, "related_products": related[:4], "product_schema": structured,
        "meta_description": product["descricao"], "og_image": product["cover"],
    })


@never_cache
@require_safe
def cart(request):
    return render(request, "loja/cart.html", {**services.cart_summary(request.session), "noindex": True})


def _cart_response(request, message, status=200):
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"message": message, "cart_count": services.cart_count(request.session)}, status=status)
    if status != 200:
        return HttpResponseBadRequest(message)
    messages.success(request, message)
    destination = request.POST.get("next") or request.META.get("HTTP_REFERER", "")
    if not url_has_allowed_host_and_scheme(destination, {request.get_host()}, require_https=request.is_secure()):
        destination = reverse("loja:cart")
    return redirect(destination or reverse("loja:cart"))


@require_POST
def add_to_cart(request, id):
    product = services.get_product(id)
    if not product:
        raise Http404("Produto nao encontrado")
    try:
        services.add_to_cart(request.session, id)
    except ValueError as error:
        return _cart_response(request, str(error), status=400)
    return _cart_response(request, f"{product['nome']} adicionado ao carrinho.")


@require_POST
def remove_from_cart(request, id):
    if not services.get_product(id):
        raise Http404("Produto nao encontrado")
    services.remove_from_cart(request.session, id)
    return _cart_response(request, "Quantidade atualizada.")


@require_POST
def update_cart(request, id):
    if not services.get_product(id):
        raise Http404("Produto nao encontrado")
    try:
        quantity = int(request.POST.get("quantity", ""))
        services.set_quantity(request.session, id, quantity)
    except (ValueError, TypeError):
        return _cart_response(request, "Quantidade inv\u00e1lida. Use um n\u00famero entre 0 e 99.", status=400)
    return _cart_response(request, "Produto removido." if quantity == 0 else "Quantidade atualizada.")


@require_safe
def robots(request):
    content = "User-agent: *\nDisallow: /admin/\nDisallow: /carrinho/\n"
    if settings.SITE_URL:
        content += f"Sitemap: {settings.SITE_URL}/sitemap.xml\n"
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    patch_cache_control(response, public=True, max_age=3600)
    return response


@require_safe
def sitemap(request):
    paths = [reverse("loja:home"), reverse("loja:products")]
    paths += [reverse("loja:product_detail", args=[p["id"]]) for p in services.get_products()]
    response = render(request, "loja/sitemap.xml", {"locations": [settings.SITE_URL + path for path in paths]
                      if settings.SITE_URL else []}, content_type="application/xml")
    patch_cache_control(response, public=True, max_age=3600)
    return response
