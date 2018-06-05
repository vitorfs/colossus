from django.shortcuts import get_object_or_404
from django.views.generic.base import ContextMixin

from .models import Campaign


class CampaignMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'campaigns'
        return super().get_context_data(**kwargs)
