from django import template
from django.utils.html import mark_safe

from .. import constants


register = template.Library()


@register.filter
def campaign_status_badge(campaign):
    css_classes = {
        constants.SENT: 'badge-primary',
        constants.SCHEDULED: 'badge-warning',
        constants.DRAFT: 'badge-secondary',
        constants.TRASH: 'badge-danger',
    }
    html = '<span class="badge %s badge-pill">%s</span>' % (css_classes[campaign.status], campaign.get_status_display())
    return mark_safe(html)
