(function () {
    'use strict';

    function isDarkTheme() {
        var docEl = document.documentElement;
        var body = document.body;

        // Common theme markers used by Django admin themes / dark-mode packages
        var markers = [
            docEl && docEl.getAttribute('data-theme'),
            docEl && docEl.getAttribute('data-color-scheme'),
            body && body.getAttribute('data-theme'),
            body && body.getAttribute('data-color-scheme')
        ].filter(Boolean).join(' ').toLowerCase();

        var classNames = [
            docEl && docEl.className,
            body && body.className
        ].filter(Boolean).join(' ').toLowerCase();

        if (markers.indexOf('dark') !== -1 || classNames.indexOf('dark') !== -1) return true;

        // Fallback to OS preference
        try {
            return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        } catch (e) {
            return false;
        }
    }

    function applyThemeToDatepickerContainers() {
        var dark = isDarkTheme();
        var containers = document.querySelectorAll('.ndp-container');
        if (!containers || !containers.length) return;

        containers.forEach(function (c) {
            c.classList.remove('ndp-dark');
            c.classList.remove('ndp-light');
            c.classList.add(dark ? 'ndp-dark' : 'ndp-light');
        });
    }

    function initNepaliDatePickers() {
        var inputs = document.querySelectorAll('.nepkit-datepicker:not(.nepali-datepicker-initialized)');
        if (!inputs || !inputs.length) return;

        inputs.forEach(function (el) {
            var format = el.dataset.format || 'YYYY-MM-DD';
            // Convert strftime format to datepicker format
            format = format.replace(/%Y/g, 'YYYY').replace(/%m/g, 'MM').replace(/%d/g, 'DD');

            var options = {
                dateFormat: format,
                closeOnDateSelect: true
            };

            // Determine language based on data attributes
            var useNepali = el.dataset.ne === 'true';
            var useEnglish = el.dataset.en === 'true';

            if (useNepali) {
                // Devanagari digits and Nepali month/day names
                options.unicodeDate = true;
            } else if (useEnglish || (!useNepali && !el.dataset.ne)) {
                // English month/day names and digits
                options.language = 'english';
            }

            // Nepali Datepicker v5 exposes `element.NepaliDatePicker(options)`
            if (typeof el.NepaliDatePicker === 'function') {
                el.NepaliDatePicker(options);
                el.classList.add('nepali-datepicker-initialized');
            }
            // Fallback for jQuery plugin (v2.0.2)
            else if (typeof window.jQuery !== 'undefined' && typeof window.jQuery(el).nepaliDatePicker === 'function') {
                window.jQuery(el).nepaliDatePicker(options);
                el.classList.add('nepali-datepicker-initialized');
            }

            // Ensure theme is applied when the picker is actually shown.
            // (The plugin often creates/inserts DOM on focus.)
            var applySoon = function () {
                // Run twice: once immediately, once after paint.
                applyThemeToDatepickerContainers();
                window.setTimeout(applyThemeToDatepickerContainers, 0);
            };

            el.addEventListener('focus', applySoon);
            el.addEventListener('click', applySoon);
        });
    }

    // Also listen for DOM changes (admin popups/other dynamic content)
    function initObserver() {
        if (typeof MutationObserver !== 'undefined' && document.body) {
            var observer = new MutationObserver(function () {
                initNepaliDatePickers();
                applyThemeToDatepickerContainers();
            });
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initNepaliDatePickers();
            initObserver();
        });
    } else {
        initNepaliDatePickers();
        initObserver();
    }
})();
