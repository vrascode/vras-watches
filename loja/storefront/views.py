"""Storefront landing page and search-engine endpoints."""
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import patch_cache_control
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from loja.catalog import services
from loja.media import assets as media


@require_safe
@never_cache
def home(request):
    manifest = media.load_media()
    catalog = services.get_products()
    return render(request, "loja/storefront/home.html", {
        "catalog_pending": not catalog,
        "featured_products": services.get_featured_products(catalog) or catalog[:4],
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
    response = render(request, "loja/storefront/sitemap.xml", {"locations": [settings.SITE_URL + path for path in paths]
                      if settings.SITE_URL else []}, content_type="application/xml")
    patch_cache_control(response, public=True, max_age=3600)
    return response
