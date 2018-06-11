from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.views.generic import UpdateView
from django.urls import reverse_lazy


def dashboard(request):
    return render(request, 'core/dashboard.html', {'menu': 'dashboard'})


def settings(request):
    return render(request, 'core/settings.html', {'menu': 'settings'})


class SiteUpdateView(UpdateView):
    model = Site
    fields = ('name', 'domain',)
    template_name = 'core/site_form.html'
    success_url = reverse_lazy('settings')

    def get_object(self, queryset=None):
        return get_current_site(self.request)
