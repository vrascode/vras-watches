from django.urls import path

from loja.catalog import views


urlpatterns = [
    path("produtos/", views.products, name="products"),
    path("produto/<int:id>/", views.product_detail, name="product_detail"),
]
