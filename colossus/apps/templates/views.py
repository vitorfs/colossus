from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views.generic.base import ContextMixin

from .forms import EmailTemplateForm
from .models import EmailTemplate


class EmailTemplateMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        kwargs['menu'] = 'templates'
        return super().get_context_data(**kwargs)


@method_decorator(login_required, name='dispatch')
class EmailTemplateListView(EmailTemplateMixin, ListView):
    model = EmailTemplate
    context_object_name = 'templates'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        kwargs['total_count'] = self.model.objects.count()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        queryset = self.model.objects.select_related('last_used_campaign')
        if self.request.GET.get('q', ''):
            query = self.request.GET.get('q')
            queryset = queryset.filter(Q(name__icontains=query) | Q(content__icontains=query))
            self.extra_context.update({
                'is_filtered': True,
                'query': query
            })
        queryset = queryset.order_by(F('last_used_date').desc(nulls_last=True), '-update_date')
        return queryset


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


@login_required
def email_template_editor(request, pk):
    email_template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == 'POST':
        form = EmailTemplateForm(data=request.POST, instance=email_template)
        if form.is_valid():
            email_template = form.save()
            if request.POST.get('action', 'save_changes') == 'save_changes':
                return redirect(email_template)
            return redirect('templates:emailtemplates')
    else:
        form = EmailTemplateForm(instance=email_template)
    return render(request, 'templates/emailtemplate_editor.html', {
        'menu': 'templates',
        'form': form,
        'email_template': email_template
    })


@login_required
def email_template_preview(request, pk):
    email_template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == 'POST':
        form = EmailTemplateForm(data=request.POST, instance=email_template)
        if form.is_valid():
            email_template = form.save(commit=False)
    html = email_template.html_preview()
    if 'application/json' in request.META.get('HTTP_ACCEPT'):
        return JsonResponse({'html': html})
    return HttpResponse(html)


@require_POST
@login_required
def email_template_autosave(request, pk):
    data = {'valid': False}
    status_code = 200
    try:
        email_template = EmailTemplate.objects.get(pk=pk)
        form = EmailTemplate(instance=email_template, data=request.POST)
        if form.is_valid():
            email_template = form.save()
            data['preview'] = email_template.html_preview()
            data['valid'] = True
        else:
            data['errors'] = form.errors()
    except EmailTemplate.DoesNotExist:
        data['message'] = _('Email template does not exist.')
        status_code = 404
    return JsonResponse(data, status_code=status_code)
