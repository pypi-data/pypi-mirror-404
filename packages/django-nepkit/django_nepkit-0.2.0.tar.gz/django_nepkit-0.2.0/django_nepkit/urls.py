from django.urls import path

from django_nepkit.views import district_list_view, municipality_list_view

app_name = "django_nepkit"

urlpatterns = [
    path("districts/", district_list_view, name="district-list"),
    path("municipalities/", municipality_list_view, name="municipality-list"),
]
