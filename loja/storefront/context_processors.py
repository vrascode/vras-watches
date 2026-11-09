from urllib.parse import urlsplit

from django.conf import settings

from loja.cart import services as cart_services
from loja.media import assets as media


def storefront(request):
    manifest = media.load_media()
    policies = []
    for label, url in manifest.get("policies", {}).items():
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.netloc and not parsed.username:
            policies.append({"label": label, "url": url})
    count = cart_services.cart_count(request.session)
    return {"cart_count": count,
            "cart_catalog_notice": request.session.pop(cart_services.CART_NOTICE_KEY, False),
            "brand_logo": media.local_asset(manifest.get("brand", {}).get("logo")),
            "policies": policies, "site_url": settings.SITE_URL,
            "instagram_url": "https://www.instagram.com/usevras/",
            "canonical_url": settings.SITE_URL + request.path if settings.SITE_URL else ""}
