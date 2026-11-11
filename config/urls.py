from django.contrib import admin
from django.urls import include, path
from loja.management_portal.reference_admin import reference_dashboard, reference_csv


urlpatterns = [
    path("admin/catalogo-referencia/", admin.site.admin_view(reference_dashboard), name="reference_admin"),
    path("admin/catalogo-referencia/inventario.csv", admin.site.admin_view(reference_csv), name="reference_inventory_csv"),
    path("admin/", admin.site.urls),
    path("", include("loja.urls")),
]
