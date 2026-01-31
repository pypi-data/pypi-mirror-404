from django.http import JsonResponse, HttpResponse

from django_nepkit.utils import (
    get_districts_by_province,
    get_municipalities_by_district,
)


from django_nepkit.conf import nepkit_settings


def _render_options(data, placeholder):
    """Internal helper to render list of options as HTML."""
    options = [f'<option value="">{placeholder}</option>']
    for item in data:
        options.append(f'<option value="{item["id"]}">{item["text"]}</option>')
    return HttpResponse("\n".join(options))


def district_list_view(request):
    province = request.GET.get("province")

    # Fallback: take the first non-internal parameter as province
    if not province:
        for key, value in request.GET.items():
            if key not in ["ne", "en", "html"] and value:
                province = value
                break

    if not province:
        return JsonResponse([], safe=False)

    default_lang = nepkit_settings.DEFAULT_LANGUAGE
    ne_param = request.GET.get("ne")
    ne = ne_param.lower() == "true" if ne_param else default_lang == "ne"

    en_param = request.GET.get("en")
    en = en_param.lower() == "true" if en_param else not ne

    as_html = (
        request.GET.get("html", "false").lower() == "true"
        or request.headers.get("HX-Request") == "true"
    )

    data = get_districts_by_province(province, ne=ne, en=en)

    if as_html:
        placeholder = "जिल्ला छान्नुहोस्" if ne else "Select District"
        return _render_options(data, placeholder)

    return JsonResponse(data, safe=False)


def municipality_list_view(request):
    district = request.GET.get("district")

    # Fallback: take the first non-internal parameter as district
    if not district:
        for key, value in request.GET.items():
            if key not in ["ne", "en", "html"] and value:
                district = value
                break

    if not district:
        return JsonResponse([], safe=False)

    default_lang = nepkit_settings.DEFAULT_LANGUAGE
    ne_param = request.GET.get("ne")
    ne = ne_param.lower() == "true" if ne_param else default_lang == "ne"

    en_param = request.GET.get("en")
    en = en_param.lower() == "true" if en_param else not ne

    as_html = (
        request.GET.get("html", "false").lower() == "true"
        or request.headers.get("HX-Request") == "true"
    )

    data = get_municipalities_by_district(district, ne=ne, en=en)

    if as_html:
        placeholder = "नगरपालिका छान्नुहोस्" if ne else "Select Municipality"
        return _render_options(data, placeholder)

    return JsonResponse(data, safe=False)
