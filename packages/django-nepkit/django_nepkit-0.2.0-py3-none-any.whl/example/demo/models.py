from django.db import models
from django_nepkit import (
    NepaliDateField,
    NepaliTimeField,
    NepaliPhoneNumberField,
    NepaliDateTimeField,
    ProvinceField,
    DistrictField,
    MunicipalityField,
    NepaliCurrencyField,
)


class Person(models.Model):
    name = models.CharField(max_length=100)
    # Dates and times
    birth_date = NepaliDateField()  # English by default
    birth_date_ne = NepaliDateField(ne=True, blank=True, null=True)  # Using Devanagari
    registration_time = NepaliTimeField(auto_now_add=True)  # English digits by default
    phone_number = NepaliPhoneNumberField()

    # Location fields
    province = ProvinceField()  # English names by default
    province_ne = ProvinceField(ne=True, blank=True, null=True)  # In Devanagari
    district = DistrictField()
    district_ne = DistrictField(ne=True, blank=True, null=True)
    municipality = MunicipalityField()
    municipality_ne = MunicipalityField(ne=True, blank=True, null=True)

    created_at = NepaliDateTimeField(auto_now_add=True)
    updated_at = NepaliDateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Citizen(models.Model):
    name = models.CharField(max_length=100)

    # Chaining works automatically
    province = ProvinceField()
    district = DistrictField()
    municipality = MunicipalityField()

    def __str__(self):
        return self.name


class AuditedPerson(models.Model):
    name = models.CharField(max_length=100)
    birth_date = NepaliDateField()
    created_at = NepaliDateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    title = models.CharField(max_length=100)
    amount = NepaliCurrencyField()
    date = NepaliDateField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"
