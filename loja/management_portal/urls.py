from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import path

from loja.management_portal import views


urlpatterns = [
    path("gestao/entrar/", LoginView.as_view(template_name="loja/management_portal/login.html",
                                          authentication_form=AdminAuthenticationForm), name="catalog_login"),
    path("gestao/catalogo/", views.catalog_manager, name="catalog_manager"),
    path("gestao/catalogo/<int:id>/", views.catalog_product, name="catalog_product"),
]
