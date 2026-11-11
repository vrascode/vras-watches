"""Bounded public HTTPS downloads. Never supplies credentials or bypasses gates."""
import ipaddress
import socket
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


HOSTS = {"poedagareco.com", "cdn.shopify.com"}
LIMIT = 120 * 1024 * 1024


def validate_public_url(url, *, resolve=True):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.port not in {None, 443}
            or parsed.username or parsed.password or parsed.fragment):
        raise ValueError("URL fora das origens HTTPS públicas permitidas.")
    if resolve:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            raise ValueError("A origem não resolve para um endereço público.")
    return url


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def download(url, *, limit=LIMIT):
    validate_public_url(url)
    request = Request(url, headers={"User-Agent": "VRAS-Catalog/1.0 (public product catalog import)"})
    with build_opener(PublicRedirects).open(request, timeout=30) as response:
        validate_public_url(response.url)
        if int(response.headers.get("Content-Length", 0)) > limit:
            raise ValueError("Arquivo excede o limite permitido.")
        content = response.read(limit + 1)
        if len(content) > limit:
            raise ValueError("Arquivo excede o limite permitido.")
        mime = response.headers.get_content_type()
        if mime == "text/html" and "/cdn/" in url:
            raise ValueError("A origem retornou HTML em lugar da mídia.")
        return content, mime
