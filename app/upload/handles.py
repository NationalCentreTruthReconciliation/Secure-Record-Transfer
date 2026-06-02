"""Opaque per-wizard upload handles.

This module provides a small server-side mapping between opaque handles and :class:`UploadSession`
instances. The mapping is stored in the authenticated user's Django session.

This allows the frontend to refer to an active upload session by an opaque handle without ever
seeing the underlying :attr:`UploadSession.token`. The security model is analogous to Django's CSRF
token: an opaque value the client echoes back, validated against per-session server state.
"""

import time
from typing import Optional
from uuid import uuid4

from django.http import HttpRequest

from .models import UploadSession

SESSION_KEY = "upload_handles"

#: How long a handle remains valid without being re-registered or resolved.
#: One hour by default — long enough for normal upload flows, short enough that
#: a leaked handle becomes useless quickly.
HANDLE_TTL_SECONDS = 60 * 60


def _get_handles_for_session(request: HttpRequest) -> dict[str, dict]:
    """Return the available handles for the given request's session."""
    return request.session.get(SESSION_KEY, {})


def _prune_expired(handles: dict[str, dict], now: float) -> dict[str, dict]:
    """Drop any entries whose timestamp is older than the TTL."""
    return {h: entry for h, entry in handles.items() if now - entry["ts"] <= HANDLE_TTL_SECONDS}


def _save_handles_for_session(request: HttpRequest, handles: dict[str, dict]) -> None:
    """Save the given handles to the request's session."""
    request.session[SESSION_KEY] = handles
    request.session.modified = True


def register_handle(request: HttpRequest, upload_session: UploadSession) -> str:
    """Register an upload session against an opaque handle in the user's session.

    If a (non-expired) handle already exists for this upload session, that handle is returned and
    its timestamp is refreshed. Otherwise, a fresh handle is generated.

    Expired entries are pruned opportunistically.

    Args:
        request: The incoming HTTP request whose ``request.session`` will store the handle mapping.
        upload_session: The upload session to register.

    Returns:
        The opaque handle string that should be sent to the client.
    """
    now = time.time()
    handles = _prune_expired(_get_handles_for_session(request), now)

    for existing_handle, entry in handles.items():
        if entry["sid"] == upload_session.pk:
            entry["ts"] = now
            _save_handles_for_session(request, handles)
            return existing_handle

    handle = uuid4().hex
    handles[handle] = {"sid": upload_session.pk, "ts": now}
    _save_handles_for_session(request, handles)
    return handle


def resolve_handle(request: HttpRequest, handle: str) -> Optional[UploadSession]:
    """Resolve a handle back to an :class:`UploadSession`.

    The lookup is constrained to upload sessions owned by the authenticated user, so even if a
    handle is leaked across users it cannot be used to access another user's session. The handle's
    timestamp is refreshed on every successful resolution so active uploads keep it alive.

    Args:
        request: The incoming HTTP request.
        handle: The opaque handle previously returned by :func:`register_handle`.

    Returns:
        The matching :class:`UploadSession`, or ``None`` if the handle is unknown, expired, or its
        session does not belong to the user.
    """
    if not handle:
        return None

    now = time.time()
    handles = _get_handles_for_session(request)

    # If the handle doesn't exist, return None
    entry = handles.get(handle)
    if entry is None:
        return None

    # If the handle expired, delete it and return None
    if now - entry["ts"] > HANDLE_TTL_SECONDS:
        handles.pop(handle, None)
        _save_handles_for_session(request, handles)
        return None

    # If the handle does not correspond to an upload session, return None
    session = UploadSession.objects.filter(pk=entry["sid"], user=request.user).first()
    if session is None:
        return None

    # Refresh last interaction time on entry
    entry["ts"] = now
    _save_handles_for_session(request, handles)
    return session
