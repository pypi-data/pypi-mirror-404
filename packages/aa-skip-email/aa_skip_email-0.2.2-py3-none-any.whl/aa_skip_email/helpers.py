import re
import uuid
from typing import Optional

from aa_skip_email.app_settings import (
    AA_SKIP_EMAIL_DOMAIN,
    AA_SKIP_EMAIL_FALLBACK_USERNAME,
    AA_SKIP_EMAIL_SEPARATOR,
)


def make_placeholder_email(
    username: Optional[str] = None, id: Optional[int] = None
) -> str:
    if username:
        safe = (
            re.sub(
                r"[^A-Za-z0-9.+-]+", AA_SKIP_EMAIL_SEPARATOR, username
            ).strip(AA_SKIP_EMAIL_SEPARATOR)
            or AA_SKIP_EMAIL_FALLBACK_USERNAME
        )
    else:
        safe = AA_SKIP_EMAIL_FALLBACK_USERNAME
    suffix = str(id) if id is not None else uuid.uuid4().hex
    separator = AA_SKIP_EMAIL_SEPARATOR
    max_local = 64
    max_safe = max(1, max_local - len(separator) - len(suffix))
    safe = safe[:max_safe]
    return f"{safe}{separator}{suffix}@{AA_SKIP_EMAIL_DOMAIN}"
