from django.views.generic import CreateView, ListView, DetailView, UpdateView, FormView, TemplateView
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Campaign, Email
from .mixins import CampaignMixin


class CampaignListView(CampaignMixin, ListView):
    model = Campaign
    context_object_name = 'campaigns'


class CampaignCreateView(CampaignMixin, CreateView):
    model = Campaign
    fields = ('campaign_type', 'name',)


class CampaignEditView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_edit.html'


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
    fields = ('content',)
