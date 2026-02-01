import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Q

from aa_skip_email.app_settings import AA_SKIP_EMAIL_LIMIT
from aa_skip_email.helpers import make_placeholder_email

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(name="aa_skip_email.fill_missing_emails")
def fill_missing_emails(limit=AA_SKIP_EMAIL_LIMIT):
    qs = (
        User.objects.filter(Q(email__isnull=True) | Q(email=""))
        .order_by("id")
        .only("id", "email")[:limit]
    )
    updated = 0
    for u in qs.iterator():
        username = u.get_username()
        u.email = make_placeholder_email(username, u.id)
        u.save(update_fields=["email"])
        updated += 1
        logger.debug("Filled in missing email for %s", u)
    return updated
