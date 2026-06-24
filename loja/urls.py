from django.urls import path

from loja import views


app_name = "loja"

urlpatterns = [
    path("", views.home, name="home"),
    path("produtos/", views.products, name="products"),
    path("produto/<int:id>/", views.product_detail, name="product_detail"),
    path("carrinho/", views.cart, name="cart"),
    path("carrinho/adicionar/<int:id>/", views.add_to_cart, name="add_to_cart"),
    path("carrinho/remover/<int:id>/", views.remove_from_cart, name="remove_from_cart"),
]
