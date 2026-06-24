from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from loja import services


def _common_context(request):
    return {
        "cart_count": services.cart_count(request.session),
    }


def home(request):
    context = _common_context(request)
    context["featured_products"] = services.get_featured_products()
    return render(request, "loja/home.html", context)


def products(request):
    category = request.GET.get("categoria", "").strip()
    query = request.GET.get("q", "").strip()
    products_list = services.filter_products(category=category, query=query)

    context = _common_context(request)
    context.update({
        "products": products_list,
        "categories": services.get_categories(),
        "selected_category": category,
        "search_query": query,
        "product_count": len(products_list),
    })
    return render(request, "loja/products.html", context)


def product_detail(request, id):
    product = services.get_product(id)
    if not product:
        raise Http404("Produto nao encontrado")

    context = _common_context(request)
    context["product"] = product
    return render(request, "loja/product_detail.html", context)


def cart(request):
    context = _common_context(request)
    summary = services.cart_summary(request.session)
    context.update({
        "items": summary["items"],
        "cart_quantity": summary["quantity"],
        "total": summary["total"],
        "total_brl": summary["total_brl"],
    })
    return render(request, "loja/cart.html", context)


@require_POST
def add_to_cart(request, id):
    product = services.get_product(id)
    if not product:
        raise Http404("Produto nao encontrado")

    services.add_to_cart(request.session, id)
    messages.success(request, f"{product['nome']} foi adicionado ao carrinho.")
    return redirect(request.META.get("HTTP_REFERER") or reverse("loja:cart"))


@require_POST
def remove_from_cart(request, id):
    product = services.get_product(id)
    services.remove_from_cart(request.session, id)
    if product:
        messages.success(request, f"{product['nome']} foi removido do carrinho.")
    return redirect(request.META.get("HTTP_REFERER") or reverse("loja:cart"))
