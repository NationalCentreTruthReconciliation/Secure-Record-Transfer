from typing import Any

from django import template

register = template.Library()


@register.filter
def class_name(value: Any) -> str:
    """Get the class name of an object as a string."""
    return value.__class__.__name__
