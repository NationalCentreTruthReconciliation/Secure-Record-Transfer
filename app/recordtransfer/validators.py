from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from recordtransfer.models import User


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


class CharacterCategoriesValidator:
    """Require at least N of the defined character categories.
    Categories used here:
    - Uppercase (A-Z)
    - Lowercase (a-z)
    - Digits (0-9)
    - Special characters from the allowed set: _ # % ( ) . ^ { } !.
    """

    def __init__(self, allowed_specials: str = "_#%().^{}!", required_categories: int = 3):
        self.allowed_specials = allowed_specials
        self.required_categories = required_categories

    def validate(self, password: str, user: User | None = None) -> None:
        """Validate that the password contains at least the required number of character
        categories.
        """
        pwd = password or ""
        has_upper = any(c.isupper() for c in pwd)
        has_lower = any(c.islower() for c in pwd)
        has_digit = any(c.isdigit() for c in pwd)
        has_special = any(c in self.allowed_specials for c in pwd)
        count = sum([has_upper, has_lower, has_digit, has_special])
        if count < self.required_categories:
            raise ValidationError(
                _(
                    "This password must contain at least three of the following: uppercase, lowercase, "
                    "numbers, or one of these special characters: %(specials)s"
                ),
                code="password_not_enough_categories",
                params={"specials": self.allowed_specials},
            )

    def get_help_text(self) -> str:
        """Return help text describing the required character categories for the password."""
        return _(
            "Your password must include at least three of the following types: uppercase, lowercase, "
            "numbers, or one of these special characters: _ # % ( ) . ^ { } !"
        )


class PasswordHistoryValidator:
    """Ensure the new password is different from the user's previous N passwords."""

    def __init__(self, history_depth: int = 5):
        self.history_depth = history_depth

    def validate(self, password: str, user: User | None = None) -> None:
        """Validate that the password is not in the user's recent password history."""
        if not user or not user.pk or not password:
            return
        # Import here to avoid circular imports
        from django.contrib.auth.hashers import check_password

        from recordtransfer.models import PasswordHistory

        # First check if the new password is the same as the current password
        if user.password and check_password(password, user.password):
            raise ValidationError(
                _("Your new password cannot be the same as your current password."),
                code="password_same_as_current",
            )

        # Then check against password history
        recent_hashes = PasswordHistory.get_recent_password_hashes(
            user=user, limit=self.history_depth
        )
        if any(check_password(password, old_hash) for old_hash in recent_hashes):
            raise ValidationError(
                _("You cannot reuse your previous %(n)d passwords."),
                code="password_in_history",
                params={"n": self.history_depth},
            )

    def get_help_text(self) -> str:
        """Return help text describing the password history requirement."""
        return _("Your password must be different from your previous five passwords.")


class UserAttributeContainsValidator:
    """Reject passwords that contain the full first name, last name, or username
    (case-insensitive). Email is intentionally ignored.
    """

    def __init__(self, user_attributes: tuple[str, ...] | None = None):
        # Only check whole attribute values for these fields; do not check email
        self.user_attributes = user_attributes or ("username", "first_name", "last_name")

    def get_user_attribute_values(self, user: User) -> list[str]:
        """Get the values of the user attributes."""
        attribute_values_lower: list[str] = []
        for attribute_name in self.user_attributes:
            attribute_value = getattr(user, attribute_name, None)
            if not attribute_value:
                continue
            attribute_value_lower = str(attribute_value).strip().lower()
            if attribute_value_lower:
                attribute_values_lower.append(attribute_value_lower)
        return attribute_values_lower

    def validate(self, password: str, user: User | None = None) -> None:
        """Validate that the password does not contain the user's first name, last name, or username."""
        if not user or not password:
            return
        password_lower = (password or "").lower()
        for attribute_value_lower in self.get_user_attribute_values(user):
            if attribute_value_lower and attribute_value_lower in password_lower:
                from django.core.exceptions import ValidationError
                from django.utils.translation import gettext as _

                raise ValidationError(
                    _("Your password cannot contain your first name, last name, or username."),
                    code="password_contains_user_attribute",
                )

    def get_help_text(self) -> str:
        """Return help text describing the user attribute requirement."""
        return _("Your password cannot contain your first name, last name, or username.")
