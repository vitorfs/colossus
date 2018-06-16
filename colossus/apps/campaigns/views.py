from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from . import constants
from .api import get_test_email_context
from .forms import CampaignTestEmailForm, DesignEmailForm, PlainTextEmailForm
from .mixins import CampaignMixin
from .models import Campaign, Email


@method_decorator(login_required, name='dispatch')
class CampaignListView(CampaignMixin, ListView):
    model = Campaign
    context_object_name = 'campaigns'
    ordering = ('-create_date',)
    paginate_by = 25


@method_decorator(login_required, name='dispatch')
class CampaignCreateView(CampaignMixin, CreateView):
    model = Campaign
    fields = ('campaign_type', 'name',)


@method_decorator(login_required, name='dispatch')
class CampaignEditView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_edit.html'

    def get_context_data(self, **kwargs):
        kwargs['test_email_form'] = CampaignTestEmailForm()
        kwargs['plain_text_email_form'] = PlainTextEmailForm(instance=self.object.email)
        kwargs['checklist'] = self.object.email.checklist()
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignDetailView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'


@method_decorator(login_required, name='dispatch')
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


@method_decorator(login_required, name='dispatch')
class CampaignEditFromView(AbstractCampaignEmailUpdateView):
    title = 'From'
    fields = ('from_name', 'from_email',)


@method_decorator(login_required, name='dispatch')
class CampaignEditSubjectView(AbstractCampaignEmailUpdateView):
    title = 'Subject'
    fields = ('subject', 'preview',)


@method_decorator(login_required, name='dispatch')
class CampaignEditContentView(AbstractCampaignEmailUpdateView):
    title = 'Design Email'
    form_class = DesignEmailForm
    template_name = 'campaigns/design_email_form.html'


@method_decorator(login_required, name='dispatch')
class CampaignEditPlainTextContentView(AbstractCampaignEmailUpdateView):
    title = 'Edit Plain-Text Email'
    form_class = PlainTextEmailForm


@login_required
def campaign_test_email(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == 'POST':
        form = CampaignTestEmailForm(request.POST)
        if form.is_valid():
            form.send(campaign.email)
            return redirect(campaign.get_absolute_url())
    else:
        form = CampaignTestEmailForm()
    return render(request, 'campaigns/test_email_form.html', {
        'menu': 'campaigns',
        'campaign': campaign,
        'form': form
    })


@login_required
def campaign_preview_email(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == 'POST':
        campaign.email.content = request.POST.get('content')
    test_context_dict = get_test_email_context()
    html = campaign.email.render_html(test_context_dict)
    if 'application/json' in request.META.get('HTTP_ACCEPT'):
        return JsonResponse({'html': html})
    else:
        return HttpResponse(html)


@login_required
def send_campaign(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)

    if campaign.status == constants.SENT or not campaign.can_send():
        return redirect(campaign.get_absolute_url())

    if request.method == 'POST':
        campaign.send()
        return redirect('campaigns:send_campaign_complete', pk=pk)

    return render(request, 'campaigns/send_campaign.html', {
        'menu': 'campaign',
        'campaign': campaign
    })


@method_decorator(login_required, name='dispatch')
class SendCampaignCompleteView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/send_campaign_done.html'
