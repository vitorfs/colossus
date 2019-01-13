from django.utils import timezone

import pytz
from pytz import UnknownTimeZoneError


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                timezone.activate(pytz.timezone(request.user.timezone))
            except UnknownTimeZoneError:
                timezone.deactivate()

        response = self.get_response(request)
        return response
