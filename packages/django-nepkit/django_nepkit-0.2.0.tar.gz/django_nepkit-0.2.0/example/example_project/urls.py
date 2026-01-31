from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("nepkit/", include("django_nepkit.urls")),
    path("", include("demo.urls")),
]
