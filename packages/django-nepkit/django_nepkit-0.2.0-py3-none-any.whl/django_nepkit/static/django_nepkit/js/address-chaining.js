(function() {
    'use strict';

    function updateOptions(selectElement, data, placeholder) {
        selectElement.innerHTML = '';
        if (placeholder) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = placeholder;
            selectElement.appendChild(opt);
        }
        data.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.id;
            opt.textContent = item.text;
            selectElement.appendChild(opt);
        });
        selectElement.dispatchEvent(new Event('change'));
    }

    function getLocalData(type, parentId, isNepali) {
        if (!window.NEPKIT_DATA) return null;
        const lang = isNepali ? 'ne' : 'en';
        const data = window.NEPKIT_DATA[lang];
        if (!data) return null;

        if (type === 'districts') {
            return data.districts[parentId] || [];
        } else if (type === 'municipalities') {
            return data.municipalities[parentId] || [];
        }
        return null;
    }

    function getMatchingSelect(container, selector, isNepali) {
        const matches = container.querySelectorAll(selector);
        for (let el of matches) {
            const elIsNepali = el.dataset.ne === 'true';
            if (elIsNepali === isNepali) {
                return el;
            }
        }
        return null;
    }

    function init() {
        document.querySelectorAll('.nepkit-province-select').forEach(provinceSelect => {
            const isNepali = provinceSelect.dataset.ne === 'true';
            const container = provinceSelect.closest('form') || document;
            const districtSelect = getMatchingSelect(container, '.nepkit-district-select', isNepali);
            const municipalitySelect = getMatchingSelect(container, '.nepkit-municipality-select', isNepali);

            if (!provinceSelect.value) {
                if (districtSelect && !districtSelect.value) {
                    updateOptions(districtSelect, [], isNepali ? 'जिल्ला छान्नुहोस्' : 'Select District');
                }
                if (municipalitySelect && !municipalitySelect.value) {
                    updateOptions(municipalitySelect, [], isNepali ? 'नगरपालिका छान्नुहोस्' : 'Select Municipality');
                }
            }
        });

        document.querySelectorAll('.nepkit-district-select').forEach(districtSelect => {
            const isNepali = districtSelect.dataset.ne === 'true';
            const container = districtSelect.closest('form') || document;
            const municipalitySelect = getMatchingSelect(container, '.nepkit-municipality-select', isNepali);

            if (!districtSelect.value) {
                if (municipalitySelect && !municipalitySelect.value) {
                    updateOptions(municipalitySelect, [], isNepali ? 'नगरपालिका छान्नुहोस्' : 'Select Municipality');
                }
            }
        });
    }

    document.addEventListener('change', function(e) {
        if (e.target.matches('.nepkit-province-select')) {
            const province = e.target.value;
            const isNepali = e.target.dataset.ne === 'true';
            const container = e.target.closest('form') || document;
            const districtSelect = getMatchingSelect(container, '.nepkit-district-select', isNepali);
            const municipalitySelect = getMatchingSelect(container, '.nepkit-municipality-select', isNepali);

            // Always clear municipality if province changes
            if (municipalitySelect) {
                updateOptions(municipalitySelect, [], isNepali ? 'नगरपालिका छान्नुहोस्' : 'Select Municipality');
            }

            if (districtSelect) {
                if (!province) {
                    updateOptions(districtSelect, [], isNepali ? 'जिल्ला छान्नुहोस्' : 'Select District');
                    return;
                }

                const localData = getLocalData('districts', province, isNepali);

                if (localData) {
                    updateOptions(districtSelect, localData, isNepali ? 'जिल्ला छान्नुहोस्' : 'Select District');
                } else if (districtSelect.dataset.url) {
                    // Fallback to AJAX
                    let url = districtSelect.dataset.url + '?province=' + encodeURIComponent(province);
                    if (isNepali) url += '&ne=true';
                    if (districtSelect.dataset.en === 'true') url += '&en=true';

                    fetch(url)
                        .then(response => response.json())
                        .then(data => {
                            updateOptions(districtSelect, data, isNepali ? 'जिल्ला छान्नुहोस्' : 'Select District');
                        });
                }
            }
        }

        if (e.target.matches('.nepkit-district-select')) {
            const district = e.target.value;
            const isNepali = e.target.dataset.ne === 'true';
            const container = e.target.closest('form') || document;
            const municipalitySelect = getMatchingSelect(container, '.nepkit-municipality-select', isNepali);

            if (municipalitySelect) {
                if (!district) {
                    updateOptions(municipalitySelect, [], isNepali ? 'नगरपालिका छान्नुहोस्' : 'Select Municipality');
                    return;
                }

                const localData = getLocalData('municipalities', district, isNepali);

                if (localData) {
                    updateOptions(municipalitySelect, localData, isNepali ? 'नगरपालिका छान्नुहोस्' : 'Select Municipality');
                } else if (municipalitySelect.dataset.url) {
                    // Fallback to AJAX
                    let url = municipalitySelect.dataset.url + '?district=' + encodeURIComponent(district);
                    if (isNepali) url += '&ne=true';
                    if (municipalitySelect.dataset.en === 'true') url += '&en=true';

                    fetch(url)
                        .then(response => response.json())
                        .then(data => {
                            updateOptions(municipalitySelect, data, isNepali ? 'नगरपालिका छान्नुहोस्' : 'Select Municipality');
                        });
                }
            }
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
