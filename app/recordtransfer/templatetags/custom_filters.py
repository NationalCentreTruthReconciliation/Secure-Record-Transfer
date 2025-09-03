from django import template
from utility import get_human_readable_size

register = template.Library()


@register.filter
def dict_get(d: dict, key: str) -> str:
    """Retrieve a value from a dictionary by key, returning an empty string
    if the key is not found.
    """
    return d.get(key, "")


@register.filter
def filesizeformat(size_bytes: int) -> str:
    """Convert bytes to human-readable file size using binary prefixes (KiB, MiB, etc.)."""
    if size_bytes is None:
        return "0 B"
    return get_human_readable_size(size_bytes, base=1024, precision=1)


@register.filter
def subtract(value: int, arg: int) -> int:
    """Subtract one number from another."""
    return value - arg
