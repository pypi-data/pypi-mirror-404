from datetime import date as python_date

from django import forms
from django.utils.translation import gettext_lazy as _
from nepali.datetime import nepalidate

from django_nepkit.utils import try_parse_nepali_date
from django_nepkit.validators import validate_nepali_phone_number
from django_nepkit.widgets import NepaliDatePickerWidget


class NepaliDateFormField(forms.DateField):
    """A form field for entering Nepali dates."""

    widget = NepaliDatePickerWidget

    def __init__(self, *args, **kwargs):
        kwargs.pop("max_length", None)
        # Clean up arguments not needed for base Field
        kwargs.pop("empty_value", None)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, nepalidate):
            return value
        if isinstance(value, python_date):
            return nepalidate.from_date(value)
        try:
            parsed = try_parse_nepali_date(str(value))
            if parsed is not None:
                return parsed
            raise ValueError("Invalid BS date format")
        except Exception:
            from django_nepkit.utils import BS_DATE_FORMAT

            raise forms.ValidationError(
                _("Enter a valid Nepali date in %(format)s format.")
                % {"format": BS_DATE_FORMAT},
                code="invalid",
            )


class NepaliPhoneNumberFormField(forms.CharField):
    """A form field for entering Nepali phone numbers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.append(validate_nepali_phone_number)
