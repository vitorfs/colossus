from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _

from colossus.apps.subscribers.models import Tag

from .api import send_campaign_email_test
from .constants import CampaignStatus
from .models import Campaign


class CreateCampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ('name',)


class CampaignRecipientsForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ('mailing_list', 'tag')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tag'].queryset = Tag.objects.none()
        if 'tag' in self.data:
            try:
                mailing_list_id = int(self.data.get('mailing_list'))
                self.fields['tag'].queryset = Tag.objects.filter(mailing_list_id=mailing_list_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['tag'].queryset = self.instance.mailing_list.tags.order_by('name')


class ScheduleCampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ('send_date',)
        widgets = {
            'send_date': forms.DateTimeInput(
                attrs={
                    'data-toggle': 'datetimepicker',
                    'data-target': '#id_send_date',
                    'autocomplete': 'off'
                }
            )
        }

    def clean_send_date(self):
        send_date = self.cleaned_data.get('send_date')
        if send_date <= timezone.now():
            past_date_error = ValidationError(
                gettext('Invalid date. Scheduled send date must be a future date.'),
                code='past_date_error'
            )
            self.add_error('send_date', past_date_error)
        return send_date

    def save(self, commit=True):
        campaign = super().save(commit=False)
        if commit:
            campaign.status = CampaignStatus.SCHEDULED
            campaign.update_date = timezone.now()
            campaign.save()
        return campaign


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
