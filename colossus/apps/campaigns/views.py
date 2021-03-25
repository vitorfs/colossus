from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_GET
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from colossus.apps.core.models import Country
from colossus.apps.lists.models import MailingList
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Activity

from ...utils import get_campaign_connection
from .api import get_test_email_context
from .constants import CampaignStatus, CampaignTypes
from .forms import (
    CampaignRecipientsForm, CampaignTestEmailForm, CreateCampaignForm,
    EmailEditorForm, ScheduleCampaignForm,
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
            if status_filter in CampaignStatus.FILTERS:
                self.extra_context['status'] = status_filter
                queryset = queryset.filter(status=status_filter)
        except (ValueError, TypeError):
            pass

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

    def get_initial(self):
        initial = super().get_initial()
        mailing_list_id = self.request.GET.get('mailing_list', '')
        tag_id = self.request.GET.get('tag', '')
        try:
            initial['mailing_list'] = int(mailing_list_id)
            initial['tag'] = int(tag_id)
        except (TypeError, ValueError):
            pass
        return initial


@method_decorator(login_required, name='dispatch')
class CampaignEditView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_edit.html'

    def get_queryset(self):
        return super().get_queryset() \
            .select_related('mailing_list') \
            .prefetch_related('emails') \
            .filter(status=CampaignStatus.DRAFT)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        messages.debug(request, '[debug] campaign uuid: %s' % self.object.uuid)
        return response

    def get_context_data(self, **kwargs):
        kwargs['test_email_form'] = CampaignTestEmailForm()
        kwargs['checklist'] = self.object.email.checklist()
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignDetailView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    extra_context = {'submenu': 'details'}


@method_decorator(login_required, name='dispatch')
class CampaignScheduledView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    extra_context = {'submenu': 'details'}
    template_name = 'campaigns/campaign_scheduled.html'

    def get_queryset(self):
        return super().get_queryset().filter(status=CampaignStatus.SCHEDULED)


@method_decorator(login_required, name='dispatch')
class CampaignRevertDraftView(View):
    def post(self, request, pk):
        campaign = get_object_or_404(Campaign, pk=pk, status=CampaignStatus.SCHEDULED)
        campaign.status = CampaignStatus.DRAFT
        campaign.save(update_fields=['status'])
        messages.success(request, gettext('Campaign reverted to Draft status so you can make changes. Don\'t forget '
                                          'to schedule your campaign again after you\'re done with your changes.'))
        return redirect(campaign)


@method_decorator(login_required, name='dispatch')
class CampaignPreviewView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_preview.html'
    extra_context = {'submenu': 'preview'}


@method_decorator(login_required, name='dispatch')
class CampaignLinksView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_links.html'
    extra_context = {'submenu': 'links'}

    def get_context_data(self, **kwargs):
        kwargs['links'] = self.object.get_links().order_by('index')
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignReportsView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_reports.html'
    extra_context = {'submenu': 'reports'}

    def get_context_data(self, **kwargs):
        campaign: Campaign = self.object

        links = campaign.get_links().only('url', 'total_clicks_count')[:10]

        unsubscribed_count = Activity.objects \
            .filter(campaign_id=self.kwargs.get('pk'), activity_type=ActivityTypes.UNSUBSCRIBED) \
            .count()

        subscriber_open_activities = Activity.objects.filter(email__campaign_id=self.kwargs.get('pk'),
                                                             activity_type=ActivityTypes.OPENED) \
                                                     .values('subscriber__id', 'subscriber__email') \
                                                     .annotate(total_opens=Count('id')) \
                                                     .order_by('-total_opens')[:10]

        location_open_activities = Activity.objects.filter(email__campaign_id=self.kwargs.get('pk'),
                                                           activity_type=ActivityTypes.OPENED) \
                                                   .values('location__country__code', 'location__country__name') \
                                                   .annotate(total_opens=Count('id')) \
                                                   .order_by('-total_opens')[:10]

        kwargs.update({
            'links': links,
            'unsubscribed_count': unsubscribed_count,
            'subscriber_open_activities': subscriber_open_activities,
            'location_open_activities': location_open_activities,
        })
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignReportsLocationsView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_reports_locations.html'
    extra_context = {'submenu': 'reports'}

    def get_context_data(self, **kwargs):
        location_open_activities = Activity.objects \
            .filter(email__campaign_id=self.kwargs.get('pk'), activity_type=ActivityTypes.OPENED) \
            .values('location__country__code', 'location__country__name') \
            .annotate(total_opens=Count('id')) \
            .order_by('-total_opens')

        kwargs.update({
            'location_open_activities': location_open_activities,
        })
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignReportsCountryView(CampaignMixin, DetailView):
    model = Campaign
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_reports_country.html'
    extra_context = {'submenu': 'reports'}

    def get_context_data(self, **kwargs):
        country_code = self.kwargs.get('country_code')
        country = get_object_or_404(Country, code=country_code)

        country_total_opens = Activity.objects \
            .filter(email__campaign_id=self.kwargs.get('pk'),
                    activity_type=ActivityTypes.OPENED,
                    location__country__code=country_code) \
            .values('location__country__code') \
            .aggregate(total=Count('location__country__code'))

        cities = Activity.objects \
            .filter(email__campaign_id=self.kwargs.get('pk'),
                    activity_type=ActivityTypes.OPENED,
                    location__country__code=country_code) \
            .select_related('location') \
            .values('location__name') \
            .annotate(total=Count('location__name')) \
            .order_by('-total')

        kwargs['menu'] = 'lists'
        kwargs['country'] = country
        kwargs['country_total_opens'] = country_total_opens['total']
        kwargs['cities'] = cities
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class CampaignEditRecipientsView(CampaignMixin, UpdateView):
    model = Campaign
    form_class = CampaignRecipientsForm
    context_object_name = 'campaign'
    template_name = 'campaigns/campaign_edit_recipients.html'


@login_required
def load_list_tags(request):
    list_id = request.GET.get('id')

    try:
        mailing_list = MailingList.objects.get(pk=list_id)
        tags = mailing_list.tags.order_by('name')
    except MailingList.DoesNotExist:
        tags = list()

    context = {
        'tags': tags
    }
    options = render_to_string('campaigns/_campaign_list_tags_options.html', context, request)
    return JsonResponse({'options': options})


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
        if self.campaign.mailing_list is not None:
            if self.campaign.email.from_email == '':
                self.initial['from_name'] = self.campaign.mailing_list.campaign_default_from_name
                self.initial['from_email'] = self.campaign.mailing_list.campaign_default_from_email
        return super().get_initial()


@method_decorator(login_required, name='dispatch')
class CampaignEditSubjectView(AbstractCampaignEmailUpdateView):
    title = _('Subject')
    fields = ('subject', 'preview',)

    def get_initial(self):
        if self.campaign.mailing_list is not None:
            if self.campaign.email.subject == '':
                self.initial['subject'] = self.campaign.mailing_list.campaign_default_email_subject
        return super().get_initial()


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
    template_name = 'campaigns/schedule_campaign_form.html'

    def get_queryset(self):
        return super().get_queryset().filter(status__in={CampaignStatus.DRAFT, CampaignStatus.SCHEDULED})

    def get_context_data(self, **kwargs):
        kwargs['time'] = timezone.now()
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class LinkUpdateView(SuccessMessageMixin, CampaignMixin, UpdateView):
    model = Link
    fields = ('url',)
    context_object_name = 'link'
    pk_url_kwarg = 'link_pk'
    extra_context = {'submenu': 'links'}
    success_message = 'The link <strong>%s</strong> was updated successfully.'

    def get_queryset(self):
        return super().get_queryset().select_related()

    def get_context_data(self, **kwargs):
        kwargs['campaign'] = self.object.email.campaign
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('campaigns:campaign_links', kwargs={'pk': self.kwargs.get('pk')})

    def get_success_message(self, cleaned_data):
        return mark_safe(self.success_message % self.object.short_uuid)


@login_required
def campaign_edit_content(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)

    if not campaign.email.template_content:
        messages.info(request, gettext('First, select a template for your email'))
        return redirect('campaigns:campaign_edit_template', pk=pk)

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
    connection = get_campaign_connection(campaign=campaign)

    if request.method == 'POST':
        form = CampaignTestEmailForm(request.POST)
        if form.is_valid():
            form.send(campaign.email, connection=connection)
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
