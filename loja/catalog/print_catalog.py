"""Print and HTML export share the same current VRAS offers and photo selection."""
from django.http import Http404

from loja.catalog.presentation import model_groups, model_slug, present_product


def catalog_context(model=""):
    groups = model_groups()
    if model:
        groups = {name: items for name, items in groups.items() if name.casefold() == model.casefold()}
        if not groups:
            raise Http404("Modelo não encontrado.")
    sections = [{"name": name, "slug": model_slug(name),
                 "variants": [present_product(product, products) for product in products]}
                for name, products in groups.items()]
    return {"catalog_sections": sections, "catalog_model": model,
            "model_count": len(sections), "color_count": sum(len(s["variants"]) for s in sections)}
