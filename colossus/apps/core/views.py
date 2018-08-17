from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView

from colossus.apps.lists.models import MailingList


@method_decorator(login_required, name='dispatch')
class SiteUpdateView(UpdateView):
    model = Site
    fields = ('name', 'domain',)
    template_name = 'core/site_form.html'
    success_url = reverse_lazy('settings')

    def get_object(self, queryset=None):
        return get_current_site(self.request)


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html', {'menu': 'dashboard'})


@login_required
def settings(request):
    return render(request, 'core/settings.html', {'menu': 'settings'})


def subscribe_shortcut(request, mailing_list_slug):
    mailing_list = get_object_or_404(MailingList, slug=mailing_list_slug)
    return redirect('subscribers:subscribe', mailing_list_uuid=mailing_list.uuid)


def unsubscribe_shortcut(request, mailing_list_slug):
    mailing_list = get_object_or_404(MailingList, slug=mailing_list_slug)
    return redirect('subscribers:unsubscribe_manual', mailing_list_uuid=mailing_list.uuid)
