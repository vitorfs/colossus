from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, FormView, TemplateView

from .mixins import MailingListMixin
from .models import MailingList, Subscriber
from .forms import NewSubscriber, ImportSubscribersForm


class MailingListListView(ListView):
    model = MailingList
    context_object_name = 'mailing_lists'


class MailingListCreateView(CreateView):
    model = MailingList
    fields = ('name',)


class MailingListDetailView(DetailView):
    model = MailingList
    context_object_name = 'mailing_list'

    def get_context_data(self, **kwargs):
        kwargs['submenu'] = 'details'
        return super().get_context_data(**kwargs)


class SubscriberListView(MailingListMixin, ListView):
    model = Subscriber
    context_object_name = 'subscribers'
    paginate_by = 100

    def get_context_data(self, **kwargs):
        kwargs['submenu'] = 'subscribers'
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = Subscriber.objects.filter(mailing_list_id=self.kwargs.get('pk')).order_by('date_created')
        return queryset


class SubscriberCreateView(MailingListMixin, CreateView):
    model = Subscriber
    fields = ('email', 'name')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.mailing_list_id = self.kwargs.get('pk')
        self.object.status = Subscriber.SUBSCRIBED
        self.object.save()
        return redirect('mailing:subscribers', pk=self.kwargs.get('pk'))


class SubscriberUpdateView(MailingListMixin, UpdateView):
    model = Subscriber
    fields = ('email', 'name', 'status')
    pk_url_kwarg = 'subscriber_pk'

    def get_success_url(self):
        return reverse('mailing:subscribers', kwargs={'pk': self.kwargs.get('pk')})


class ImportSubscribersView(MailingListMixin, FormView):
    form_class = ImportSubscribersForm
    template_name = 'mailing/import_subscribers_form.html'

    def form_valid(self, form):
        form.import_subscribers(self.request, self.kwargs.get('pk'))
        return redirect('mailing:subscribers', pk=self.kwargs.get('pk'))
