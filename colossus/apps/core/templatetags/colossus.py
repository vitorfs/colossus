from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def qs(context, **kwargs):
    '''
    Returns the URL-encoded querystring for the current page,
    updating the params with the key/value pairs passed to the tag.

    E.g: given the querystring ?foo=1&bar=2
    {% query_transform bar=3 %} outputs ?foo=1&bar=3
    {% query_transform foo='baz' %} outputs ?foo=baz&bar=2
    {% query_transform foo='one' bar='two' baz=99 %} outputs ?foo=one&bar=two&baz=99

    A RequestContext is required for access to the current querystring.

    Original source by benbacardi
    https://gist.github.com/benbacardi/d6cd0fb8c85e1547c3c60f95f5b2d5e1
    '''
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value:
            query[key] = value
    return query.urlencode()


@register.simple_tag
def dict(dictionary, key):
    return dictionary[key]


@register.filter
def percent(value):
    percentage = round(value * 100, 1)
    return f'{percentage}%'
