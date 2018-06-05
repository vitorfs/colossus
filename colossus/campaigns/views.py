from django.views.generic import CreateView, ListView, DetailView, UpdateView, FormView, TemplateView

from .models import Campaign


class CampaignListView(ListView):
    model = Campaign

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'campaigns'
        return super().get_context_data(**kwargs)
