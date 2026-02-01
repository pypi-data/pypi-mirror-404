from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from aa_skip_email.app_settings import (
    AA_SKIP_EMAIL_DOMAIN,
    AA_SKIP_EMAIL_LIMIT,
)
from aa_skip_email.helpers import make_placeholder_email

User = get_user_model()


class Command(BaseCommand):
    help = "Fill missing user emails with placeholder addresses (one-off run)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=AA_SKIP_EMAIL_LIMIT,
            help=f"Max users to process (default: {AA_SKIP_EMAIL_LIMIT})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not write changes, only show what would be updated.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite emails for ALL users (dangerous).",
        )
        parser.add_argument(
            "--only-placeholders",
            action="store_true",
            help=f"Overwrite only emails that already end with @{AA_SKIP_EMAIL_DOMAIN}.",  # noqa: E501
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]
        only_placeholders = options["only_placeholders"]

        if overwrite:
            qs = User.objects.all().order_by("id").only("id", "email")[:limit]
            if only_placeholders:
                qs = (
                    User.objects.filter(
                        email__iendswith=f"@{AA_SKIP_EMAIL_DOMAIN}"
                    )
                    .order_by("id")
                    .only("id", "email")[:limit]
                )
        else:
            qs = (
                User.objects.filter(Q(email__isnull=True) | Q(email=""))
                .order_by("id")
                .only("id", "email")[:limit]
            )

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("No matching users found."))
            return

        mode = "OVERWRITE" if overwrite else "MISSING-ONLY"
        if overwrite and not dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: --overwrite will replace existing emails."
                )
            )

        updated = 0
        for u in qs.iterator():
            username = u.get_username()
            new_email = make_placeholder_email(username, u.id)

            if dry_run:
                self.stdout.write(
                    f"[DRY:{mode}] id={u.id} {u.email!r} -> {new_email}"
                )
                updated += 1
                continue

            u.email = new_email
            u.save(update_fields=["email"])
            updated += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry-run complete ({mode}). Would update: {updated}/{total}"  # noqa: E501
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done ({mode}). Updated: {updated}/{total}"
                )
            )
