from smtplib import SMTPAuthenticationError
from typing import Dict, List

from django import forms
from django.core.exceptions import ValidationError
from django.core.mail.backends.smtp import EmailBackend
from django.db import transaction
from django.forms import BoundField
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _

from colossus.apps.lists.constants import ImportFields, ImportStatus
from colossus.apps.lists.tasks import import_subscribers
from colossus.apps.subscribers.constants import ActivityTypes, Status
from colossus.apps.subscribers.fields import MultipleEmailField
from colossus.apps.subscribers.models import Domain, Subscriber, Tag

from .models import MailingList, SubscriberImport


class ConfirmSubscriberImportForm(forms.ModelForm):
    """
    Form used to define what status will be assigned to the imported subscribers
    and the import strategy (update or create, or create only).

    After saving the form, place the csv import file in the queue to be
    processed by a Celery task.
    """
    submit = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = SubscriberImport
        fields = ('subscriber_status', 'strategy', 'submit')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        choices = (('', _('--- Ignore column ---'),),) + ImportFields.CHOICES
        self.headings = self.instance.get_headings()
        columns_mapping = self.instance.get_columns_mapping()
        if not columns_mapping:
            columns_mapping = [choice[0] for choice in ImportFields.CHOICES]
        for index, heading in enumerate(self.headings):
            self.fields[self._field_key(index)] = forms.ChoiceField(
                label=heading,
                required=False,
                choices=choices
            )
            try:
                self.initial[self._field_key(index)] = columns_mapping[index]
            except (KeyError, IndexError):
                pass

    def _field_key(self, index: int) -> str:
        """
        Utility method to compose the dynamic mapping columns fields

        :param index: Zero-based index. Number of the column in the CSV file
        :return: Unique field name for column mapping fields.
        """
        return f'__column_{index}'

    def clean(self) -> Dict:
        """
        Validate the form data and check if there is at least one field mapping
        back to the email field.

        The email field is the main subscriber identifier and is the only
        required field that must be in the CSV file.

        :return: Dictionary with cleaned form data
        """
        cleaned_data = super().clean()

        for index, heading in enumerate(self.headings):
            column_field_name = self._field_key(index)
            if cleaned_data.get(column_field_name, '') == 'email':
                break
        else:
            email_column_required = ValidationError(
                gettext('At least one column should map to "Email address" field.'),
                code='email_column_required'
            )
            self.add_error(None, email_column_required)

        return cleaned_data

    def save(self, commit: bool = True) -> SubscriberImport:
        """
        Saves the form instance and place the imported CSV file in a queue to
        be processed.

        Please note that if the save method is called with commit = False, the
        queue() method must be called manually after the object is finally
        saved.

        Also note that the queue() method will only have effect if the object
        status is equal to ImportStatus.QUEUED.

        :param commit: Flag to determine if the object will be saved or not.
        :return: SubscriberImport instance saved by the form
        """
        subscriber_import: SubscriberImport = super().save(commit=False)

        mapping = dict()
        for index, heading in enumerate(self.headings):
            column_field_name = self._field_key(index)
            value = self.cleaned_data.get(column_field_name, '')
            if value:
                mapping[index] = value

        subscriber_import.set_columns_mapping(mapping)

        submit = self.cleaned_data.get('submit')
        if submit == 'import':
            subscriber_import.status = ImportStatus.QUEUED

        if commit:
            subscriber_import.save()
            if subscriber_import.status == ImportStatus.QUEUED:
                self.queue()

        return subscriber_import

    def column_mapping_fields(self) -> List[BoundField]:
        """
        Convenience method to be used in the front-end to render import template
        table.

        :return: List of BoundField objects that are visible and part of the
                 columns mapping fields.
        """
        return [field for field in self.visible_fields() if field.name.startswith('__column_')]

    def import_settings_fields(self) -> List[BoundField]:
        """
        Convenience method to be used in the front-end to list visible fields
        not related to columns mapping.

        :return: List of BoundField objects that are visible and not part of the
                 columns mapping fields.
        """
        return [field for field in self.visible_fields() if not field.name.startswith('__column_')]

    def queue(self):
        """
        Place the import file in a queue to be processed by a Celery task
        """
        import_subscribers.delay(self.instance.pk)


class PasteImportSubscribersForm(forms.Form):
    emails = MultipleEmailField(
        label=_('Paste email addresses'),
        help_text=_('One email per line, or separated by comma. Duplicate emails will be suppressed.'),
    )
    status = forms.ChoiceField(
        label=_('Assign status to subscriber'),
        choices=Status.CHOICES,
        initial=Status.SUBSCRIBED,
        widget=forms.Select(attrs={'class': 'w-50'})
    )

    def import_subscribers(self, mailing_list):
        cached_domains = dict()
        emails = self.cleaned_data.get('emails')
        status = self.cleaned_data.get('status')

        with transaction.atomic():
            for email in emails:

                email_name, domain_part = email.rsplit('@', 1)
                domain_name = '@' + domain_part

                try:
                    domain = cached_domains[domain_name]
                except KeyError:
                    domain, created = Domain.objects.get_or_create(name=domain_name)
                    cached_domains[domain_name] = domain

                subscriber, created = Subscriber.objects.get_or_create(
                    email__iexact=email,
                    mailing_list=mailing_list,
                    defaults={
                        'email': email,
                        'domain': domain
                    }
                )
                if created:
                    subscriber.create_activity(ActivityTypes.IMPORTED)
                subscriber.status = status
                subscriber.update_date = timezone.now()
                subscriber.save()
            mailing_list.update_subscribers_count()


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


class BulkTagForm(forms.Form):
    tag = forms.ModelChoiceField(queryset=Tag.objects.none())
    emails = MultipleEmailField(
        label=_('Paste email addresses'),
        help_text=_('One email per line, or separated by comma. '
                    'Duplicate emails will be suppressed. '
                    'Emails not matching any subscriber will be ignored.')
    )

    def __init__(self, *args, **kwargs):
        self.mailing_list = kwargs.pop('mailing_list')
        super().__init__(*args, **kwargs)
        self.fields['tag'].queryset = self.mailing_list.tags.all()

    @transaction.atomic()
    def tag_subscribers(self) -> int:
        """
        Process the form adding the valid subscribers to the given tag.
        :return: The number of subscribers successfully tagged
        """
        tag = self.cleaned_data.get('tag')
        emails = self.cleaned_data.get('emails')
        success_count = 0
        for email in emails:
            try:
                subscriber = Subscriber.objects.get(mailing_list=self.mailing_list, email__iexact=email)
                subscriber.tags.add(tag)
                success_count += 1
            except Subscriber.DoesNotExist:
                pass
        return success_count
