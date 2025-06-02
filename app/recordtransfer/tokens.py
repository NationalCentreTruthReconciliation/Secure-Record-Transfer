from django.contrib.auth.tokens import PasswordResetTokenGenerator

from recordtransfer.models import User


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Strategy object used to generate and check tokens for user account activation."""

    def __init__(self):
        super().__init__()
        # sha1 is 40 characters. Since _make_token_with_timestamp returns every second character of
        # the hash hexdigest, we know the token will be 20 characters long.
        self.algorithm = "sha1"

    def _make_hash_value(self, user: User, timestamp: int): # type: ignore
        """Create a hash input value to be used in the token generation. The generated token
        is invalidated if the user is active or if the timestamp is too old.
        """
        return f"{user.pk}{timestamp}{user.is_active}"


account_activation_token = AccountActivationTokenGenerator()
