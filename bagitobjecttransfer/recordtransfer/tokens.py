from django.contrib.auth.tokens import PasswordResetTokenGenerator

from recordtransfer.models import User

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user: User, timestamp):
        return str(user.pk) + timestamp + str(user.confirmed_email)

account_activation_token = AccountActivationTokenGenerator()
