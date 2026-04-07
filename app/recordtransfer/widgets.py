from typing import Any, Optional

from django.utils.safestring import SafeText, mark_safe
from django_countries.widgets import CountrySelectWidget


class CustomCountrySelectWidget(CountrySelectWidget):
    """Custom Country Select Widget that wraps the rendered field in a container div, so that both
    the select field and the flag show side by side.
    """

    FLAG_LAYOUT = (
        '{widget}<img class="country-select-flag" id="{flag_id}" src="{country.flag}" alt="" aria-hidden="true">'
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Render the flag without inline styles so our CSS can position it reliably."""
        kwargs.setdefault("layout", self.FLAG_LAYOUT)
        super().__init__(*args, **kwargs)

    def render(
        self,
        name: str,
        value: object,
        attrs: Optional[dict] = None,
        renderer: Optional[object] = None,
    ) -> SafeText:
        """Render the widget with a container div around it."""
        rendered = super().render(name, value, attrs, renderer)
        return mark_safe(f'<div class="country-select-container">{rendered}</div>')
