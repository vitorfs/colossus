import csv
from io import TextIOWrapper

from django import forms
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email

import pytz

from colossus.apps.subscribers.constants import Status
from colossus.apps.subscribers.models import Subscriber

from .models import MailingList


class CSVImportSubscribersForm(forms.Form):
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
                    status=Status.SUBSCRIBED,
                    mailing_list_id=mailing_list_id
                )
                subscribers.append(subscriber)
            else:
                continue
        Subscriber.objects.bulk_create(subscribers)
        mailing_list.update_subscribers_count()


class PasteImportSubscribersForm(forms.Form):
    emails = forms.CharField(
        label=_('Paste email addresses'),
        help_text=_('One email per line, or separated by comma. Duplicate emails will be supressed.'),
        widget=forms.Textarea()
    )
    status = forms.ChoiceField(
        label=_('Assign status to subscriber'),
        choices=Status.CHOICES,
        initial=Status.SUBSCRIBED,
        widget=forms.Select(attrs={'class': 'w-50'})
    )

    def clean(self):
        cleaned_data = super().clean()
        emails = self.cleaned_data.get('emails', '')
        emails = emails.replace(',', '\n').splitlines()
        cleaned_emails = dict()
        for email in emails:
            email = email.strip()
            validate_email(email)
            cleaned_emails[email.lower()] = email
        cleaned_data['emails'] = cleaned_emails.values()
        return cleaned_data

    def import_subscribers(self, request, mailing_list_id):
        mailing_list = MailingList.objects.get(pk=mailing_list_id)
        emails = self.cleaned_data.get('emails')
        status = self.cleaned_data.get('status')
        with transaction.atomic():
            for email in emails:
                subscriber, created = Subscriber.objects.get_or_create(
                    email__iexact=email,
                    mailing_list=mailing_list,
                    defaults={
                        'email': email,
                    }
                )
                if created:
                    pass
                subscriber.status = status
                subscriber.update_date = timezone.now()
                subscriber.save()
