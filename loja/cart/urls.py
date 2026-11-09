from django.urls import path

from loja.cart import views


urlpatterns = [
    path("carrinho/", views.cart, name="cart"),
    path("carrinho/adicionar/<int:id>/", views.add_to_cart, name="add_to_cart"),
    path("carrinho/remover/<int:id>/", views.remove_from_cart, name="remove_from_cart"),
    path("carrinho/atualizar/<int:id>/", views.update_cart, name="update_cart"),
]
