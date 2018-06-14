from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView

from .models import EmailTemplate


@method_decorator(login_required, name='dispatch')
class EmailTemplateListView(ListView):
    model = EmailTemplate
    context_object_name = 'templates'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'templates'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class EmailTemplateCreateView(CreateView):
    model = EmailTemplate
    fields = ('name', 'content',)


@method_decorator(login_required, name='dispatch')
class EmailTemplateUpdateView(UpdateView):
    model = EmailTemplate
    fields = ('name', 'content',)
