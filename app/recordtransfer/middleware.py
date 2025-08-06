"""Custom middleware for the recordtransfer app."""

from typing import Callable, cast

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from recordtransfer.constants import SessionFlags
from recordtransfer.models import User


class SaveUserLanguageMiddleware:
    """Middleware to save language preference changes to the User model."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and save language changes."""
        # Get the current language from cookie before processing
        old_language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

        # Process the request
        response = self.get_response(request)
        new_language = None
        if hasattr(response, "cookies") and settings.LANGUAGE_COOKIE_NAME in response.cookies:
            new_language = response.cookies[settings.LANGUAGE_COOKIE_NAME].value

        # Return early if no new language was set or if language hasn't changed
        if not new_language or new_language == old_language:
            return response

        # Save language preference to user if user is authenticated
        if request.user.is_authenticated and hasattr(request.user, "language"):
            user = cast(User, request.user)
            if user.language != new_language:
                user.language = new_language
                user.save(update_fields=["language"])

        return response


class SetLanguageOnLoginMiddleware:
    """Middleware to set language cookie when user logs in with a preferred language."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and set language cookie if needed."""
        response = self.get_response(request)

        # Check if user just logged in and has a language preference
        if (
            request.user.is_authenticated
            and hasattr(request.user, "language")
            and hasattr(request, "session")
            and request.session.get(SessionFlags.JUST_LOGGED_IN)
        ):
            user = cast(User, request.user)
            if user.language:
                # Set the language cookie
                response.set_cookie(
                    settings.LANGUAGE_COOKIE_NAME,
                    user.language,
                    max_age=settings.LANGUAGE_COOKIE_AGE,
                    path=settings.LANGUAGE_COOKIE_PATH,
                    domain=settings.LANGUAGE_COOKIE_DOMAIN,
                    secure=settings.LANGUAGE_COOKIE_SECURE,
                    httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                    samesite=settings.LANGUAGE_COOKIE_SAMESITE,
                )
            # Clear the flag
            del request.session[SessionFlags.JUST_LOGGED_IN]

        return response
