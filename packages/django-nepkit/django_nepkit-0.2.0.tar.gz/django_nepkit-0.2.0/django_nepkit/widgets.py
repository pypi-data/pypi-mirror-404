from django import forms
from django.urls import reverse, NoReverseMatch
from nepali.datetime import nepalidate
from django_nepkit.utils import BS_DATE_FORMAT

from django_nepkit.conf import nepkit_settings


def _append_css_class(attrs, class_name: str):
    """Helper to add a CSS class safely."""
    existing = (attrs.get("class") or "").strip()
    attrs["class"] = (f"{existing} {class_name}").strip() if existing else class_name
    return attrs


class NepaliWidgetMixin:
    def __init__(self, *args, **kwargs):
        default_lang = nepkit_settings.DEFAULT_LANGUAGE
        self.ne = kwargs.pop("ne", default_lang == "ne")

        self.en = kwargs.pop("en", not self.ne)
        self.htmx = kwargs.pop("htmx", False)

        attrs = kwargs.get("attrs", {}) or {}

        # Language settings
        if self.ne:
            attrs["data-ne"] = "true"
        if self.en:
            attrs["data-en"] = "true"

        # Pass the date format to JavaScript
        attrs["data-format"] = BS_DATE_FORMAT

        self._configure_attrs(attrs)

        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)

    def _configure_attrs(self, attrs):
        """Override in subclasses or use class attributes."""
        css_class = getattr(self, "css_class", None)
        if css_class:
            _append_css_class(attrs, css_class)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget_attrs = context.get("widget", {}).get("attrs", {})

        # Handle URLs for data fetching
        url_name = getattr(self, "_url_name", None)
        if url_name:
            try:
                widget_attrs["data-url"] = reverse(url_name)
            except NoReverseMatch:
                pass

        # Handle HTMX dynamic updates
        if self.htmx:
            hx_url_name = getattr(self, "_hx_url_name", None)
            if hx_url_name:
                try:
                    widget_attrs["hx-get"] = reverse(hx_url_name)
                    widget_attrs["hx-target"] = getattr(self, "_hx_target", "")
                    widget_attrs["hx-trigger"] = "change"
                except NoReverseMatch:
                    pass

        return context


class ChainedSelectWidget(forms.Select):
    class Media:
        js = (
            "django_nepkit/js/nepal-data.js",
            "django_nepkit/js/address-chaining.js",
        )


class ProvinceSelectWidget(NepaliWidgetMixin, ChainedSelectWidget):
    css_class = "nepkit-province-select"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.htmx:
            self._hx_url_name = "django_nepkit:district-list"
            self._hx_target = ".nepkit-district-select"


class DistrictSelectWidget(NepaliWidgetMixin, ChainedSelectWidget):
    css_class = "nepkit-district-select"
    _url_name = "django_nepkit:district-list"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.htmx:
            self._hx_url_name = "django_nepkit:municipality-list"
            self._hx_target = ".nepkit-municipality-select"


class MunicipalitySelectWidget(NepaliWidgetMixin, ChainedSelectWidget):
    css_class = "nepkit-municipality-select"
    _url_name = "django_nepkit:municipality-list"


class NepaliDatePickerWidget(NepaliWidgetMixin, forms.TextInput):
    input_type = "text"

    class Media:
        css = {
            "all": (
                "https://nepalidatepicker.sajanmaharjan.com.np/v5/nepali.datepicker/css/nepali.datepicker.v5.0.6.min.css",
            )
        }
        js = (
            "https://code.jquery.com/jquery-3.5.1.slim.min.js",
            "https://nepalidatepicker.sajanmaharjan.com.np/v5/nepali.datepicker/js/nepali.datepicker.v5.0.6.min.js",
            "django_nepkit/js/nepali-datepicker-init.js",
        )

    def _configure_attrs(self, attrs):
        classes = attrs.get("class", "")
        if "vDateField" in classes:
            classes = classes.replace("vDateField", "")
        attrs["class"] = classes

        _append_css_class(attrs, "nepkit-datepicker")
        attrs["autocomplete"] = "off"
        attrs["placeholder"] = (
            BS_DATE_FORMAT.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")
        )

    def format_value(self, value):
        if value is None:
            return None

        if self.ne and isinstance(value, nepalidate):
            if hasattr(value, "strftime_ne"):
                return value.strftime_ne(BS_DATE_FORMAT)

        return super().format_value(value)
