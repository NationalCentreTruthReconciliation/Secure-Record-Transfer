from django.utils.html import strip_tags


def html_to_text(html: str) -> str:
    """Convert HTML content to plain text by stripping tags and whitespace."""
    no_tags_split = strip_tags(html).split("\n")
    plain_text_split = filter(None, map(str.strip, no_tags_split))
    return "\n".join(plain_text_split)
