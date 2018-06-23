from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.views.generic.base import ContextMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db.models import Q

from .models import EmailTemplate
from .forms import EmailTemplateForm


class EmailTemplateMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'templates'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class EmailTemplateListView(EmailTemplateMixin, ListView):
    model = EmailTemplate
    context_object_name = 'templates'
    paginate_by = 2

    def get_context_data(self, **kwargs):
        kwargs['total_count'] = self.model.objects.count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = self.model.objects.all()
        if 'q' in self.request.GET:
            query = self.request.GET.get('q')
            queryset = queryset.filter(Q(name__icontains=query) | Q(content__icontains=query))
            self.extra_context = {
                'is_filtered': True,
                'query': query
            }
        return queryset.order_by('-update_date')


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
class EmailTemplateDeleteView(EmailTemplateMixin, DeleteView):
    model = EmailTemplate
    context_object_name = 'email_template'
    success_url = reverse_lazy('templates:emailtemplates')


@method_decorator(login_required, name='dispatch')
class EmailTemplateEditorView(EmailTemplateMixin, UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    context_object_name = 'email_template'
    template_name = 'templates/emailtemplate_editor.html'

    def get_success_url(self):
        if self.request.POST.get('action', 'save_changes') == 'save_changes':
            return self.object.get_absolute_url()
        return reverse('templates:emailtemplates')


@login_required
def preview_email_template(request, pk):
    email_template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == 'POST':
        form = EmailTemplateForm(data=request.POST, instance=email_template)
        if form.is_valid():
            email_template = form.save(commit=False)
    html = email_template.html_preview()
    if 'application/json' in request.META.get('HTTP_ACCEPT'):
        return JsonResponse({'html': html})
    else:
        return HttpResponse(html)
