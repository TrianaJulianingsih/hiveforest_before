from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from datetime import timedelta
import six


# FaisalS | HF-8 - Forced Password Change function
class ExpiringPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        login_timestamp = (
            ""
            if user.last_login is None
            else timezone.make_naive(
                user.last_login.replace(microsecond=0),
                timezone.utc,
            )
        )

        return (
            six.text_type(user.pk)
            + six.text_type(timestamp)
            + six.text_type(user.is_active)
            + six.text_type(login_timestamp)
        )

    def is_token_expired(self, token_timestamp):
        token_time = timezone.make_aware(
            timezone.datetime(2001, 1, 1),
            timezone.utc,
        ) + timedelta(days=token_timestamp)

        return timezone.now() > token_time + timedelta(minutes=2)

    def check_token(self, user, token):
        if not user or not token:
            return False

        try:
            ts_b36, _ = token.split("-")
            from django.utils.http import base36_to_int

            token_ts = base36_to_int(ts_b36)
        except (ValueError, TypeError):
            return False

        if not super().check_token(user, token):
            return False

        return not self.is_token_expired(token_ts)
