import csv
from io import TextIOWrapper

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import pytz

from colossus.subscribers import constants as subscribers_constants
from colossus.subscribers.models import Subscriber

from .models import MailingList


class ImportSubscribersForm(forms.Form):
    upload_file = forms.FileField(help_text=_('Supported file type: .csv'))

    def import_subscribers(self, request, mailing_list_id):
        mailing_list = MailingList.objects.get(pk=mailing_list_id)
        upload_file = self.cleaned_data.get('upload_file')
        csvfile = TextIOWrapper(upload_file, encoding=request.encoding)
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        subscribers = list()
        for row in reader:
            if '@' in row[0]:
                optin_date = timezone.datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
                confirm_date = timezone.datetime.strptime(row[6], '%Y-%m-%d %H:%M:%S')
                subscriber = Subscriber(
                    email=row[0],
                    name=row[2],
                    optin_date=pytz.utc.localize(optin_date),
                    optin_ip_address=row[5],
                    confirm_date=pytz.utc.localize(confirm_date),
                    confirm_ip_address=row[7],
                    status=subscribers_constants.SUBSCRIBED,
                    mailing_list_id=mailing_list_id
                )
                subscribers.append(subscriber)
            else:
                continue
        Subscriber.objects.bulk_create(subscribers)
        mailing_list.update_subscribers_count()
