"""Utility functions for determining the deployed environment."""

import functools

from django.conf import settings


@functools.lru_cache(maxsize=1)
def is_deployed_environment() -> bool:
    """Detect if the app is running in a deployed production environment.

    Returns True if ALLOWED_HOSTS contains any non-localhost/non-127.0.0.1 hosts,
    indicating this is a deployed production environment.
    """
    allowed_hosts = settings.ALLOWED_HOSTS

    # If ALLOWED_HOSTS is ['*'], consider it production
    if "*" in allowed_hosts:
        return True

    # Check if any host is not localhost/127.0.0.1
    for host in allowed_hosts:
        host = host.strip().lower()
        if host not in ["localhost", "127.0.0.1", ""]:
            return True

    return False
