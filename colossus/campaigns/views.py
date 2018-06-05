from django.views.generic import CreateView, ListView, DetailView, UpdateView, FormView, TemplateView

from .models import Campaign
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
