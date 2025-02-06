from django.contrib.auth.tokens import PasswordResetTokenGenerator

from recordtransfer.models import User

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def __init__(self):
        super().__init__()
        # sha1 is 40 characters. Since _make_token_with_timestamp returns every second character of
        # the hash hexdigest, we know the token will be 20 characters long.
        self.algorithm = 'sha1'

    def _make_hash_value(self, user: User, timestamp):
        return str(user.pk) + str(timestamp) + str(user.confirmed_email)

account_activation_token = AccountActivationTokenGenerator()
