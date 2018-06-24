from django import forms
from django.utils.translation import gettext_lazy as _

from .api import send_campaign_email_test
from .models import Email
from .utils import get_plain_text_from_html


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


class EmailEditorForm(forms.Form):
    def __init__(self, email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = email
        blocks = email.get_blocks()
        for block_key, block_content in blocks.items():
            self.fields[block_key] = forms.CharField(
                label=_('Block %s' % block_key),
                required=False,
                initial=block_content,
                widget=forms.Textarea()
            )

    def save(self, commit=True):
        self.email.set_blocks(self.cleaned_data)
        if commit:
            self.email.save()
        return self.email
