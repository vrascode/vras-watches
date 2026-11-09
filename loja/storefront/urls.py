from django.urls import path

from loja.storefront import views


urlpatterns = [
    path("", views.home, name="home"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
]
