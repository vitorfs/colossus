from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Activity
from .api import get_test_email_context
from .constants import CampaignStatus, CampaignTypes
from .forms import (
    CampaignTestEmailForm, CreateCampaignForm, EmailEditorForm,
    PlainTextEmailForm, ScheduleCampaignForm,
)
from .mixins import CampaignMixin
from .models import Campaign, Email, Link


@method_decorator(login_required, name='dispatch')
class CampaignListView(CampaignMixin, ListView):
    model = Campaign
    context_object_name = 'campaigns'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        kwargs['campaign_types'] = CampaignTypes
        kwargs['campaign_status'] = CampaignStatus
        kwargs['total_count'] = Campaign.objects.count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.extra_context = {}

        queryset = super().get_queryset().select_related('mailing_list')

        try:
            status_filter = int(self.request.GET.get('status'))
            if status_filter in CampaignStatus.LABELS.keys():
                self.extra_context['status'] = status_filter
                queryset = queryset.filter(status=status_filter)
        except Exception:
            status_filter = None

        if self.request.GET.get('q', ''):
            query = self.request.GET.get('q')
            queryset = queryset.filter(name__icontains=query)
            self.extra_context['is_filtered'] = True
            self.extra_context['query'] = query

        queryset = queryset.order_by('-update_date')

        return queryset


@method_decorator(login_required, name='dispatch')
class CampaignCreateView(CampaignMixin, CreateView):
    model = Campaign
    form_class = CreateCampaignForm


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
    extra_context = {'submenu': 'details'}


@method_decorator(login_required, name='dispatch')
class CampaignPreviewView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_preview.html'
    extra_context = {'submenu': 'preview'}


@method_decorator(login_required, name='dispatch')
class CampaignReportsView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_reports.html'
    extra_context = {'submenu': 'reports'}

    def get_context_data(self, **kwargs):
        kwargs['links'] = Link.objects.filter(email__campaign_id=self.kwargs.get('pk')) \
            .only('url', 'total_clicks_count') \
            .order_by('-total_clicks_count')
        locations = Activity.objects \
            .filter(email__campaign_id=self.kwargs.get('pk'), activity_type=ActivityTypes.OPENED) \
            .values('location__country__code', 'location__country__name') \
            .annotate(total_opens=Count('id')) \
            .order_by('-total_opens')
        kwargs['locations'] = locations
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignEditRecipientsView(CampaignMixin, UpdateView):
    model = Campaign
    fields = ('mailing_list',)
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        kwargs['title'] = _('Recipients')
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignEditNameView(CampaignMixin, UpdateView):
    model = Campaign
    fields = ('name',)
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        kwargs['title'] = _('Rename campaign')
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignDeleteView(CampaignMixin, DeleteView):
    model = Campaign
    context_object_name = 'campaign'
    success_url = reverse_lazy('campaigns:campaigns')


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
    title = _('From')
    fields = ('from_name', 'from_email',)

    def get_initial(self):
        if not self.campaign.email and self.campaign.mailing_list is not None:
            self.initial['from_name'] = self.campaign.mailing_list.campaign_default_from_name
            self.initial['from_email'] = self.campaign.mailing_list.campaign_default_from_email
        return super().get_initial()


@method_decorator(login_required, name='dispatch')
class CampaignEditSubjectView(AbstractCampaignEmailUpdateView):
    title = _('Subject')
    fields = ('subject', 'preview',)


@method_decorator(login_required, name='dispatch')
class CampaignEditPlainTextContentView(AbstractCampaignEmailUpdateView):
    title = _('Edit Plain-Text Email')
    form_class = PlainTextEmailForm


@method_decorator(login_required, name='dispatch')
class CampaignEditTemplateView(AbstractCampaignEmailUpdateView):
    title = _('Template')
    fields = ('template',)

    def form_valid(self, form):
        email = form.save(commit=False)
        email.set_template_content()
        email.set_blocks()
        email.save()
        return redirect('campaigns:campaign_edit_content', pk=self.kwargs.get('pk'))


@method_decorator(login_required, name='dispatch')
class SendCampaignCompleteView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/send_campaign_done.html'


@method_decorator(login_required, name='dispatch')
class ScheduleCampaignView(CampaignMixin, UpdateView):
    model = Campaign
    context_object_name = 'campaign'
    form_class = ScheduleCampaignForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = _('Schedule campaign')
        return super().get_context_data(**kwargs)


@login_required
def campaign_edit_content(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == 'POST':
        form = EmailEditorForm(campaign.email, data=request.POST)
        if form.is_valid():
            form.save()
            if request.POST.get('action', 'save_changes') == 'save_changes':
                return redirect('campaigns:campaign_edit_content', pk=pk)
            return redirect('campaigns:campaign_edit', pk=pk)

    else:
        form = EmailEditorForm(campaign.email)
    return render(request, 'campaigns/email_form.html', {
        'campaign': campaign,
        'form': form
    })


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
    email = campaign.email
    if request.method == 'POST':
        form = EmailEditorForm(email, data=request.POST)
        if form.is_valid():
            email = form.save(commit=False)
    context = dict()
    if campaign.mailing_list:
        context['unsub'] = reverse('subscribers:unsubscribe_manual', kwargs={
            'mailing_list_uuid': campaign.mailing_list.uuid
        })
    test_context_dict = get_test_email_context(**context)
    html = email.render(test_context_dict)
    if 'application/json' in request.META.get('HTTP_ACCEPT'):
        return JsonResponse({'html': html})
    else:
        return HttpResponse(html)


@login_required
def send_campaign(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)

    if campaign.status == CampaignStatus.SENT or not campaign.can_send:
        return redirect(campaign.get_absolute_url())

    if request.method == 'POST':
        campaign.send()
        return redirect('campaigns:send_campaign_complete', pk=pk)

    return render(request, 'campaigns/send_campaign.html', {
        'menu': 'campaign',
        'campaign': campaign
    })


@require_GET
@login_required
def replicate_campaign(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    replicated_campaign = campaign.replicate()
    return redirect(replicated_campaign)
