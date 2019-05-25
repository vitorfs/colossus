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
        fields = ('name', 'mailing_list', 'tag')
        widgets = {
            'mailing_list': forms.HiddenInput(),
            'tag': forms.HiddenInput()
        }

    def save(self, commit=True) -> Campaign:
        """
        Before saving check the mailing_list and tag data for consistency
        This is done during the save method instead of the clean because
        both fields are hidden fields, used when the user clicks the "Send"
        button on a tag (as a shortcut to create and campaign for subscribers
        in a given tag).

        If the mailing_list + tag combo is invalid there is nothing the user
        can do in the user interface, so just fallback to create a campaign
        with the Name only. Later on the user can set the mailing_list and tag.

        :param commit: Boolean to indicate if the data should be saved
            on the database or not
        :return: A new Campaign instance
        """

        campaign = super().save(commit=False)
        mailing_list = self.cleaned_data.get('mailing_list')
        tag = self.cleaned_data.get('tag')

        if tag is not None and mailing_list is None:
            # Remove the tag if there was no mailing list associated with
            # This is just to keep the consistency of the data
            # In normal cases this should never happen, unless the user is injecting/forging
            # a POST request manually
            campaign.tag = None

        if tag is not None and mailing_list is not None:
            # Remove the tag if it is not associated with the mailing list
            if not mailing_list.tags.filter(pk=tag.pk).exists():
                campaign.tag = None

        if commit:
            campaign.save()

        return campaign


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
        elif self.instance.pk and self.instance.mailing_list:
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
