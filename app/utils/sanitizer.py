"""Input sanitization to prevent XSS."""

import bleach

ALLOWED_TAGS = []
ALLOWED_ATTRIBUTES = {}


def sanitize_html(text):
    """Strip all HTML tags from user input."""
    if not text:
        return text
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def sanitize_dict(data):
    """Sanitize all string values in a dictionary."""
    return {k: sanitize_html(v) if isinstance(v, str) else v for k, v in data.items()}
