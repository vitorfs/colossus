from django import forms
from django.core.exceptions import ValidationError
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.utils.translation import ugettext as _
from django.template import loader

from colossus.mailing.models import Subscriber, Token


class SubscribeForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': _('Your Name')}),
        max_length=150,
        label=_('Name')
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': _('your@email.com')}),
        label=_('Email Address'),
        help_text=_('We\'ll never share your email with anyone else.')
    )

    class Meta:
        fields = ('name', 'email')

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
                _('The email address "%(email)s" is already subscribed to this list.'),
                params={'email': email},
                code='already_subscribed_error'
            )
            self.add_error('email', email_validation_error)
        return cleaned_data

    @transaction.atomic
    def subscribe(self, request):
        email = self.cleaned_data.get('email')
        name = self.cleaned_data.get('name')
        user, created = User.objects.get_or_create(email__iexact=email, defaults={
            'email': email,
            'name': name
        })
        subscriber, created = Subscriber.objects.get_or_create(user=user, mailing_list=self.mailing_list)
        subscriber.status = Subscriber.PENDING
        subscriber.save()

        if not created:
            subscriber.tokens.filter(status=Token.PENDING).update(status=Token.CANCELED)

        token = subscriber.tokens.create(description='confirm_subscription')
        print(token)

        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain
        context = {
            'mailing_list': self.mailing_list,
            'token': token,
            'site_name': site_name,
            'domain': domain,
            'protocol': 'https' if request.is_secure() else 'http',
            'contact_email': 'vitor@simpleisbetterthancomplex.com'

        }

        subject = loader.render_to_string('mailing/confirm_subscription_subject.txt', context)
        subject = ''.join(subject.splitlines())  # Email subject *must not* contain newlines
        body = loader.render_to_string('mailing/confirm_subscription_email.txt', context)

        user.email_user(subject=subject, message=body)

        return subscriber