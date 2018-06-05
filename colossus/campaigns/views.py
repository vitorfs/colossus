from django.views.generic import CreateView, ListView, DetailView, UpdateView, FormView, TemplateView

from .models import Campaign


class CampaignListView(ListView):
    model = Campaign

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'campaigns'
        return super().get_context_data(**kwargs)


class CampaignCreateView(CreateView):
    model = Campaign
    fields = ('campaign_type', 'name', 'mailing_list')

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'campaigns'
        return super().get_context_data(**kwargs)
