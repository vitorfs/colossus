from django import forms
from django.core.mail import send_mail
from django.utils.translation import gettext, gettext_lazy as _

from .api import send_campaign_email_test
from .markup import get_plain_text_from_html
from .models import Email


class DesignEmailForm(forms.ModelForm):
    class Meta:
        model = Email
        fields = ('content',)

    def save(self, commit=True):
        email = super().save(commit=False)
        email.content_text = get_plain_text_from_html(email.content)
        if commit:
            email.save()
        return email


class PlainTextEmailForm(forms.ModelForm):
    class Meta:
        model = Email
        fields = ('content_text',)


class CampaignTestEmailForm(forms.Form):
    email = forms.EmailField(label=_('Email address'))

    class Meta:
        fields = ('email',)

    def send(self, email):
        recipient_email = self.cleaned_data.get('email')
        send_campaign_email_test(email, recipient_email)
