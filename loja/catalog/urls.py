from django.urls import path

from loja.catalog import views, showcase_views


urlpatterns = [
    path("catalogos/poedagar/", showcase_views.printable_catalog, name="poedagar_catalog"),
    path("colecao/<slug:slug>/", showcase_views.collection_model, name="collection_model"),
    path("produtos/", views.products, name="products"),
    path("produto/<int:id>/", views.product_detail, name="product_detail"),
]
