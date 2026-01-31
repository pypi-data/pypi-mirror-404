from django.contrib import admin

from django_nepkit import (
    NepaliModelAdmin,
    NepaliAdminMixin,
    NepaliDateFilter,
    NepaliMonthFilter,
)

from .models import Person, Citizen, AuditedPerson, Transaction


# Example 1: Basic setup
@admin.register(Person)
class PersonAdmin(NepaliModelAdmin):
    list_display = (
        "name",
        "birth_date",
        "birth_date_ne",
        "phone_number",
        "province",
        "province_ne",
        "district",
        "district_ne",
        "municipality",
        "municipality_ne",
        "created_at",
        "updated_at",
    )
    # Added Year and Month filters
    list_filter = (
        ("birth_date", NepaliDateFilter),
        ("birth_date", NepaliMonthFilter),
        "province",
    )
    search_fields = ("name", "phone_number")


# Example 2: Using a Mixin
class BaseAuditAdmin(admin.ModelAdmin):
    """A fake base class for testing."""

    pass


# Use the Mixin if you already have a base Admin class
@admin.register(AuditedPerson)
class CustomPersonAdmin(NepaliAdminMixin, BaseAuditAdmin):
    list_display = ("name", "birth_date", "created_at")
    list_filter = (
        ("created_at", NepaliMonthFilter),  # Filter by Nepali Month
    )


# Example 3: HTMX support
@admin.register(Citizen)
class CitizenAdmin(NepaliModelAdmin):
    list_display = ("name", "province", "district", "municipality")
    # Filters still work with HTMX
    list_filter = ("province", "district")


@admin.register(Transaction)
class TransactionAdmin(NepaliModelAdmin):
    list_display = ("title", "amount", "date")
    list_filter = (("date", NepaliDateFilter),)
