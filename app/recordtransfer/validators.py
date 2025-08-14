from __future__ import annotations

from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.translation import format_lazy, ngettext_lazy
from django.utils.translation import gettext as _

from recordtransfer.models import User


class LengthRangeValidator:
    """Validate that a password length falls within an inclusive range.

    Django ships a MinimumLengthValidator but does not enforce an upper bound.
    """

    def __init__(self, min_length: int = 10, max_length: int = 30):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, password: str) -> None:
        """Validate that the password length is within the specified min and max range."""
        length = len(password or "")
        if length < self.min_length:
            raise ValidationError(
                _("This password is too short. It must contain at least %(num)s characters.")
                % {"num": self.min_length},
                code="password_too_short",
            )
        if length > self.max_length:
            raise ValidationError(
                _("This password is too long. It must contain at most %(num)s characters.")
                % {"num": self.max_length},
                code="password_too_long",
            )

    def get_help_text(self) -> str:
        """Return help text describing the required password length range."""
        return _("Your password must be between %(num)s and %(num2)s characters long.") % {
            "num": self.min_length,
            "num2": self.max_length,
        }


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

    def validate(self, password: str) -> None:
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
                format_lazy(
                    ngettext_lazy(
                        "This password must contain one of the following: uppercase, lowercase, numbers, or one of these special characters: {specials}",
                        "This password must contain at least {num} of the following: uppercase, lowercase, numbers, or one of these special characters: {specials}",
                        self.required_categories,
                    ),
                    num=self.required_categories,
                    specials=self.allowed_specials,
                ),
                code="password_not_enough_categories",
            )

    def get_help_text(self) -> str:
        """Return help text describing the required character categories for the password."""
        return format_lazy(
            ngettext_lazy(
                "Your password must include one of the following types: uppercase, lowercase, numbers, or one of these special characters: {specials}",
                "Your password must include at least {num} of the following types: uppercase, lowercase, numbers, or one of these special characters: {specials}",
                self.required_categories,
            ),
            num=self.required_categories,
            specials=self.allowed_specials,
        )


class PasswordHistoryValidator:
    """Ensure the new password is different from the user's previous N passwords."""

    def __init__(self, history_depth: int = 5):
        self.history_depth = history_depth

    def validate(self, password: str, user: User) -> None:
        """Validate that the password is not in the user's recent password history."""
        if not user or not user.pk or not password:
            return

        # First check if the new password is the same as the current password
        if user.password and check_password(password, user.password):
            raise ValidationError(
                _("Your new password cannot be the same as your current password."),
                code="password_same_as_current",
            )

        # Then check against password history
        recent_hashes = user.past_password_hashes(self.history_depth)
        if any(check_password(password, old_hash) for old_hash in recent_hashes):
            raise ValidationError(
                format_lazy(
                    ngettext_lazy(
                        "You cannot reuse your previous password.",
                        "You cannot reuse your previous {num} passwords.",
                        self.history_depth,
                    ),
                    num=self.history_depth,
                ),
                code="password_in_history",
            )

    def get_help_text(self) -> str:
        """Return help text describing the password history requirement."""
        return format_lazy(
            ngettext_lazy(
                "Your password must be different from your previous password.",
                "Your password must be different from your previous {num} passwords.",
                self.history_depth,
            ),
            num=self.history_depth,
        )


class ContainsUserNameValidator:
    """Reject passwords that contain the full first name, last name, or username
    (case-insensitive). Email is intentionally ignored.
    """

    user_attributes: tuple = ("username", "first_name", "last_name")

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
        """Validate that the password does not contain the user's
        first name, last name, or username.
        """
        if not user or not password:
            return
        password_lower = (password or "").lower()
        for attribute_value_lower in self.get_user_attribute_values(user):
            if attribute_value_lower and attribute_value_lower in password_lower:
                raise ValidationError(
                    _("Your password cannot contain your first name, last name, or username."),
                    code="password_contains_user_attribute",
                )

    def get_help_text(self) -> str:
        """Return help text describing the user attribute requirement."""
        return _("Your password cannot contain your first name, last name, or username.")
