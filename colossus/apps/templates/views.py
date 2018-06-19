from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView
from django.template.loader import get_template

from .models import EmailTemplate


@method_decorator(login_required, name='dispatch')
class EmailTemplateListView(ListView):
    model = EmailTemplate
    context_object_name = 'templates'
    paginate_by = 10
    ordering = ('-update_date')

    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'templates'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class EmailTemplateCreateView(CreateView):
    model = EmailTemplate
    context_object_name = 'email_template'
    fields = ('name',)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        default_content = get_template('templates/default_email_template_content.html')
        self.object.content = default_content.template.source
        self.object.save()
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class EmailTemplateUpdateView(UpdateView):
    model = EmailTemplate
    context_object_name = 'email_template'
    fields = ('name',)


@method_decorator(login_required, name='dispatch')
class EmailTemplateEditorView(UpdateView):
    model = EmailTemplate
    context_object_name = 'email_template'
    fields = ('content',)
    template_name = 'templates/emailtemplate_editor.html'
