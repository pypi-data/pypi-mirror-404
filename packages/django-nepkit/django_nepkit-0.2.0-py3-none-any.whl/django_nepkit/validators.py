from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from nepali import phone_number


# Check if a phone number is valid in Nepal
def validate_nepali_phone_number(value):
    if not phone_number.is_valid(value):
        raise ValidationError(
            _("%(value)s is not a valid nepali phone number"),
            params={"value": value},
        )
