from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from recordtransfer.models import PasswordHistory, User


@dataclass
class LengthRangeValidator:
    """Validate that a password length falls within an inclusive range.

    Django ships a MinimumLengthValidator but does not enforce an upper bound.
    """

    min_length: int = 10
    max_length: int = 30

    def validate(self, password: str, user: User | None = None) -> None:
        """Validate that the password length is within the specified min and max range."""
        length = len(password or "")
        if length < self.min_length:
            raise ValidationError(
                _(
                    f"This password is too short. It must contain at least {self.min_length} characters."
                ),
                code="password_too_short",
            )
        if length > self.max_length:
            raise ValidationError(
                _(
                    f"This password is too long. It must contain at most {self.max_length} characters."
                ),
                code="password_too_long",
            )

    def get_help_text(self) -> str:
        """Return help text describing the required password length range."""
        return _(
            f"Your password must be between {self.min_length} and {self.max_length} characters long."
        )
