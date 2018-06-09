from smtplib import SMTPException

from django.views.generic import CreateView, ListView, DetailView, UpdateView, FormView, TemplateView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Campaign, Email
from .mixins import CampaignMixin
from .forms import DesignEmailForm, PlainTextEmailForm, CampaignTestEmailForm


class CampaignListView(CampaignMixin, ListView):
    model = Campaign
    context_object_name = 'campaigns'
    paginate_by = 3


class CampaignCreateView(CampaignMixin, CreateView):
    model = Campaign
    fields = ('campaign_type', 'name',)


class CampaignEditView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_edit.html'

    def get_context_data(self, **kwargs):
        kwargs['test_email_form'] = CampaignTestEmailForm()
        kwargs['plain_text_email_form'] = PlainTextEmailForm(instance=self.object.email)
        kwargs['checklist'] = self.object.email.checklist()
        return super().get_context_data(**kwargs)


class CampaignDetailView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'


class CampaignEditRecipientsView(CampaignMixin, UpdateView):
    model = Campaign
    fields = ('mailing_list',)
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Recipients'
        return super().get_context_data(**kwargs)


class AbstractCampaignEmailUpdateView(CampaignMixin, UpdateView):
    model = Email
    template_name = 'campaigns/campaign_form.html'

    def get_context_data(self, **kwargs):
        kwargs['title'] = self.title
        kwargs['campaign'] = self.campaign
        return super().get_context_data(**kwargs)

    def get_object(self, queryset=None):
        self.campaign = get_object_or_404(Campaign, pk=self.kwargs.get('pk'))
        return self.campaign.email

    def get_success_url(self):
        return reverse('campaigns:campaign_edit', kwargs=self.kwargs)


class CampaignEditFromView(AbstractCampaignEmailUpdateView):
    title = 'From'
    fields = ('from_name', 'from_email',)


class CampaignEditSubjectView(AbstractCampaignEmailUpdateView):
    title = 'Subject'
    fields = ('subject', 'preview',)


class CampaignEditContentView(AbstractCampaignEmailUpdateView):
    title = 'Design Email'
    form_class = DesignEmailForm
    template_name = 'campaigns/design_email_form.html'


class CampaignEditPlainTextContentView(AbstractCampaignEmailUpdateView):
    title = 'Edit Plain-Text Email'
    form_class = PlainTextEmailForm


def campaign_test_email(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == 'POST':
        form = CampaignTestEmailForm(request.POST)
        if form.is_valid():
            try:
                form.send(campaign)
            except SMTPException as err:
                # log
                pass
            return redirect(campaign.get_absolute_url())
    else:
        form = CampaignTestEmailForm()
    return render(request, 'campaigns/test_email_form.html', {
        'menu': 'campaigns',
        'campaign': campaign,
        'form': form
    })

def campaign_preview_email(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    subject = campaign.email.subject
    body = campaign.email.render_html(subscriber=None)
    return render(request, 'campaigns/email_preview.html', {
        'subject': subject,
        'body': body
    })
