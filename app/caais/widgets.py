from typing import Any, Dict, Optional

from django.conf import settings
from django.forms.renderers import BaseRenderer
from django.forms.widgets import CheckboxInput, TextInput
from django.utils.safestring import SafeText, mark_safe
from django_countries.widgets import CountrySelectWidget


class DateOfMaterialsWidget(TextInput):
    """Custom widget for date_of_materials field for use in the MetadataForm."""

    def render(
        self,
        name: str,
        value: str | None,
        attrs: Optional[Dict[str, Any]] = None,
        renderer: Optional[BaseRenderer] = None,
    ) -> SafeText:
        """Render the widget with additional HTML elements."""
        original_html = super().render(name, value, attrs, renderer)

        parts = settings.APPROXIMATE_DATE_FORMAT.split("{date}")
        prefix = parts[0] if len(parts) > 0 else ""
        suffix = parts[1] if len(parts) > 1 else ""

        return mark_safe(
            f'<div class="date-materials-wrapper">'
            f'<span class="approx-date-wrapper">{prefix}</span>{original_html}'
            f'<span class="approx-date-wrapper">{suffix}</span></div>'
        )


class DateIsApproximateWidget(CheckboxInput):
    """Custom widget for date_is_approximate field for use in the MetadataForm."""

    def render(
        self,
        name: str,
        value: Any,
        attrs: Optional[Dict[str, Any]] = None,
        renderer: Optional[BaseRenderer] = None,
    ) -> SafeText:
        """Render the widget with additional HTML elements."""
        original_html = super().render(name, value, attrs, renderer)
        return mark_safe(f'<div class="date-is-approximate-wrapper">{original_html}</div>')


class CustomCountrySelectWidget(CountrySelectWidget):
    """Custom Country Select Widget that wraps the rendered field in a container div, so that both
    the select field and the flag show side by side.
    """

    def render(
        self,
        name: str,
        value: Any,
        attrs: Optional[Dict[str, Any]] = None,
        renderer: Optional[BaseRenderer] = None,
    ) -> SafeText:
        """Render the widget with a container div around it."""
        rendered = super().render(name, value, attrs, renderer)
        return SafeText(f'<div class="country-select-container">{rendered}</div>')
