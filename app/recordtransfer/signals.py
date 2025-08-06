from typing import Any, cast

from django.http import HttpRequest
from django.utils import translation

from recordtransfer.constants import SessionFlags
from recordtransfer.models import User


def add_logged_in_flag(sender: type, request: HttpRequest, user: User, **kwargs: Any) -> None:
    """Add a temporary session flag for SetLanguageOnLoginMiddleware to use after login."""
    user = cast(User, user)
    if user.language:
        # Activate the language for the current request
        translation.activate(user.language)
        # Set a flag so the middleware knows to set the cookie
        request.session[SessionFlags.JUST_LOGGED_IN] = True
