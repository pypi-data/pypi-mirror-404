from typing import Final

from django.conf import settings

AA_SKIP_EMAIL_DOMAIN: Final[str] = getattr(
    settings, "AA_SKIP_EMAIL_DOMAIN", "no-email.invalid"
)

AA_SKIP_EMAIL_LIMIT: Final[int] = getattr(
    settings, "AA_SKIP_EMAIL_LIMIT", 5000
)

AA_SKIP_EMAIL_FALLBACK_USERNAME: Final[str] = "user"

AA_SKIP_EMAIL_SEPARATOR: Final[str] = "-"
