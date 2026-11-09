"""Session cart endpoints with CSRF protection and safe return URLs."""
from django.contrib import messages
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_safe

from loja.cart import services as cart_services
from loja.catalog import services


@never_cache
@require_safe
def cart(request):
    return render(request, "loja/cart/cart.html", {**cart_services.cart_summary(request.session), "noindex": True})


def _cart_response(request, message, status=200):
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"message": message, "cart_count": cart_services.cart_count(request.session)}, status=status)
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
        cart_services.add_to_cart(request.session, id)
    except ValueError as error:
        return _cart_response(request, str(error), status=400)
    return _cart_response(request, f"{product['nome']} adicionado ao carrinho.")


@require_POST
def remove_from_cart(request, id):
    if not services.get_product(id):
        raise Http404("Produto nao encontrado")
    cart_services.remove_from_cart(request.session, id)
    return _cart_response(request, "Quantidade atualizada.")


@require_POST
def update_cart(request, id):
    if not services.get_product(id):
        raise Http404("Produto nao encontrado")
    try:
        quantity = int(request.POST.get("quantity", ""))
        cart_services.set_quantity(request.session, id, quantity)
    except (ValueError, TypeError):
        return _cart_response(request, "Quantidade inv\u00e1lida. Use um n\u00famero entre 0 e 99.", status=400)
    return _cart_response(request, "Produto removido." if quantity == 0 else "Quantidade atualizada.")
