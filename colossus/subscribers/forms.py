from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.template import loader
from django.utils import timezone
from django.utils.translation import gettext

from colossus.utils import get_client_ip

from . import constants
from .models import Subscriber


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
            .filter(email__iexact=email, status=constants.SUBSCRIBED, mailing_list=self.mailing_list) \
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
        subscriber.status = constants.PENDING
        subscriber.optin_ip_address = get_client_ip(request)
        subscriber.optin_date = timezone.now()
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

        subject = loader.render_to_string('subscribers/confirm_subscription_subject.txt', context)
        subject = ''.join(subject.splitlines())  # Email subject *must not* contain newlines
        body = loader.render_to_string('subscribers/confirm_subscription_email.txt', context)

        subscriber.send_mail(subject=subject, message=body)

        return subscriber


class UnsubscribeForm(forms.Form):
    email = forms.EmailField()

    class Meta:
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        self.mailing_list = kwargs.pop('mailing_list')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        is_subscribed = Subscriber.objects.filter(
            email__iexact=email,
            mailing_list=self.mailing_list,
            status=constants.SUBSCRIBED
        )
        if not is_subscribed:
            email_validation_error = ValidationError(
                gettext('The email address "%(email)s" is not subscribed to this list.'),
                params={'email': email},
                code='not_subscribed_error'
            )
            self.add_error('email', email_validation_error)
        return cleaned_data

    def unsubscribe(self, request):
        email = self.cleaned_data.get('email')
        subscriber = Subscriber.objects.get(email=email, mailing_list=self.mailing_list)
        subscriber.unsubscribe(request)
