from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.base import ContextMixin

from .models import EmailTemplate


class EmailTemplateMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'templates'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class EmailTemplateListView(EmailTemplateMixin, ListView):
    model = EmailTemplate
    context_object_name = 'templates'
    paginate_by = 10
    ordering = ('-update_date')


@method_decorator(login_required, name='dispatch')
class EmailTemplateCreateView(EmailTemplateMixin, CreateView):
    model = EmailTemplate
    context_object_name = 'email_template'
    fields = ('name',)


@method_decorator(login_required, name='dispatch')
class EmailTemplateUpdateView(EmailTemplateMixin, UpdateView):
    model = EmailTemplate
    context_object_name = 'email_template'
    fields = ('name',)


@method_decorator(login_required, name='dispatch')
class EmailTemplateEditorView(EmailTemplateMixin, UpdateView):
    model = EmailTemplate
    context_object_name = 'email_template'
    fields = ('content',)
    template_name = 'templates/emailtemplate_editor.html'
