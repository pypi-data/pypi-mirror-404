from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

try:
    from django_filters import rest_framework as filters
except ImportError as e:
    raise ModuleNotFoundError(
        "django-nepkit filter support is optional. Install with `django-nepkit[drf]` "
        "to use `django_nepkit.filters`."
    ) from e


class NepaliDateYearFilter(filters.NumberFilter):
    """
    A filter for `NepaliDateField` that allows filtering by Bikram Sambat Year.
    Expects an integer year (e.g., 2080).
    """

    def filter(self, qs: QuerySet, value: Any) -> QuerySet:
        if value:
            from django_nepkit.utils import BS_DATE_FORMAT

            # Find the date separator (e.g., '-' in '2080-01-01')
            if BS_DATE_FORMAT.startswith("%Y"):
                separator = BS_DATE_FORMAT[2] if len(BS_DATE_FORMAT) > 2 else "-"
                return qs.filter(
                    **{f"{self.field_name}__startswith": f"{value}{separator}"}
                )

            # Fallback if the format is unusual
            return qs.filter(**{f"{self.field_name}__icontains": str(value)})
        return qs


class NepaliDateMonthFilter(filters.NumberFilter):
    """
    A filter for `NepaliDateField` that allows filtering by Bikram Sambat Month.
    Expects an integer month (1-12).
    """

    def filter(self, qs: QuerySet, value: Any) -> QuerySet:
        if value:
            from django_nepkit.utils import BS_DATE_FORMAT

            month_str = f"{int(value):02d}"

            # Standard format: look for '-01-' for Baisakh
            if BS_DATE_FORMAT == "%Y-%m-%d":
                return qs.filter(**{f"{self.field_name}__contains": f"-{month_str}-"})

            # Adaptive check for other separators
            separator = BS_DATE_FORMAT[2] if len(BS_DATE_FORMAT) > 2 else "-"
            return qs.filter(
                **{f"{self.field_name}__contains": f"{separator}{month_str}{separator}"}
            )
        return qs


class NepaliDateRangeFilter(filters.CharFilter):
    """
    A filter for `NepaliDateField` that allows filtering by a range of BS dates.
    Supports:
    - "start,end" -> range
    - "start," -> greater than or equal
    - ",end" -> less than or equal
    - "date" -> exact match
    """

    def filter(self, qs: QuerySet, value: Any) -> QuerySet:
        if value:
            parts = [p.strip() for p in str(value).split(",")]
            if len(parts) == 1:
                return qs.filter(**{self.field_name: parts[0]})
            if len(parts) == 2:
                if parts[0] and parts[1]:
                    return qs.filter(
                        **{f"{self.field_name}__range": (parts[0], parts[1])}
                    )
                if parts[0]:
                    return qs.filter(**{f"{self.field_name}__gte": parts[0]})
                if parts[1]:
                    return qs.filter(**{f"{self.field_name}__lte": parts[1]})
        return qs


class NepaliCurrencyRangeFilter(filters.CharFilter):
    """
    A filter for `NepaliCurrencyField` that allows range filtering.
    Supports:
    - "min,max" -> range
    - "min," -> greater than or equal
    - ",max" -> less than or equal
    - "value" -> exact match
    """

    def filter(self, qs: QuerySet, value: Any) -> QuerySet:
        if value:
            parts = [p.strip() for p in str(value).split(",")]
            if len(parts) == 1:
                return qs.filter(**{self.field_name: parts[0]})
            if len(parts) == 2:
                if parts[0] and parts[1]:
                    return qs.filter(
                        **{f"{self.field_name}__range": (parts[0], parts[1])}
                    )
                if parts[0]:
                    return qs.filter(**{f"{self.field_name}__gte": parts[0]})
                if parts[1]:
                    return qs.filter(**{f"{self.field_name}__lte": parts[1]})
        return qs
