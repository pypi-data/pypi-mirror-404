from rest_framework import serializers
from django_nepkit.serializers import (
    NepaliDateSerializerField,
    NepaliCurrencySerializerField,
    NepaliLocalizedSerializerMixin,
)
from .models import Person, Citizen, AuditedPerson, Transaction


class PersonSerializer(NepaliLocalizedSerializerMixin, serializers.ModelSerializer):
    birth_date = NepaliDateSerializerField()

    class Meta:
        model = Person
        fields = "__all__"


class TransactionSerializer(
    NepaliLocalizedSerializerMixin, serializers.ModelSerializer
):
    amount_formatted = NepaliCurrencySerializerField(source="amount")

    class Meta:
        model = Transaction
        fields = ["id", "title", "amount", "amount_formatted", "date"]


class CitizenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Citizen
        fields = "__all__"


class AuditedPersonSerializer(serializers.ModelSerializer):
    birth_date = NepaliDateSerializerField()

    class Meta:
        model = AuditedPerson
        fields = "__all__"
