from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django.template.loader import render_to_string


def custom_404(request: HttpRequest) -> HttpResponse:
    """Return custom 404 page."""
    return HttpResponseNotFound(render_to_string("404.html"))


def custom_500(request: HttpRequest) -> HttpResponse:
    """Return custom 500 page."""
    return HttpResponseServerError(render_to_string("500.html"))
