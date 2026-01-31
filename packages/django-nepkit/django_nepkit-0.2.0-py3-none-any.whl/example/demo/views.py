from django import forms
from django.shortcuts import render, redirect
from rest_framework import viewsets, filters as drf_filters
from django_filters import rest_framework as django_filters
from django_nepkit.filters import NepaliDateYearFilter, NepaliDateMonthFilter
from .models import Person, Citizen, AuditedPerson, Transaction
from .serializers import (
    PersonSerializer,
    CitizenSerializer,
    AuditedPersonSerializer,
    TransactionSerializer,
)
from django_nepkit.filters import (
    NepaliCurrencyRangeFilter,
    NepaliDateRangeFilter,
)
from django_nepkit.utils import normalize_address


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
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
        ]


def person_list(request):
    persons = Person.objects.all()
    transactions = Transaction.objects.all()
    return render(
        request,
        "demo/person_list.html",
        {"persons": persons, "transactions": transactions},
    )


def person_create(request):
    if request.method == "POST":
        form = PersonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("demo:person-list")
    else:
        form = PersonForm()
    return render(request, "demo/person_form.html", {"form": form})


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["title", "amount"]


def transaction_create(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("demo:person-list")
    else:
        form = TransactionForm()
    return render(
        request, "demo/person_form.html", {"form": form, "title": "Add Transaction"}
    )


# --- API Support (DRF) ---


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

    # Sort and Search work automatically with BS date strings
    filter_backends = [
        django_filters.DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]

    ordering_fields = ["birth_date", "created_at"]
    search_fields = ["name", "birth_date", "phone_number"]

    # Simple exact date filter
    filterset_fields = {
        "birth_date": ["exact"],
    }

    class PersonFilter(django_filters.FilterSet):
        year = NepaliDateYearFilter(field_name="birth_date")
        month = NepaliDateMonthFilter(field_name="birth_date")

        class Meta:
            model = Person
            fields = ["province", "district"]

    filterset_class = PersonFilter


class CitizenViewSet(viewsets.ModelViewSet):
    queryset = Citizen.objects.all()
    serializer_class = CitizenSerializer
    filter_backends = [drf_filters.OrderingFilter]
    ordering_fields = ["province", "district"]


class AuditedPersonViewSet(viewsets.ModelViewSet):
    queryset = AuditedPerson.objects.all()
    serializer_class = AuditedPersonSerializer
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ["name", "birth_date"]
    ordering_fields = ["created_at"]


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [django_filters.DjangoFilterBackend]

    class TransactionFilter(django_filters.FilterSet):
        amount_range = NepaliCurrencyRangeFilter(field_name="amount")
        date_range = NepaliDateRangeFilter(field_name="date")

        class Meta:
            model = Transaction
            fields = ["title", "amount", "date"]

    filterset_class = TransactionFilter


def address_normalize_demo(request):
    address = request.GET.get("address", "")
    result = None
    if address:
        result = normalize_address(address)

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "demo/address_normalize_partial.html", {"result": result}
        )

    return render(
        request, "demo/address_normalize.html", {"address": address, "result": result}
    )
