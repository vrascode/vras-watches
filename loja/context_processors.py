from urllib.parse import urlsplit

from django.conf import settings

from loja import media, services


def storefront(request):
    manifest = media.load_media()
    policies = []
    for label, url in manifest.get("policies", {}).items():
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.netloc and not parsed.username:
            policies.append({"label": label, "url": url})
    return {"cart_count": services.cart_count(request.session),
            "brand_logo": media.local_asset(manifest.get("brand", {}).get("logo")),
            "policies": policies, "site_url": settings.SITE_URL,
            "instagram_url": "https://www.instagram.com/usevras/",
            "canonical_url": settings.SITE_URL + request.path if settings.SITE_URL else ""}
