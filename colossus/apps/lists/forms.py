import csv
from io import TextIOWrapper
from smtplib import SMTPAuthenticationError

from django import forms
from django.core.exceptions import ValidationError
from django.core.mail.backends.smtp import EmailBackend
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _

import pytz

from colossus.apps.subscribers.constants import ActivityTypes, Status
from colossus.apps.subscribers.models import Subscriber

from .models import MailingList, SubscriberImport


class CSVImportSubscribersForm(forms.Form):
    upload_file = forms.FileField(help_text=_('Supported file type: .csv'))
    status = forms.ChoiceField(
        label=_('Assign status to subscriber'),
        choices=Status.CHOICES,
        initial=Status.SUBSCRIBED,
        widget=forms.Select(attrs={'class': 'w-50'})
    )

    def import_subscribers(self, request, mailing_list_id):
        mailing_list = MailingList.objects.get(pk=mailing_list_id)
        upload_file = self.cleaned_data.get('upload_file')
        status = self.cleaned_data.get('status')
        csvfile = TextIOWrapper(upload_file, encoding=request.encoding)
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        subscribers = list()
        for row in reader:
            if '@' in row[0]:
                email = Subscriber.objects.normalize_email(row[0])
                name = row[1].strip()
                optin_ip_address = row[2].strip()
                optin_date = timezone.datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
                optin_date = pytz.utc.localize(optin_date)
                confirm_ip_address = row[4]
                confirm_date = timezone.datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S')
                confirm_date = pytz.utc.localize(confirm_date)
                subscriber = Subscriber(
                    email=email,
                    name=name,
                    optin_ip_address=optin_ip_address,
                    optin_date=optin_date,
                    confirm_ip_address=confirm_ip_address,
                    confirm_date=confirm_date,
                    status=status,
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
        help_text=_('One email per line, or separated by comma. Duplicate emails will be suppressed.'),
        widget=forms.Textarea()
    )
    status = forms.ChoiceField(
        label=_('Assign status to subscriber'),
        choices=Status.CHOICES,
        initial=Status.SUBSCRIBED,
        widget=forms.Select(attrs={'class': 'w-50'})
    )

    def clean(self):
        """
        First replace the commas with new lines, then split the text by lines.
        This is done so to accept both a string of emails separated by new lines
        or by commas.
        Normalize the email addresses inside a loop and call the email validator
        for each email.
        Emails are added to a dictionary so to remove the duplicates and at the
        same time preserve the case informed. The dictionary key is the lower case
        of the email, and the value is its original form.
        After the code iterates through all the emails, return only the values of
        the dictionary.
        """
        cleaned_data = super().clean()
        emails = self.cleaned_data.get('emails', '')
        emails = emails.replace(',', '\n').splitlines()
        cleaned_emails = dict()
        for email in emails:
            email = Subscriber.objects.normalize_email(email)
            validate_email(email)
            cleaned_emails[email.lower()] = email
        cleaned_data['emails'] = cleaned_emails.values()
        return cleaned_data

    def import_subscribers(self, mailing_list):
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
                    subscriber.create_activity(ActivityTypes.IMPORTED)
                subscriber.status = status
                subscriber.update_date = timezone.now()
                subscriber.save()
            mailing_list.update_subscribers_count()


class ColumnsMappingForm(forms.ModelForm):
    FIELDS = {
        'email': _('Email address'),
        'name': _('Name'),
        'open_rate': _('Open rate'),
        'click_rate': _('Click rate'),
        'update_date': _('Update date'),
        'optin_ip_address': _('Opt-in IP address'),
        'optin_date': _('Opt-in date'),
        'confirm_ip_address': _('Confirm IP address'),
        'confirm_date': _('Confirm date')
    }

    class Meta:
        model = SubscriberImport
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = (('', _('Select...'),),) + tuple(self.FIELDS.items())
        sample_data = self.instance.get_rows(limit=1)[0]
        self.headings = self.instance.get_headings()
        columns_mapping = self.instance.get_columns_mapping()
        if not columns_mapping:
            columns_mapping = list(self.FIELDS.keys())
        self._key = lambda i: '__column_%s' % i
        for index, heading in enumerate(self.headings):
            self.fields[self._key(index)] = forms.ChoiceField(
                label=heading,
                required=False,
                choices=choices,
                help_text=_('Sample data: "%s"') % sample_data[index]
            )
            try:
                self.initial[self._key(index)] = columns_mapping[index]
            except (KeyError, IndexError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        for index, heading in enumerate(self.headings):
            if cleaned_data.get(self._key(index), '') == 'email':
                break
        else:
            email_column_required = ValidationError(
                gettext('At least one column should map to "Email address" field.'),
                code='email_column_required'
            )
            self.add_error(None, email_column_required)
        return cleaned_data

    def save(self, commit=True):
        subscriber_import = super().save(commit=False)
        mapping = dict()
        for index, heading in enumerate(self.headings):
            value = self.cleaned_data.get(self._key(index), '')
            if value:
                mapping[index] = value
        subscriber_import.set_columns_mapping(mapping)
        if commit:
            subscriber_import.save()
        return subscriber_import


class MailingListSMTPForm(forms.ModelForm):
    class Meta:
        model = MailingList
        fields = ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_use_tls', 'smtp_use_ssl',
                  'smtp_timeout', 'smtp_ssl_keyfile', 'smtp_ssl_certfile')

    def clean(self):
        cleaned_data = super().clean()
        smtp_email_backend = EmailBackend(
            host=cleaned_data.get('smtp_host'),
            port=cleaned_data.get('smtp_port'),
            username=cleaned_data.get('smtp_username'),
            password=cleaned_data.get('smtp_password'),
            use_tls=cleaned_data.get('smtp_use_tls'),
            fail_silently=False,
            use_ssl=cleaned_data.get('smtp_use_ssl'),
            timeout=cleaned_data.get('smtp_timeout'),
            ssl_keyfile=cleaned_data.get('smtp_ssl_keyfile'),
            ssl_certfile=cleaned_data.get('smtp_ssl_certfile')
        )
        try:
            smtp_email_backend.open()
        except ConnectionRefusedError:
            raise ValidationError(_('Connection refused'), code='connection_refused')
        except SMTPAuthenticationError as err:
            raise ValidationError(str(err), code='auth_error')
        return cleaned_data
