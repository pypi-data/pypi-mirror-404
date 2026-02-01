import logging

from allianceauth.authentication.backends import StateBackend
from allianceauth.authentication.models import CharacterOwnership
from django.contrib.auth import get_user_model

from aa_skip_email.helpers import make_placeholder_email

logger = logging.getLogger(__name__)
User = get_user_model()


class SkipEmailBackend(StateBackend):
    def create_user(self, token):
        username = self.iterate_username(token.character_name)
        user = User.objects.create_user(
            username, is_active=True
        )  # skip asking the email
        user.set_unusable_password()
        if not user.email:
            user.email = make_placeholder_email(username, user.pk)
        user.save()
        token.user = user
        co = CharacterOwnership.objects.create_by_token(token)
        user.profile.main_character = co.character
        user.profile.save()
        logger.debug("Created new user %s", user)
        return user
