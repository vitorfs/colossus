from django import forms
from django.core.mail import send_mail
from django.utils.translation import gettext, gettext_lazy as _

class CampaignTestEmailForm(forms.Form):
    email = forms.EmailField(label=_('Email address'))

    class Meta:
        fields = ('email',)

    def send(self, campaign):
        email_address = self.cleaned_data.get('email')
        kwargs = {
            'subject': '[%s] %s' % (gettext('Test'), campaign.email.subject),
            'message': campaign.email.content_text,
            'from_email': campaign.email.get_from(),
            'recipient_list': [email_address,],
            'fail_silently': False,
            'html_message': campaign.email.content
        }
        send_mail(**kwargs)
