from django.shortcuts import render
from django.views.generic import CreateView, ListView, DetailView

from .mixins import MailingListMixin
from .models import MailingList, Subscriber


class MailingListListView(ListView):
    model = MailingList
    context_object_name = 'mailing_lists'


class MailingListCreateView(CreateView):
    model = MailingList
    fields = ('name',)


class MailingListDetailView(DetailView):
    model = MailingList
    context_object_name = 'mailing_list'


class SubscriberListView(MailingListMixin, ListView):
    model = Subscriber
    context_object_name = 'subscribers'
