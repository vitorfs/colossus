from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView

from .models import EmailTemplate


class EmailTemplateListView(ListView):
    model = EmailTemplate
    context_object_name = 'templates'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'templates'
        return super().get_context_data(**kwargs)


class EmailTemplateCreateView(CreateView):
    model = EmailTemplate
    fields = ('name', 'content',)


class EmailTemplateUpdateView(UpdateView):
    model = EmailTemplate
    fields = ('name', 'content',)
