from django import template
from django.utils.html import mark_safe

from ..constants import ImportStatus

register = template.Library()


@register.filter
def import_status_badge(subscriber_import):
    css_classes = {
        ImportStatus.PENDING: 'badge-warning',
        ImportStatus.QUEUED: 'badge-info',
        ImportStatus.IMPORTING: 'badge-primary',
        ImportStatus.COMPLETED: 'badge-success',
        ImportStatus.ERRORED: 'badge-danger',
        ImportStatus.CANCELED: 'badge-secondary',
    }
    badge_class = css_classes[subscriber_import.status]
    badge_text = subscriber_import.get_status_display()
    html = '<span class="badge %s badge-pill">%s</span>' % (badge_class, badge_text)
    return mark_safe(html)
