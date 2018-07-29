from django.contrib.gis.geoip2 import GeoIP2

from geoip2.errors import AddressNotFoundError

from colossus.apps.core.models import City, Country


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ip_address_key(group, request):
    return get_client_ip(request)


def get_location(ip_address):
    geoip2 = GeoIP2()
    city = None
    try:
        geodata = geoip2.city(ip_address)
        if 'country_code' in geodata:
            country, created = Country.objects.get_or_create(code=geodata['country_code'], defaults={
                'name': geodata['country_name']
            })
            if 'city' in geodata:
                city, created = City.objects.get_or_create(name=geodata['city'], country=country)
    except AddressNotFoundError:
        pass
    return city
