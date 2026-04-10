import re
import bleach
from django.core.exceptions import ValidationError
from django.utils.html import escape


# ── Allowed HTML tags for reviews (very minimal) ──────────────
ALLOWED_TAGS   = []   # no HTML at all in reviews
ALLOWED_ATTRS  = {}


def sanitize_text(value):
    """
    Strip all HTML tags from user input.
    Used for reviews, bios, addresses etc.
    """
    if not value:
        return value
    # Use bleach to strip tags
    cleaned = bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return cleaned.strip()


def validate_no_script(value):
    """
    Django validator — raises ValidationError if input
    contains script tags or javascript: URIs.
    Use in forms or models.
    """
    patterns = [
        r'<\s*script',
        r'javascript\s*:',
        r'on\w+\s*=',
        r'<\s*iframe',
        r'<\s*object',
        r'<\s*embed',
        r'<\s*link',
        r'<\s*meta',
        r'vbscript\s*:',
        r'data\s*:\s*text/html',
    ]
    for pattern in patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                'Invalid content detected. HTML and scripts are not allowed.'
            )


def validate_isbn(value):
    """Validate ISBN-10 or ISBN-13 format."""
    cleaned = value.replace('-', '').replace(' ', '')
    if not re.match(r'^\d{9}[\dX]$|^\d{13}$', cleaned):
        raise ValidationError('Enter a valid ISBN-10 or ISBN-13.')


def validate_price(value):
    """Ensure price is positive and reasonable."""
    if value <= 0:
        raise ValidationError('Price must be greater than zero.')
    if value > 9999:
        raise ValidationError('Price cannot exceed €9,999.')


def safe_redirect_url(url, fallback='/'):
    """
    Prevents open redirect attacks.
    Only allows relative URLs.
    """
    if url and url.startswith('/') and not url.startswith('//'):
        return url
    return fallback