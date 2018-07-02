from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import modelform_factory
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, TemplateView,
    UpdateView, View,
)

from colossus.apps.subscribers.constants import Status, TemplateKeys
from colossus.apps.subscribers.models import (
    Subscriber, SubscriptionFormTemplate,
)

from .charts import SubscriptionsSummaryChart
from .forms import CSVImportSubscribersForm, PasteImportSubscribersForm, ColumnsMappingForm
from .mixins import MailingListMixin
from .models import MailingList, SubscriberImport


@method_decorator(login_required, name='dispatch')
class MailingListListView(ListView):
    model = MailingList
    context_object_name = 'mailing_lists'
    ordering = ('name',)
    paginate_by = 25

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        kwargs['total_count'] = MailingList.objects.count()
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class MailingListCreateView(CreateView):
    model = MailingList
    fields = ('name', 'slug', 'campaign_default_from_name', 'campaign_default_from_email', 'website_url')

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class MailingListDetailView(DetailView):
    model = MailingList
    context_object_name = 'mailing_list'

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        kwargs['submenu'] = 'details'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class SubscriberListView(MailingListMixin, ListView):
    model = Subscriber
    context_object_name = 'subscribers'
    paginate_by = 100
    template_name = 'lists/subscriber_list.html'

    def get_context_data(self, **kwargs):
        kwargs['submenu'] = 'subscribers'
        kwargs['total_count'] = self.model.objects.count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = self.model.objects.filter(mailing_list_id=self.kwargs.get('pk'))
        if self.request.GET.get('q', ''):
            query = self.request.GET.get('q')
            queryset = queryset.filter(Q(email__icontains=query) | Q(name__icontains=query))
            self.extra_context = {
                'is_filtered': True,
                'query': query
            }
        return queryset.order_by('optin_date')


@method_decorator(login_required, name='dispatch')
class SubscriberCreateView(MailingListMixin, CreateView):
    model = Subscriber
    fields = ('email', 'name')
    template_name = 'lists/subscriber_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.mailing_list_id = self.kwargs.get('pk')
        self.object.status = Status.SUBSCRIBED
        self.object.save()
        return redirect('lists:subscribers', pk=self.kwargs.get('pk'))


@method_decorator(login_required, name='dispatch')
class SubscriberUpdateView(MailingListMixin, UpdateView):
    model = Subscriber
    fields = '__all__'
    pk_url_kwarg = 'subscriber_pk'
    template_name = 'lists/subscriber_form.html'

    def get_success_url(self):
        return reverse('lists:subscribers', kwargs={'pk': self.kwargs.get('pk')})


@method_decorator(login_required, name='dispatch')
class SubscriberDeleteView(MailingListMixin, DeleteView):
    model = Subscriber
    pk_url_kwarg = 'subscriber_pk'
    context_object_name = 'subscriber'
    template_name = 'lists/subscriber_confirm_delete.html'

    def get_success_url(self):
        return reverse('lists:subscribers', kwargs={'pk': self.kwargs.get('pk')})


@method_decorator(login_required, name='dispatch')
class ImportSubscribersView(MailingListMixin, TemplateView):
    template_name = 'lists/import_subscribers.html'

    def get_context_data(self, **kwargs):
        kwargs['submenu'] = 'subscribers'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class PasteEmailsImportSubscribersView(MailingListMixin, FormView):
    template_name = 'lists/import_subscribers_form.html'
    form_class = PasteImportSubscribersForm
    extra_context = {'title': _('Paste Emails')}

    def get_context_data(self, **kwargs):
        kwargs['title'] = self.title
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.import_subscribers(self.request, self.kwargs.get('pk'))
        return redirect('lists:subscribers', pk=self.kwargs.get('pk'))


@method_decorator(login_required, name='dispatch')
class SubscriptionFormsView(MailingListMixin, TemplateView):
    template_name = 'lists/subscription_forms.html'

    def get_context_data(self, **kwargs):
        kwargs['submenu'] = 'forms'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class AbstractSettingsView(UpdateView):
    model = MailingList
    context_object_name = 'mailing_list'
    template_name = 'lists/settings.html'

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        kwargs['submenu'] = 'settings'
        kwargs['subsubmenu'] = self.subsubmenu
        kwargs['title'] = self.title
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse(self.success_url_name, kwargs={'pk': self.kwargs.get('pk')})


class ListSettingsView(AbstractSettingsView):
    fields = ('name', 'slug', 'website_url', 'contact_email_address',)
    success_url_name = 'lists:settings'
    subsubmenu = 'list_settings'
    title = _('Settings')


class SubscriptionSettingsView(AbstractSettingsView):
    fields = ('list_manager', 'enable_recaptcha',)
    success_url_name = 'lists:subscription_settings'
    subsubmenu = 'subscription_settings'
    title = _('Subscription settings')


class CampaignDefaultsView(AbstractSettingsView):
    fields = ('campaign_default_from_name', 'campaign_default_from_email', 'campaign_default_email_subject',)
    success_url_name = 'lists:defaults'
    subsubmenu = 'defaults'
    title = _('Campaign defaults')


class SMTPCredentialsView(AbstractSettingsView):
    fields = ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_use_tls', 'smtp_use_ssl',
              'smtp_timeout', 'smtp_ssl_keyfile', 'smtp_ssl_certfile')
    success_url_name = 'lists:smtp'
    subsubmenu = 'smtp'
    title = _('SMTP credentials')


@method_decorator(login_required, name='dispatch')
class FormsEditorView(MailingListMixin, TemplateView):
    template_name = 'lists/forms_editor.html'


class FormTemplateMixin:
    def get_object(self):
        mailing_list_id = self.kwargs.get('pk')
        key = self.kwargs.get('form_key')
        if key not in TemplateKeys.LABELS.keys():
            raise Http404
        form_template, created = SubscriptionFormTemplate.objects.get_or_create(
            key=key,
            mailing_list_id=mailing_list_id
        )
        return form_template


@method_decorator(login_required, name='dispatch')
class SubscriptionFormTemplateUpdateView(FormTemplateMixin, MailingListMixin, UpdateView):
    model = SubscriptionFormTemplate
    template_name = 'lists/edit_form_template.html'
    context_object_name = 'form_template'

    def get_context_data(self, **kwargs):
        kwargs['template_keys'] = TemplateKeys
        return super().get_context_data(**kwargs)

    def get_template_names(self):
        return self.object.settings['admin_template_name']

    def get_form_class(self):
        fields = self.object.settings['fields']
        form_class = modelform_factory(self.model, fields=fields)
        return form_class

    def get_initial(self):
        initial = {
            'content_html': self.object.get_default_content()
        }
        return initial


@method_decorator(login_required, name='dispatch')
class PreviewFormTemplateView(FormTemplateMixin, MailingListMixin, View):
    def get(self, request, pk, form_key):
        form_template = self.get_object()
        template_name = form_template.settings['content_template_name']
        context = {
            'mailing_list': self.mailing_list,
            'contact_email': self.mailing_list.contact_email_address,
            'unsub': '#',
            'confirm_link': '#'
        }
        if form_key == TemplateKeys.SUBSCRIBE_PAGE:
            from colossus.apps.subscribers.forms import SubscribeForm
            context['form'] = SubscribeForm(mailing_list=self.mailing_list)
        elif form_key == TemplateKeys.UNSUBSCRIBE_PAGE:
            from colossus.apps.subscribers.forms import UnsubscribeForm
            context['form'] = UnsubscribeForm(mailing_list=self.mailing_list)
        return render(request, template_name, context)


@method_decorator(login_required, name='dispatch')
class CustomizeDesignView(UpdateView):
    model = MailingList
    fields = ('forms_custom_css', 'forms_custom_header')
    context_object_name = 'mailing_list'
    template_name = 'lists/customize_design.html'

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('lists:forms_editor', kwargs={'pk': self.kwargs.get('pk')})


@method_decorator(login_required, name='dispatch')
class SubscriberImportView(MailingListMixin, CreateView):
    model = SubscriberImport
    fields = ('file',)
    template_name = 'lists/import_subscribers_form.html'
    extra_context = {'title': _('Import CSV File')}

    def get_context_data(self, **kwargs):
        kwargs['subscriber_imports'] = SubscriberImport.objects.order_by('-upload_date')
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        mailing_list_id = self.kwargs.get('pk')
        subscriber_import = form.save(commit=False)
        subscriber_import.mailing_list_id = mailing_list_id
        subscriber_import.save()
        return redirect('lists:columns_mapping', pk=mailing_list_id, import_pk=subscriber_import.pk)


@method_decorator(login_required, name='dispatch')
class ColumnsMappingView(MailingListMixin, UpdateView):
    model = SubscriberImport
    form_class = ColumnsMappingForm
    template_name = 'lists/columns_mapping.html'
    pk_url_kwarg = 'import_pk'
    context_object_name = 'subscriber_import'

    def get_success_url(self):
        return reverse('lists:columns_mapping', kwargs=self.kwargs)


@login_required
def charts_subscriptions_summary(request, pk):
    try:
        mailing_list = MailingList.objects.get(pk=pk)
        chart = SubscriptionsSummaryChart(mailing_list)
        return JsonResponse({'chart': chart.get_settings()})
    except MailingList.DoesNotExist:
        return JsonResponse(status_code=400)  # bad request status code


@login_required
def download_subscriber_import(request, pk, import_pk):
    subscriber_import = get_object_or_404(SubscriberImport, pk=import_pk, mailing_list_id=pk)
    filename = subscriber_import.file.name.split('/')[-1]
    response = HttpResponse(subscriber_import.file.read(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    return response
