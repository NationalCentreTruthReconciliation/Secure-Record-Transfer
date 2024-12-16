from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def update_query_params(context, key, value):
    """Update query parameters with a dynamically provided key and value."""
    request = context['request']
    query_params = request.GET.copy()
    query_params[key] = value
    return query_params.urlencode()
