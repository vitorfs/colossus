from django import template
from django.utils.html import mark_safe

from ..models import Subscriber


register = template.Library()


@register.filter
def status_badge(subscriber):
    css_classes = {
        Subscriber.PENDING: 'badge-warning',
        Subscriber.SUBSCRIBED: 'badge-success',
        Subscriber.UNSUBSCRIBED: 'badge-danger',
        Subscriber.CLEANED: 'badge-secondary',
    }
    html = '<span class="badge %s">%s</span>' % (css_classes[subscriber.status], subscriber.get_status_display())
    return mark_safe(html)
