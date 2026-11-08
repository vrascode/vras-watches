"""Authenticated owner workspace; public catalog never exposes drafts."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import CommandError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from loja import services
from loja.catalog_forms import CatalogReceiptForm
from loja.catalog_receipts import ISSUE_LABELS, catalog_version, receive_product


def owner_products():
    products = services.get_products(include_drafts=True)
    for product in products:
        product["pending_labels"] = [ISSUE_LABELS.get(issue, issue) for issue in product["publication_issues"]
                                     if issue != "produto_em_rascunho"]
    return products


@staff_member_required(login_url="loja:catalog_login")
@never_cache
@require_safe
def catalog_manager(request):
    products = owner_products()
    return render(request, "loja/manager/dashboard.html", {
        "products": products, "published_count": sum(p["can_purchase"] for p in products),
    })


@staff_member_required(login_url="loja:catalog_login")
@never_cache
@require_http_methods(["GET", "POST"])
def catalog_product(request, id):
    product = next((p for p in owner_products() if p["id"] == id), None)
    if not product:
        raise Http404("Produto não encontrado")
    variant = product.get("variante") or {}
    initial = {"catalog_version": catalog_version(), "referencia": product.get("referencia"),
               "fonte": (product.get("identificacao") or {}).get("fonte", ""),
               "identidade_confirmada": bool(product["verified_identity"]),
               "variante": variant.get("source_variant_id"),
               **{key: variant.get(key, "") for key in ("cor_caixa", "cor_mostrador", "cor_pulseira", "tipo_pulseira")},
               "variante_confirmada": bool(product["verified_variant"]),
               "oferta_confirmada": product.get("oferta_confirmada") is True,
               "registro_oferta": (product.get("confirmacao_oferta") or {}).get("registro", ""),
               "acao_galeria": "append"}
    form = CatalogReceiptForm(request.POST if request.method == "POST" else None,
                              request.FILES if request.method == "POST" else None, initial=initial, product=product)
    if request.method == "POST" and form.is_valid():
        try:
            result = receive_product(id, form.cleaned_data, actor=request.user.get_username())
        except (ValueError, OSError, CommandError) as error:
            form.add_error(None, f"Envio não concluído: {error}")
        else:
            product = next(p for p in services.get_products(include_drafts=True) if p["id"] == id)
            if product["can_purchase"]:
                messages.success(request, f"{product['nome']} publicado e disponível para compra. {result['imported']} fotos importadas.")
            else:
                messages.info(request, f"Dados salvos e {result['imported']} fotos importadas. O produto continua em rascunho; confira os requisitos abaixo.")
            return redirect("loja:catalog_product", id=id)
    return render(request, "loja/manager/product.html", {"product": product, "form": form})
