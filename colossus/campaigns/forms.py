from django import forms
from django.core.mail import send_mail
from django.utils.translation import gettext, gettext_lazy as _

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

    def send(self, campaign):
        email_address = self.cleaned_data.get('email')
        kwargs = {
            'subject': '[%s] %s' % (gettext('Test'), campaign.email.subject),
            'message': campaign.email.render_text(subscriber=None),
            'from_email': campaign.email.get_from(),
            'recipient_list': [email_address,],
            'fail_silently': False,
            'html_message': campaign.email.render_html(subscriber=None)
        }
        send_mail(**kwargs)
