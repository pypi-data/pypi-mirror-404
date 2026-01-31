(function () {
  "use strict";

  // Django admin exposes jQuery as `django.jQuery`.
  // Many third-party plugins expect `window.jQuery`/`window.$`.
  if (typeof window !== "undefined" && window.django && window.django.jQuery) {
    window.jQuery = window.django.jQuery;
    window.$ = window.django.jQuery;
  }
})();
