from django.views.generic.base import ContextMixin


class CampaignMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'campaigns'
        return super().get_context_data(**kwargs)
