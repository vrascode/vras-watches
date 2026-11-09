"""Compose domain routes under the existing public loja namespace."""
from loja.cart.urls import urlpatterns as cart_urls
from loja.catalog.urls import urlpatterns as catalog_urls
from loja.management_portal.urls import urlpatterns as management_urls
from loja.storefront.urls import urlpatterns as storefront_urls


app_name = "loja"
urlpatterns = management_urls + storefront_urls + catalog_urls + cart_urls
