from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

CAAIS_URL = _("https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf")


def cite_caais(text: str, section: tuple, html: bool = True) -> str:
    """Add CAAIS citation to end of text, with link to CAAIS document."""
    section_str = ".".join(map(str, section))
    if html:
        return mark_safe(
            _("%(text)s [%(link_start)sCAAIS%(link_end)s %(section)s]")
            % {
                "text": text,
                "link_start": f'<a href="{CAAIS_URL}" target="_blank">',
                "link_end": "</a>",
                "section": section_str,
            }
        )

    return _("%(text)s [CAAIS %(section)s]") % {
        "text": text,
        "section": section_str,
    }


# Create a lazy version for use in model help_text
cite_caais_lazy = lazy(cite_caais, str)
