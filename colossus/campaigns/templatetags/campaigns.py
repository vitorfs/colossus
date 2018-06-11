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
    badge_class = css_classes[campaign.status]
    badge_text = campaign.get_status_display()
    html = '<span class="badge %s badge-pill">%s</span>' % (badge_class, badge_text)
    return mark_safe(html)
