from django.urls import path
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.views import LoginView

from loja import catalog_views, views


app_name = "loja"

urlpatterns = [
    path("gestao/entrar/", LoginView.as_view(template_name="loja/manager/login.html",
                                          authentication_form=AdminAuthenticationForm), name="catalog_login"),
    path("gestao/catalogo/", catalog_views.catalog_manager, name="catalog_manager"),
    path("gestao/catalogo/<int:id>/", catalog_views.catalog_product, name="catalog_product"),
    path("", views.home, name="home"),
    path("produtos/", views.products, name="products"),
    path("produto/<int:id>/", views.product_detail, name="product_detail"),
    path("carrinho/", views.cart, name="cart"),
    path("carrinho/adicionar/<int:id>/", views.add_to_cart, name="add_to_cart"),
    path("carrinho/remover/<int:id>/", views.remove_from_cart, name="remove_from_cart"),
    path("carrinho/atualizar/<int:id>/", views.update_cart, name="update_cart"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
]
