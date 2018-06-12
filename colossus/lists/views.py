from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, TemplateView,
    UpdateView,
)

from colossus.subscribers import constants as subscribers_constants
from colossus.subscribers.models import Subscriber

from .charts import SubscriptionsSummaryChart
from .forms import ImportSubscribersForm
from .mixins import MailingListMixin
from .models import MailingList


@method_decorator(login_required, name='dispatch')
class MailingListListView(ListView):
    model = MailingList
    context_object_name = 'mailing_lists'
    ordering = ('name',)

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class MailingListCreateView(CreateView):
    model = MailingList
    fields = ('name',)

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
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = Subscriber.objects.filter(mailing_list_id=self.kwargs.get('pk')).order_by('optin_date')
        if 'q' in self.request.GET:
            query = self.request.GET.get('q')
            queryset = queryset.filter(email__icontains=query)
            self.extra_context = {
                'is_filtered': True,
                'query': query
            }
        return queryset


@method_decorator(login_required, name='dispatch')
class SubscriberCreateView(MailingListMixin, CreateView):
    model = Subscriber
    fields = ('email', 'name')
    template_name = 'lists/subscriber_form.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.mailing_list_id = self.kwargs.get('pk')
        self.object.status = subscribers_constants.SUBSCRIBED
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
class ImportSubscribersView(MailingListMixin, FormView):
    form_class = ImportSubscribersForm
    template_name = 'lists/import_subscribers_form.html'

    def form_valid(self, form):
        form.import_subscribers(self.request, self.kwargs.get('pk'))
        return redirect('lists:subscribers', pk=self.kwargs.get('pk'))


@method_decorator(login_required, name='dispatch')
class SignupFormsView(MailingListMixin, TemplateView):
    template_name = 'lists/subscription_forms.html'

    def get_context_data(self, **kwargs):
        kwargs['submenu'] = 'forms'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class MailingListSettingsView(UpdateView):
    model = MailingList
    fields = ('name', 'slug', 'website_url', 'contact_email_address', 'campaign_default_from_name',
              'campaign_default_from_email', 'campaign_default_email_subject', 'enable_recaptcha', )
    context_object_name = 'mailing_list'
    template_name = 'lists/settings.html'

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        kwargs['submenu'] = 'settings'
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('lists:settings', kwargs={'pk': self.kwargs.get('pk')})


@login_required
def charts_subscriptions_summary(request, pk):
    try:
        mailing_list = MailingList.objects.get(pk=pk)
        chart = SubscriptionsSummaryChart(mailing_list)
        return JsonResponse({'chart': chart.get_settings()})
    except MailingList.DoesNotExist:
        return JsonResponse(status_code=400)  # bad request status code
