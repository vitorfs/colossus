from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from colossus.apps.notifications.constants import Actions
from colossus.apps.notifications.models import Notification


@method_decorator(login_required, name='dispatch')
class NotificationListView(ListView):
    model = Notification
    context_object_name = 'notifications'
    paginate_by = 100

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.request.user.notifications.filter(is_seen=False).update(is_seen=True)
        return response


@method_decorator(login_required, name='dispatch')
class NotificationDetailView(DetailView):
    model = Notification
    context_object_name = 'notification'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if not self.object.is_read:
            self.object.is_read = True
            self.object.save(update_fields=['is_read'])
        return response


@login_required
def unread(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-date')
    notifications.update(is_seen=True)
    context = {
        'notifications': notifications[:5],
        'Actions': Actions
    }
    html = render_to_string('notifications/_unread.html', context, request)
    return JsonResponse({'html': html})
