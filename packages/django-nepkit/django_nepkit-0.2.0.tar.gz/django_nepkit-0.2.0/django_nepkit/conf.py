from django.conf import settings

DEFAULTS = {
    "DEFAULT_LANGUAGE": "en",
    "DATE_INPUT_FORMATS": ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"],
    "ADMIN_DATEPICKER": True,
    "TIME_FORMAT": 12,
    "BS_DATE_FORMAT": "%Y-%m-%d",
    "BS_DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
}


class NepkitSettings:
    """Handles the global NEPKIT settings from your settings.py."""

    def __init__(self, user_settings=None, defaults=None):
        self._user_settings = user_settings or {}
        self.defaults = defaults or DEFAULTS

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError(f"Invalid NEPKIT setting: '{attr}'")

        try:
            # Check if the user has a custom setting
            val = self._user_settings[attr]
        except KeyError:
            # Use default value if not set
            val = self.defaults[attr]

        return val


nepkit_settings = NepkitSettings(getattr(settings, "NEPKIT", {}), DEFAULTS)
