import logging
import uuid
from typing import Optional

from django.conf import settings
from django.conf.global_settings import (
    EMAIL_HOST, EMAIL_HOST_PASSWORD, EMAIL_HOST_USER, EMAIL_PORT,
    EMAIL_USE_TLS,
)
from django.contrib.gis.geoip2 import GeoIP2
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import get_connection
from django.http import HttpRequest
from django.urls import reverse

from geoip2.errors import AddressNotFoundError

from colossus.apps.core.models import City, Country

logger = logging.getLogger(__name__)


def get_client_ip(request: HttpRequest) -> str:
    """
    Inspects an HTTP Request object and try to determine the client's IP
    address.

    First look for the "HTTP_X_FORWARDED_FOR" header. Note that due to
    application server configuration this value may contain a list of IP
    addresses. If that's the case, return the first IP address in the list.

    The result may not be 100% correct in some cases. Known issues with Heroku
    service:
    https://stackoverflow.com/questions/18264304/

    If there is no "HTTP_X_FORWARDED_FOR" header, falls back to "REMOTE_ADDR"

    :param request: An HTTP Request object
    :return: The client IP address extracted from the HTTP Request
    """
    x_forwarded_for: Optional[str] = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ip_address_key(group: str, request: HttpRequest) -> str:
    """
    Wrapper function to be able to use the client's IP address as a key with
    django-ratelimit decorator.

    The group parameter has no effect, it is here because the ratelimit
    decorator tries to pass a group as first parameter to a callable key.

    :param group: A group of rate limits to count together.
    :param request: A Django HTTP Request object
    :return: The client IP address extracted from the HTTP Request
    """
    return get_client_ip(request)


def get_location(ip_address: str) -> Optional[City]:
    """
    Searches for the country and city of a given IP address using Django's
    GeoIP2 library.

    :param ip_address: An IP address in string format
    :return: A City instance representing the location of the IP address, or
             None if not found.
    """
    geoip2 = GeoIP2()
    city = None
    try:
        geodata = geoip2.city(ip_address)
        if geodata.get('country_code') is not None:
            country, created = Country.objects.get_or_create(code=geodata['country_code'], defaults={
                'name': geodata['country_name']
            })
            if geodata.get('city') is not None:
                city, created = City.objects.get_or_create(name=geodata['city'], country=country)
    except AddressNotFoundError:
        logger.warning('Address not found for ip_address = "%s"' % ip_address)
    return city


def is_uuid(uuid_value: str) -> bool:
    try:
        uuid.UUID(uuid_value)
        return True
    except ValueError:
        return False


def get_absolute_url(urlname: str, kwargs: dict = None) -> str:
    """
    Build an absolute URL for a given urlname. Used when URLs will be exposed
    to the external world (e.g. unsubscribe link in an email).

    :param urlname: Name of the URL pattern
    :param kwargs: Dictionary of necessary arguments to reverse the urlname
    :return: The absolute URL to a given internal URL
    """
    protocol = 'https' if settings.COLOSSUS_HTTPS_ONLY else 'http'
    site = get_current_site(request=None)
    path = reverse(urlname, kwargs=kwargs)
    absolute_url = '%s://%s%s' % (protocol, site.domain, path)
    return absolute_url


def get_campaign_connection(campaign=None, *args, **kwargs):
    if not campaign:
        return get_connection()
    smtp_username = campaign.mailing_list.smtp_username or EMAIL_HOST_USER
    smtp_password = campaign.mailing_list.smtp_password or EMAIL_HOST_PASSWORD
    smtp_host = campaign.mailing_list.smtp_host or EMAIL_HOST
    smtp_port = campaign.mailing_list.smtp_port or EMAIL_PORT
    use_tls = campaign.mailing_list.smtp_use_tls or EMAIL_USE_TLS
    use_ssl = campaign.mailing_list.smtp_use_ssl
    timeout = campaign.mailing_list.smtp_timeout
    smtp_ssl_keyfile = campaign.mailing_list.smtp_ssl_keyfile
    smtp_ssl_certfile = campaign.mailing_list.smtp_ssl_certfile
    connection = get_connection(host=smtp_host,
                                port=smtp_port,
                                username=smtp_username,
                                password=smtp_password
                                )
    if use_tls:
        connection.use_tls = use_tls
    if timeout:
        connection.timeout = timeout
    if use_ssl and smtp_ssl_certfile and smtp_ssl_keyfile:
        connection.use_ssl = use_ssl
        connection.ssl_keyfile = smtp_ssl_keyfile
        connection.ssl_certfile = smtp_ssl_certfile

    return connection
