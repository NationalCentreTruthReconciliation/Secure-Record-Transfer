from django import template

register = template.Library()


@register.filter
def dict_get(d: dict, key: str) -> str:
    """Retrieve a value from a dictionary by key, returning an empty string
    if the key is not found.
    """
    return d.get(key, "")
