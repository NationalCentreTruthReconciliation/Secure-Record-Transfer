"""Utility functions concerning client connection information."""

from django.http import HttpRequest


def get_client_ip_address(request: HttpRequest) -> str:
    """Get the client's IP address from the request."""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "unknown")
    return ip
