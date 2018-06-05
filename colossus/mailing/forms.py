import csv
from io import TextIOWrapper

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext, gettext_lazy as _
from django.utils import timezone
from django.template import loader

from .models import Subscriber, Token


class SubscribeForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        self.mailing_list = kwargs.pop('mailing_list')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        is_subscribed = Subscriber.objects \
            .filter(email__iexact=email, status=Subscriber.SUBSCRIBED, mailing_list=self.mailing_list) \
            .exists()
        if is_subscribed:
            email_validation_error = ValidationError(
                gettext('The email address "%(email)s" is already subscribed to this list.'),
                params={'email': email},
                code='already_subscribed_error'
            )
            self.add_error('email', email_validation_error)
        return cleaned_data

    @transaction.atomic
    def subscribe(self, request):
        email = self.cleaned_data.get('email')
        subscriber, created = Subscriber.objects.get_or_create(email=email, mailing_list=self.mailing_list)
        subscriber.status = Subscriber.PENDING
        subscriber.save()

        if not created:
            subscriber.tokens.filter(description='confirm_subscription').delete()

        token = subscriber.tokens.create(description='confirm_subscription')

        site_name = self.mailing_list.name
        domain = '127.0.0.1:8000'
        context = {
            'mailing_list': self.mailing_list,
            'token': token,
            'site_name': site_name,
            'domain': domain,
            'protocol': 'https' if request.is_secure() else 'http',
            'contact_email': 'vitor@simpleisbetterthancomplex.com'

        }

        subject = loader.render_to_string('mailing/subscription/confirm_subscription_subject.txt', context)
        subject = ''.join(subject.splitlines())  # Email subject *must not* contain newlines
        body = loader.render_to_string('mailing/subscription/confirm_subscription_email.txt', context)

        subscriber.send_mail(subject=subject, message=body)

        return subscriber


class NewSubscriber(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ('email', 'name')


class ImportSubscribersForm(forms.Form):
    upload_file = forms.FileField(help_text=_('Supported file type: .csv'))

    def import_subscribers(self, request, mailing_list_id):
        upload_file = self.cleaned_data.get('upload_file')
        csvfile = TextIOWrapper(upload_file, encoding=request.encoding)
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        subscribers = list()
        for row in reader:
            if '@' in row[0]:
                subscribers.append(
                    Subscriber(email=row[0],
                               name=row[2],
                               optin_ip_address=row[5],
                               confirm_ip_address=row[7],
                               status=Subscriber.SUBSCRIBED,
                               mailing_list_id=mailing_list_id,
                               date_subscribed=timezone.now())
                )
            else:
                continue
        Subscriber.objects.bulk_create(subscribers)
