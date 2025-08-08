from typing import Optional

from django.utils.safestring import SafeText
from django_countries.widgets import CountrySelectWidget


class CustomCountrySelectWidget(CountrySelectWidget):
    """Custom Country Select Widget that wraps the rendered field in a container div, so that both
    the select field and the flag show side by side.
    """

    def render(
        self,
        name: str,
        value: object,
        attrs: Optional[dict] = None,
        renderer: Optional[object] = None,
    ) -> SafeText:
        """Render the widget with a container div around it."""
        rendered = super().render(name, value, attrs, renderer)
        return SafeText(f'<div class="country-select-container">{rendered}</div>')
