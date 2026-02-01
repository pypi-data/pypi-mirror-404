# AA Skip Email (aa_skip_email)

A small Alliance Auth plugin that lets you skip collecting real email addresses
during EVE SSO registration by automatically generating a placeholder `User.email`.
This is useful for integrations (e.g., OIDC clients) that expect `email` to be present.

---

## Features

- Creates a placeholder email for newly created users during SSO registration.
- Includes a one-off Django management command to backfill missing emails.
- Includes a Celery task suitable for periodic execution to keep data consistent.

---

## Requirements

- Alliance Auth

---

## Installation

Install the plugin into the same Python environment as Alliance Auth (pip/uv/poetry-whatever you use).

```bash
pip install aa-skip-email
```

Add the app to `INSTALLED_APPS` (typically in `local.py`):

```python
INSTALLED_APPS += [
    ...
    "aa_skip_email",
    ...
]
```

Add the authentication backend to `AUTHENTICATION_BACKENDS`.

> [!IMPORTANT]
> This plugin replaces Alliance Auth’s default `allianceauth.authentication.backends.StateBackend` behavior.
> Update `AUTHENTICATION_BACKENDS` so that `SkipEmailBackend` is used instead of the original AA StateBackend.

Example:

```python
AUTHENTICATION_BACKENDS = [
    # Replace the original AA StateBackend with this plugin backend
    "aa_skip_email.authentication.backends.SkipEmailBackend",
    # Keep the rest of your original backends
    "django.contrib.auth.backends.ModelBackend",
]
```

---

## Configuration

Configure these in `local.py` (or your equivalent settings file).

### `AA_SKIP_EMAIL_DOMAIN`

Domain used for placeholder addresses.

- Type: `str`
- Default: `no-email.invalid`

```python
AA_SKIP_EMAIL_DOMAIN = "no-email.invalid"
```

Using a domain under `.invalid` helps avoid accidentally generating addresses at a real domain.

### `AA_SKIP_EMAIL_LIMIT`

Default limit for how many users are processed per run by the management command and the Celery task.

- Type: `int`
- Default: `5000`

```python
AA_SKIP_EMAIL_LIMIT = 5000
```

---

## How placeholder emails are generated

A placeholder email is generated from the user’s username
(sanitized to a conservative character set) and a unique suffix
(typically the user id; otherwise a UUID).
The local-part is kept within 64 characters.

Resulting format is similar to:

```code
<sanitized-username>-<id-or-uuid>@<AA_SKIP_EMAIL_DOMAIN>
```

---

## One-off backfill (management command)

The plugin provides a Django management command to fill missing emails.

### Fill missing emails (default)

```bash
python manage.py fill_missing_emails
```

### Limit number of users

```bash
python manage.py fill_missing_emails --limit 5000
```

### Dry-run (no writes)

```bash
python manage.py fill_missing_emails --dry-run --limit 50
```

### Overwrite emails for all users

> [!CAUTION]
> This will replace existing emails.

```bash
python manage.py fill_missing_emails --overwrite
```

### Overwrite only existing placeholders

Safer if some users have real emails and you only want to regenerate placeholders.

```bash
python manage.py fill_missing_emails --overwrite --only-placeholders
```

---

## Scheduler (Celery Beat)

The plugin includes a Celery task named:

- `aa_skip_email.fill_missing_emails`

To run it periodically, add a schedule entry in `local.py` using `CELERYBEAT_SCHEDULE`.

### Example: run every 6 hours

```python
from celery.schedules import crontab

CELERYBEAT_SCHEDULE["aa_skip_email_fill_missing_emails"] = {
    "task": "aa_skip_email.fill_missing_emails",
    "schedule": crontab(minute=0, hour="*/6"),
    # Optional: helps spread load across instances in some AA deployments
    "apply_offset": True,
}
```

### Example: run daily at 04:15

```python
from celery.schedules import crontab

CELERYBEAT_SCHEDULE["aa_skip_email_fill_missing_emails"] = {
    "task": "aa_skip_email.fill_missing_emails",
    "schedule": crontab(minute=15, hour=4),
    "apply_offset": True,
}
```

---

## See also

- [allianceauth/issues/1286](https://gitlab.com/allianceauth/allianceauth/-/issues/1286)
- [allianceauth.allianceauth.backends](https://gitlab.com/allianceauth/allianceauth/-/blob/master/allianceauth/authentication/backends.py)
- [github.com/allianceauth/allianceauth/issues/1060](https://github.com/allianceauth/allianceauth/issues/1060)
