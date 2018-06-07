from django import template
from django.utils.html import mark_safe

from .. import constants


register = template.Library()


@register.filter
def status_badge(subscriber):
    css_classes = {
        constants.PENDING: 'badge-warning',
        constants.SUBSCRIBED: 'badge-success',
        constants.UNSUBSCRIBED: 'badge-danger',
        constants.CLEANED: 'badge-secondary',
    }
    html = '<span class="badge %s badge-pill">%s</span>' % (css_classes[subscriber.status], subscriber.get_status_display())
    return mark_safe(html)
