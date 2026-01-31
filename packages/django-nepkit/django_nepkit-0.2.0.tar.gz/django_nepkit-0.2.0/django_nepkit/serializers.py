from __future__ import annotations

from typing import Any, Optional, Type

from nepali.datetime import nepalidate, nepalidatetime

try:
    from rest_framework import serializers
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "django-nepkit DRF support is optional. Install with `django-nepkit[drf]` "
        "to use `django_nepkit.serializers`."
    ) from e

from django_nepkit.conf import nepkit_settings
from django_nepkit.utils import (
    BS_DATE_FORMAT,
    BS_DATETIME_FORMAT,
    format_nepali_currency,
    try_parse_nepali_date,
    try_parse_nepali_datetime,
)


class BaseNepaliBSField(serializers.Field):
    """
    Handles Nepali (BS) dates.
    - Input: A date string (like '2080-01-01') or a date object.
    - Output: A formatted string for your API.
    """

    format: str = ""
    nepali_type: Type[object] = object

    default_error_messages = {
        "invalid": "Invalid Bikram Sambat value. Expected format: {format}.",
        "invalid_type": "Invalid type. Expected a string.",
    }

    def __init__(
        self,
        *,
        format: Optional[str] = None,
        ne: Optional[bool] = None,
        en: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            format: Optional `strftime` format used for representation.
                    If not provided, uses the class default.
            ne: If True, output in Devanagari script. If None, uses DEFAULT_LANGUAGE.
            en: If True, output in English. If None, derived from ne.
        """
        if format is not None:
            self.format = format

        default_lang = nepkit_settings.DEFAULT_LANGUAGE

        if ne is None:
            self.ne = default_lang == "ne"
        else:
            self.ne = ne

        if en is None:
            self.en = not self.ne
        else:
            self.en = en

        super().__init__(**kwargs)

    def _parse(self, value: str):
        if self.nepali_type is nepalidate:
            return try_parse_nepali_date(value)
        if self.nepali_type is nepalidatetime:
            return try_parse_nepali_datetime(value)
        return None

    def _format_value(self, value: Any) -> str:
        """Format value using strftime or strftime_ne (Devanagari) based on self.ne."""
        if self.ne and hasattr(value, "strftime_ne"):
            return value.strftime_ne(self.format)  # type: ignore[attr-defined]
        return value.strftime(self.format)  # type: ignore[attr-defined]

    def to_representation(self, value: Any) -> Optional[str]:
        if value is None:
            return None

        if isinstance(value, self.nepali_type):
            return self._format_value(value)

        # Convert string dates to Nepali date objects
        if isinstance(value, str):
            parsed = self._parse(value)
            if parsed is not None:
                return self._format_value(parsed)

        return str(value)

    def to_internal_value(self, data: Any):
        if data in (None, ""):
            return None

        if isinstance(data, self.nepali_type):
            return data

        if not isinstance(data, str):
            self.fail("invalid_type")

        parsed = self._parse(data)
        if parsed is not None:
            return parsed

        self.fail("invalid", format=self.format)


class NepaliDateSerializerField(BaseNepaliBSField):
    """API field for Nepali Dates."""

    format = BS_DATE_FORMAT
    nepali_type = nepalidate


class NepaliDateTimeSerializerField(BaseNepaliBSField):
    """API field for Nepali Date and Time."""

    format = BS_DATETIME_FORMAT
    nepali_type = nepalidatetime


class NepaliCurrencySerializerField(serializers.Field):
    """
    API field for Nepali Currency.
    Formats decimal values with Nepali-style commas.
    """

    def __init__(self, currency_symbol="Rs.", ne=None, **kwargs):
        self.currency_symbol = currency_symbol
        self.ne = ne
        super().__init__(**kwargs)

    def to_representation(self, value):
        if value is None:
            return None

        ne = self.ne
        if ne is None:
            ne = self.context.get("ne", nepkit_settings.DEFAULT_LANGUAGE == "ne")

        return format_nepali_currency(
            value, currency_symbol=self.currency_symbol, ne=ne
        )

    def to_internal_value(self, data):
        # We don't support converting back from formatted string to decimal here
        # Users should send raw decimal/float values for input.
        return data


class NepaliLocalizedSerializerMixin:
    """
    A mixin for ModelSerializer that automatically adds localized counterparts
    for eligible fields if `ne=True` is passed in the context.
    Eligible fields: NepaliDateField, NepaliDateTimeField, NepaliCurrencyField.

    Usage:
        class MySerializer(NepaliLocalizedSerializerMixin, serializers.ModelSerializer):
            ...
    """

    def to_representation(self, instance):
        ret = super().to_representation(instance)  # type: ignore[misc]
        ne = self.context.get("ne", False)
        if not ne:
            return ret

        from django_nepkit.models import (
            NepaliCurrencyField,
            NepaliDateField,
            NepaliDateTimeField,
        )

        model = getattr(self.Meta, "model", None)  # type: ignore[attr-defined]
        if not model:
            return ret

        for field_name, value in list(ret.items()):
            try:
                model_field = model._meta.get_field(field_name)
                localized_name = f"{field_name}_ne"

                if localized_name in ret:
                    continue

                if isinstance(model_field, NepaliDateField):
                    raw_val = getattr(instance, field_name)
                    if hasattr(raw_val, "strftime_ne"):
                        ret[localized_name] = raw_val.strftime_ne(BS_DATE_FORMAT)

                elif isinstance(model_field, NepaliDateTimeField):
                    raw_val = getattr(instance, field_name)
                    if hasattr(raw_val, "strftime_ne"):
                        ret[localized_name] = raw_val.strftime_ne(BS_DATETIME_FORMAT)

                elif isinstance(model_field, NepaliCurrencyField):
                    ret[localized_name] = format_nepali_currency(
                        value, currency_symbol="", ne=True
                    )
            except Exception:
                continue

        return ret
