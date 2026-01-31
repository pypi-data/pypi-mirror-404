from . import views
from rest_framework.routers import DefaultRouter
from django.urls import path

app_name = "demo"

router = DefaultRouter()
router.register("api/persons", views.PersonViewSet, basename="person-api")
router.register("api/citizens", views.CitizenViewSet, basename="citizen-api")
router.register("api/audited", views.AuditedPersonViewSet, basename="audited-api")
router.register(
    "api/transactions", views.TransactionViewSet, basename="transaction-api"
)

urlpatterns = [
    path("", views.person_list, name="person-list"),
    path("add/", views.person_create, name="person-create"),
    path("transactions/add/", views.transaction_create, name="transaction-create"),
    path("normalize/", views.address_normalize_demo, name="address-normalize"),
] + router.urls
