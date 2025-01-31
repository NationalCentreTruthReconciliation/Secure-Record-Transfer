from django import template
from django.template.context import RequestContext

register = template.Library()

@register.simple_tag(takes_context=True)
def update_query_params(context: RequestContext, key: str, value: str) -> str:
    """Update or add onto existing query parameters with a dynamically provided key and value.

    Args:
        context: The context containing the request object.
        key: The query parameter key to update or add.
        value: The value to assign to the query parameter.

    Returns:
        The updated query string with the new or modified query parameter.
    """
    request = context['request']
    query_params = request.GET.copy()
    query_params[key] = value
    return query_params.urlencode()
