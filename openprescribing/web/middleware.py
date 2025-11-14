# This is a temporary module for use in development
# pragma: no cover file
import base64

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse


class BasicAuthMiddleware:
    """
    Adds HTTP Basic Authentication site-wide

    Additionally, sets auth details in a cookie so they persist beyond browser close.

    Absolutely not for serious auth purposes but useful for low-touch protection of
    staging/demo environments.
    """

    auth_realm = "Protected"
    auth_html = """\
        <!doctype html>
        <title>Authorization Required</title>
        <h1>Authorization Required</h1>
    """
    auth_cookie_name = "basic_auth"
    auth_cookie_max_age = 60 * 60 * 24 * 7

    def __init__(self, get_response):
        self.get_response = get_response
        self.username = getattr(settings, "BASIC_AUTH_USERNAME", "")
        self.password = getattr(settings, "BASIC_AUTH_PASSWORD", "")
        if not self.username or not self.password:
            raise MiddlewareNotUsed()

    def __call__(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth:
            auth = request.COOKIES.get(self.auth_cookie_name, "")

        if self.is_authorized(auth):
            response = self.get_response(request)
            response.set_cookie(
                self.auth_cookie_name,
                auth,
                httponly=True,
                max_age=self.auth_cookie_max_age,
            )
            return response
        else:
            return self.unauthorized_response()

    def is_authorized(self, auth):
        if auth.startswith("Basic "):
            creds = base64.b64decode(auth[6:]).decode()
            user, _, pwd = creds.partition(":")
            return user == self.username and pwd == self.password
        else:
            return False

    def unauthorized_response(self):
        response = HttpResponse(self.auth_html, status=401, content_type="text/html")
        response["WWW-Authenticate"] = f'Basic realm="{self.auth_realm}"'
        return response
