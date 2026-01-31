from datetime import date as python_date
from datetime import datetime as python_datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from nepali.datetime import nepalidate, nepalidatetime
from nepali.locations import districts, municipalities, provinces

from django_nepkit.forms import NepaliDateFormField
from django_nepkit.utils import (
    BS_DATE_FORMAT,
    BS_DATETIME_FORMAT,
    try_parse_nepali_date,
    try_parse_nepali_datetime,
)
from django_nepkit.validators import validate_nepali_phone_number
from django_nepkit.widgets import (
    DistrictSelectWidget,
    MunicipalitySelectWidget,
    NepaliDatePickerWidget,
    ProvinceSelectWidget,
)
from django_nepkit.conf import nepkit_settings


class NepaliFieldMixin:
    """Adds Nepali 'ne' and 'en' support to any field."""

    def __init__(self, *args, **kwargs):
        default_lang = nepkit_settings.DEFAULT_LANGUAGE
        self.ne = kwargs.pop("ne", default_lang == "ne")

        explicit_en = "en" in kwargs
        en_value = kwargs.pop("en", not self.ne)

        if self.ne and not explicit_en:
            self.en = False
        else:
            self.en = en_value

        self.htmx = kwargs.pop("htmx", False)

        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.ne:
            kwargs["ne"] = True
        if not self.en:
            kwargs["en"] = False
        if self.htmx:
            kwargs["htmx"] = True
        return name, path, args, kwargs


class NepaliPhoneNumberField(models.CharField):
    description = _("Nepali Phone Number")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 10)
        super().__init__(*args, **kwargs)
        self.validators.append(validate_nepali_phone_number)


class BaseNepaliBSField(NepaliFieldMixin, models.CharField):
    """Base class for Nepali date and datetime fields."""

    def __init__(self, *args, **kwargs):
        self.auto_now = kwargs.pop("auto_now", False)
        self.auto_now_add = kwargs.pop("auto_now_add", False)

        if self.auto_now or self.auto_now_add:
            kwargs.setdefault("editable", False)
            kwargs.setdefault("blank", True)

        kwargs.setdefault("max_length", getattr(self, "default_max_length", 20))
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            now = timezone.now()
            if timezone.is_aware(now):
                now = timezone.localtime(now)

            nepali_cls = getattr(self, "nepali_cls", nepalidate)
            format_str = getattr(self, "format_str", BS_DATE_FORMAT)

            value = (
                nepali_cls.from_date(now).strftime(format_str)
                if nepali_cls == nepalidate
                else nepali_cls.from_datetime(now).strftime(format_str)
            )
            setattr(model_instance, self.attname, value)
            return value
        return super().pre_save(model_instance, add)

    def from_db_value(self, value, expression, connection):
        parsed = self.parse_func(value)
        return parsed if parsed is not None else value

    def to_python(self, value):
        if value is None or isinstance(value, self.nepali_cls):
            return value
        if isinstance(value, (python_date, python_datetime)):
            try:
                if isinstance(value, python_datetime) and timezone.is_aware(value):
                    value = timezone.localtime(value)
                return (
                    self.nepali_cls.from_date(value)
                    if self.nepali_cls == nepalidate
                    else self.nepali_cls.from_datetime(value)
                )
            except (ValueError, TypeError):
                return str(value)
        if isinstance(value, str):
            parsed = self.parse_func(value)
            return parsed if parsed is not None else value
        return super().to_python(value)

    def _get_string_value(self, value):
        if isinstance(value, (nepalidate, nepalidatetime)):
            return value.strftime(self.format_str)
        return value

    def validate(self, value, model_instance):
        super().validate(self._get_string_value(value), model_instance)

    def run_validators(self, value):
        super().run_validators(self._get_string_value(value))

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, self.nepali_cls):
            return value.strftime(self.format_str)
        if isinstance(value, (python_date, python_datetime)):
            try:
                if isinstance(value, python_datetime) and timezone.is_aware(value):
                    value = timezone.localtime(value)
                nepali_obj = (
                    self.nepali_cls.from_date(value)
                    if self.nepali_cls == nepalidate
                    else self.nepali_cls.from_datetime(value)
                )
                return nepali_obj.strftime(self.format_str)
            except (ValueError, TypeError):
                return str(value)
        return str(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.auto_now:
            kwargs["auto_now"] = True
        if self.auto_now_add:
            kwargs["auto_now_add"] = True
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {
            "widget": NepaliDatePickerWidget(ne=self.ne, en=self.en),
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class NepaliDateField(BaseNepaliBSField):
    description = _("Nepali Date (Bikram Sambat)")
    default_max_length = 10
    nepali_cls = nepalidate
    format_str = BS_DATE_FORMAT
    parse_func = staticmethod(try_parse_nepali_date)

    def formfield(self, **kwargs):
        kwargs.setdefault("form_class", NepaliDateFormField)
        return super().formfield(**kwargs)


class NepaliTimeField(NepaliFieldMixin, models.TimeField):
    description = _("Nepali Time")


class NepaliDateTimeField(BaseNepaliBSField):
    description = _("Nepali DateTime (Bikram Sambat)")
    default_max_length = 19
    nepali_cls = nepalidatetime
    format_str = BS_DATETIME_FORMAT
    parse_func = staticmethod(try_parse_nepali_datetime)


class BaseLocationField(NepaliFieldMixin, models.CharField):
    """Base class for Province, District, and Municipality fields."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 100)

        default_lang = nepkit_settings.DEFAULT_LANGUAGE
        ne = kwargs.get("ne", default_lang == "ne")

        # Load choices from the library (provinces, districts, etc.)
        kwargs.setdefault("choices", self.get_choices_from_source(ne))
        super().__init__(*args, **kwargs)

    def get_choices_from_source(self, ne):
        source = getattr(self, "source", [])
        return [(self._get_name(item, ne), self._get_name(item, ne)) for item in source]

    def _get_name(self, item, ne):
        name = getattr(item, "name_nepali", item.name) if ne else item.name
        # Handle name variations and Koshi Province mapping
        if name == "Province 1":
            return "Koshi Province"
        if name == "प्रदेश नं. १":
            return "कोशी प्रदेश"
        return name

    def formfield(self, **kwargs):
        widget_cls = getattr(self, "widget_class", None)
        if widget_cls:
            defaults = {"widget": widget_cls(ne=self.ne, en=self.en, htmx=self.htmx)}
            defaults.update(kwargs)
            return super(models.CharField, self).formfield(**defaults)
        return super().formfield(**kwargs)


class ProvinceField(BaseLocationField):
    description = _("Nepali Province")
    source = provinces
    widget_class = ProvinceSelectWidget


class DistrictField(BaseLocationField):
    description = _("Nepali District")
    source = districts
    widget_class = DistrictSelectWidget


class MunicipalityField(BaseLocationField):
    description = _("Nepali Municipality")
    source = municipalities
    widget_class = MunicipalitySelectWidget


class NepaliCurrencyField(models.DecimalField):
    description = _("Nepali Currency")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_digits", 19)
        kwargs.setdefault("decimal_places", 2)
        super().__init__(*args, **kwargs)
