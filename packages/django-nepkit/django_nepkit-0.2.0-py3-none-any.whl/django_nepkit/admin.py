from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from nepali.datetime import nepalidate, nepalidatetime

from django_nepkit.conf import nepkit_settings
from django_nepkit.models import (
    NepaliDateField,
    NepaliDateTimeField,
    NepaliCurrencyField,
)
from django_nepkit.utils import (
    try_parse_nepali_date,
    try_parse_nepali_datetime,
    format_nepali_currency,
)
from django_nepkit.utils import BS_DATE_FORMAT


def _format_nepali_common(value, try_parse_func, format_string, ne, cls_type):
    """Helper to format dates/times with optional Devanagari support."""
    if value is None:
        return ""

    try:
        parsed = try_parse_func(value)
        if parsed is not None:
            if ne and hasattr(parsed, "strftime_ne"):
                return parsed.strftime_ne(format_string)
            return parsed.strftime(format_string)
        if isinstance(value, cls_type):
            if ne and hasattr(value, "strftime_ne"):
                return value.strftime_ne(format_string)
            return value.strftime(format_string)
    except (ValueError, TypeError, AttributeError):
        pass

    return str(value) if value else ""


def format_nepali_date(date_value, format_string="%B %d, %Y", ne=False):
    """
    Format a nepalidate object with Nepali month names.
    """
    return _format_nepali_common(
        date_value, try_parse_nepali_date, format_string, ne, nepalidate
    )


def format_nepali_datetime(datetime_value, format_string=None, ne=False):
    """
    Format a nepalidatetime object with Nepali month names.
    """
    if format_string is None:
        if nepkit_settings.TIME_FORMAT == 24:
            format_string = "%B %d, %Y %H:%M"
        else:
            format_string = "%B %d, %Y %I:%M %p"

    return _format_nepali_common(
        datetime_value, try_parse_nepali_datetime, format_string, ne, nepalidatetime
    )


class BaseNepaliDateFilter(admin.FieldListFilter):
    """Base class for date filters (Year/Month)."""

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.parameter_name = f"{field_path}_{self.suffix}"
        super().__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, changelist):
        yield {
            "selected": self.used_parameters.get(self.parameter_name) is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": _("All"),
        }
        for value, display in self.get_filter_options():
            yield {
                "selected": self.used_parameters.get(self.parameter_name) == str(value),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: str(value)}
                ),
                "display": display,
            }

    def queryset(self, request, queryset):
        value = self.used_parameters.get(self.parameter_name)
        if value:
            return self.apply_filter(queryset, value)
        return queryset

    def get_filter_options(self):
        raise NotImplementedError

    def apply_filter(self, queryset, value):
        raise NotImplementedError


class NepaliDateFilter(BaseNepaliDateFilter):
    """Filter by Nepali Year (e.g., 2080)."""

    suffix = "bs_year"
    title = _("Nepali Date (Year)")

    def get_filter_options(self):
        current_year = nepalidate.today().year
        return [(y, str(y)) for y in range(current_year - 10, current_year + 2)]

    def apply_filter(self, queryset, value):
        if BS_DATE_FORMAT.startswith("%Y"):
            separator = BS_DATE_FORMAT[2] if len(BS_DATE_FORMAT) > 2 else "-"
            return queryset.filter(
                **{f"{self.field_path}__startswith": f"{value}{separator}"}
            )

        return queryset.filter(**{f"{self.field_path}__icontains": f"{value}"})


class NepaliMonthFilter(BaseNepaliDateFilter):
    """Filter by Nepali Month (e.g., Baisakh)."""

    suffix = "bs_month"
    title = _("Nepali Date (Month)")

    def get_filter_options(self):
        ne = nepkit_settings.DEFAULT_LANGUAGE == "ne"
        names = [
            ("बैशाख", "Baisakh"),
            ("जेठ", "Jestha"),
            ("असार", "Ashad"),
            ("साउन", "Shrawan"),
            ("भदौ", "Bhadra"),
            ("असोज", "Ashwin"),
            ("कात्तिक", "Kartik"),
            ("मंसिर", "Mangsir"),
            ("पुष", "Poush"),
            ("माघ", "Magh"),
            ("फागुन", "Falgun"),
            ("चैत", "Chaitra"),
        ]
        return [(f"{i:02d}", n[0] if ne else n[1]) for i, n in enumerate(names, 1)]

    def apply_filter(self, queryset, value):
        from django_nepkit.utils import BS_DATE_FORMAT

        if BS_DATE_FORMAT == "%Y-%m-%d":
            return queryset.filter(**{f"{self.field_path}__contains": f"-{value}-"})

        separator = BS_DATE_FORMAT[2] if len(BS_DATE_FORMAT) > 2 else "-"
        return queryset.filter(
            **{f"{self.field_path}__contains": f"{separator}{value}{separator}"}
        )


# Standard filter for any NepaliDateField in Admin
admin.FieldListFilter.register(
    lambda f: isinstance(f, NepaliDateField),
    NepaliDateFilter,
    take_priority=True,
)


class NepaliAdminMixin:
    """Provides date formatting tools for Admin classes."""

    def _get_field_ne_setting(self, field_name):
        """
        Get the 'ne' setting from a model field.

        Args:
            field_name: Name of the field in the model

        Returns:
            True if field has ne=True, False otherwise
        """
        if not hasattr(self, "model"):
            return False

        try:
            field = self.model._meta.get_field(field_name)
            if hasattr(field, "ne"):
                return field.ne
        except (AttributeError, LookupError):
            pass

        return False

    def format_nepali_date(
        self, date_value, format_string="%B %d, %Y", ne=None, field_name=None
    ):
        """
        Format a nepalidate object with Nepali month names.
        Available as a method on admin classes using this mixin.

        Args:
            date_value: A nepalidate object or string
            format_string: strftime format string
            ne: If True, format using Devanagari script. If None, auto-detect from field or global settings (default: None)
            field_name: Name of the field to auto-detect 'ne' setting from (optional)
        """
        if ne is None and field_name:
            ne = self._get_field_ne_setting(field_name)
        elif ne is None:
            ne = nepkit_settings.DEFAULT_LANGUAGE == "ne"

        return format_nepali_date(date_value, format_string, ne=ne)

    def format_nepali_datetime(
        self,
        datetime_value,
        format_string=None,
        ne=None,
        field_name=None,
    ):
        """
        Format a nepalidatetime object with Nepali month names.

        Args:
            datetime_value: A nepalidatetime object or string
            format_string: strftime format string
            ne: If True, format using Devanagari script. If None, auto-detect from field or global settings (default: None)
            field_name: Name of the field to auto-detect 'ne' setting from (optional)
        """
        if ne is None and field_name:
            ne = self._get_field_ne_setting(field_name)
        elif ne is None:
            ne = nepkit_settings.DEFAULT_LANGUAGE == "ne"

        return format_nepali_datetime(datetime_value, format_string, ne=ne)

    def format_nepali_currency(self, value, currency_symbol="Rs.", ne=False, **kwargs):
        """
        Format a number with Nepali-style commas.
        Available as a method on admin classes using this mixin.
        """
        return format_nepali_currency(value, currency_symbol=currency_symbol, ne=ne)


class NepaliModelAdmin(NepaliAdminMixin, admin.ModelAdmin):
    """
    Standard Admin class that automatically formats Nepali dates in lists.

    Example:
        from django_nepkit import NepaliModelAdmin, NepaliDateFilter

        @admin.register(MyModel)
        class MyModelAdmin(NepaliModelAdmin):
            list_display = ("name", "birth_date", "created_at")  # auto-formatted
            list_filter = (("birth_date", NepaliDateFilter),)
    """

    # Make filters available as class attributes
    NepaliDateFilter = NepaliDateFilter
    NepaliMonthFilter = NepaliMonthFilter

    def _make_nepali_display(self, field_name, formatter_method):
        """Helper to create display columns for Nepali dates."""
        admin_instance = self
        try:
            field = self.model._meta.get_field(field_name)
            short_description = getattr(
                field, "verbose_name", field_name.replace("_", " ").title()
            )
        except Exception:
            short_description = field_name.replace("_", " ").title()

        def display(obj):
            val = getattr(obj, field_name, None)
            if val is None:
                return admin_instance.get_empty_value_display()
            # Call the passed formatter method (bound to self)
            return formatter_method(val, field_name=field_name)

        display.short_description = short_description
        display.admin_order_field = field_name
        return display

    def _make_nepali_date_display(self, field_name):
        return self._make_nepali_display(field_name, self.format_nepali_date)

    def _make_nepali_datetime_display(self, field_name):
        return self._make_nepali_display(field_name, self.format_nepali_datetime)

    def _make_nepali_currency_display(self, field_name):
        return self._make_nepali_display(field_name, self.format_nepali_currency)

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        result = []
        for item in list_display:
            if not isinstance(item, str):
                result.append(item)
                continue
            try:
                field = self.model._meta.get_field(item)
                if isinstance(field, NepaliDateField):
                    result.append(self._make_nepali_date_display(item))
                    continue
                if isinstance(field, NepaliDateTimeField):
                    result.append(self._make_nepali_datetime_display(item))
                    continue
                if isinstance(field, NepaliCurrencyField):
                    result.append(self._make_nepali_currency_display(item))
                    continue
            except Exception:
                pass
            result.append(item)
        return result

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Automatically use NepaliDatePicker in the admin form."""
        try:
            from django_nepkit.models import NepaliDateField, NepaliDateTimeField
            from django_nepkit.widgets import NepaliDatePickerWidget
        except Exception:
            return super().formfield_for_dbfield(db_field, request, **kwargs)

        if (
            isinstance(db_field, (NepaliDateField, NepaliDateTimeField))
            and nepkit_settings.ADMIN_DATEPICKER
        ):
            # Pass ne/en parameters from field to widget if they exist
            widget_kwargs = {}
            if hasattr(db_field, "ne"):
                widget_kwargs["ne"] = db_field.ne
            if hasattr(db_field, "en"):
                widget_kwargs["en"] = db_field.en
            kwargs.setdefault("widget", NepaliDatePickerWidget(**widget_kwargs))

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    class Media:
        """Loads the Nepali Datepicker and bridging scripts."""

        css = {
            "all": (
                "https://nepalidatepicker.sajanmaharjan.com.np/v5/nepali.datepicker/css/nepali.datepicker.v5.0.6.min.css",
                "django_nepkit/css/admin-nepali-datepicker.css",
            )
        }
        js = (
            # Bridge admin's `django.jQuery` -> `window.jQuery`
            "django_nepkit/js/admin-jquery-bridge.js",
            # Date picker lib
            "https://nepalidatepicker.sajanmaharjan.com.np/v5/nepali.datepicker/js/nepali.datepicker.v5.0.6.min.js",
            # Init
            "django_nepkit/js/nepali-datepicker-init.js",
        )


__all__ = [
    "NepaliDateFilter",
    "NepaliMonthFilter",
    "format_nepali_date",
    "format_nepali_datetime",
    "NepaliAdminMixin",
    "NepaliModelAdmin",
]
