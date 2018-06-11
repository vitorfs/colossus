from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, FormView, TemplateView

from colossus.subscribers.models import Subscriber
from colossus.subscribers import constants as subscribers_constants

from .mixins import MailingListMixin
from .models import MailingList
from .forms import ImportSubscribersForm


class MailingListListView(ListView):
    model = MailingList
    context_object_name = 'mailing_lists'

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        return super().get_context_data(**kwargs)


class MailingListCreateView(CreateView):
    model = MailingList
    fields = ('name',)

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        return super().get_context_data(**kwargs)


class MailingListDetailView(DetailView):
    model = MailingList
    context_object_name = 'mailing_list'

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        kwargs['submenu'] = 'details'
        return super().get_context_data(**kwargs)


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


class SubscriberUpdateView(MailingListMixin, UpdateView):
    model = Subscriber
    fields = '__all__'
    pk_url_kwarg = 'subscriber_pk'
    template_name = 'lists/subscriber_form.html'

    def get_success_url(self):
        return reverse('lists:subscribers', kwargs={'pk': self.kwargs.get('pk')})


class ImportSubscribersView(MailingListMixin, FormView):
    form_class = ImportSubscribersForm
    template_name = 'lists/import_subscribers_form.html'

    def form_valid(self, form):
        form.import_subscribers(self.request, self.kwargs.get('pk'))
        return redirect('lists:subscribers', pk=self.kwargs.get('pk'))


class SignupFormsView(MailingListMixin, TemplateView):
    template_name = 'lists/subscription_forms.html'

    def get_context_data(self, **kwargs):
        kwargs['submenu'] = 'forms'
        return super().get_context_data(**kwargs)


class MailingListSettingsView(UpdateView):
    model = MailingList
    fields = ('name', 'slug', 'website_url', 'campaign_default_from_name', 'campaign_default_from_email',
              'campaign_default_email_subject', 'enable_recaptcha', )
    context_object_name = 'mailing_list'
    template_name = 'lists/settings.html'

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'lists'
        kwargs['submenu'] = 'settings'
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('lists:settings', kwargs={'pk': self.kwargs.get('pk')})
