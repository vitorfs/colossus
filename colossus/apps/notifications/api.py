import json

from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from colossus.apps.lists.models import MailingList


def render_list_cleaned(notification):
    data = json.loads(notification.text)
    mailing_list = MailingList.objects.values('id', 'name').get(pk=data['mailing_list_id'])
    data['mailing_list_name'] = escape(mailing_list['name'])
    data['url'] = reverse('lists:list', kwargs={'pk': mailing_list['id']})
    message = _('<strong>Cleaned</strong> %(cleaned)s emails from mailing list %(mailing_list_name)s') % data
    return mark_safe(message)
