from typing import Any, NamedTuple, Optional

from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from recordtransfer.constants import QueryParameters
from recordtransfer.enums import SiteSettingKey
from recordtransfer.models import SiteSetting


def paginated_table_view(
    request: HttpRequest,
    queryset: QuerySet,
    template_name: str,
    target_id: str,
    paginate_url: str,
    extra_context: Optional[dict[str, Any]] = None,
) -> HttpResponse:
    """Define a generic function to render paginated tables. Request must be made by HTMX, or else
    a 400 Error is returned.
    """
    if not request.htmx:
        return HttpResponse(status=400)

    paginator = Paginator(queryset, SiteSetting.get_value_int(SiteSettingKey.PAGINATE_BY))
    page_num = request.GET.get(QueryParameters.PAGINATE_QUERY_NAME, 1)

    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        page_num = 1

    if page_num < 1:
        page_num = 1
    elif page_num > paginator.num_pages:
        page_num = paginator.num_pages

    context = {
        "page": paginator.get_page(page_num),
        "page_num": page_num,
        "target_id": target_id,
        "paginate_url": paginate_url,
        **(extra_context or {}),
    }

    return render(request, template_name, context)
