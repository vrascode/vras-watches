import json

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def product_json_ld(value):
    # Escape HTML-significant characters before inserting serialized JSON in a script.
    payload = json.dumps(value, ensure_ascii=True).translate({ord("<"): "\\u003C", ord(">"): "\\u003E", ord("&"): "\\u0026"})
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(payload))
