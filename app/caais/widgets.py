from django.conf import settings
from django.forms.widgets import CheckboxInput, TextInput
from django.utils.safestring import SafeText, mark_safe


class DateOfMaterialsWidget(TextInput):
    """Custom widget for date_of_materials field of the MetadataForm."""

    def render(self, name, value, attrs=None, renderer=None) -> SafeText:
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
    """Custom widget for date_is_approximate field of the MetadataForm."""

    def render(self, name, value, attrs=None, renderer=None) -> SafeText:
        """Render the widget with additional HTML elements."""
        original_html = super().render(name, value, attrs, renderer)
        return mark_safe(
            f'<div class="date-is-approximate-wrapper">{original_html}</div>'
        )
