from typing import Any

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def qs(context, **kwargs):
    """
    Returns the URL-encoded querystring for the current page,
    updating the params with the key/value pairs passed to the tag.

    E.g: given the querystring ?foo=1&bar=2
    {% qs bar=3 %} outputs ?foo=1&bar=3
    {% qs foo='baz' %} outputs ?foo=baz&bar=2
    {% qs foo='one' bar='two' baz=99 %} outputs ?foo=one&bar=two&baz=99

    A RequestContext is required for access to the current querystring.

    Original source by benbacardi
    https://gist.github.com/benbacardi/d6cd0fb8c85e1547c3c60f95f5b2d5e1
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value:
            query[key] = str(value)
    return query.urlencode()


@register.filter
def get(collection: Any, key: Any):
    if type(collection) == list or type(collection) == tuple:
        try:
            key = int(key)
            return collection[key]
        except Exception:
            return ''
    elif type(collection) == dict:
        return collection.get(key, '')
    else:
        return ''


@register.filter
def percentage(value):
    return round(value * 100, 1)


@register.filter
def calc_percentage(value, total):
    if total > 0:
        return percentage(value / total)
    return 0.0


@register.filter
def flag(country_code):
    if country_code is not None:
        html = '<span class="flag-icon flag-icon-%s mr-2"></span>' % country_code.lower()
        return mark_safe(html)
    else:
        return ''


@register.filter
def domain_icon(domain):
    domains = {
        '@gmail.com': 'fab fa-google',
        '@hotmail.com': 'fab fa-microsoft',
        '@yahoo.com': 'fab fa-yahoo',
        '@outlook.com': 'fab fa-microsoft',
        '@qq.com': 'fab fa-qq',
        '@icloud.com': 'fab fa-apple',
        '@live.com': 'fab fa-microsoft',
        '@yandex.ru': 'fab fa-yandex'
    }
    if domain in domains:
        icon = domains[domain]
    else:
        icon = 'far fa-envelope'
    return mark_safe('<span class="%s d-inline-block mr-2" style="width: 16px"></span>' % icon)
