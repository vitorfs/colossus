from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from colossus.apps.notifications.models import Notification


@method_decorator(login_required, name='dispatch')
class NotificationListView(ListView):
    model = Notification
    paginate_by = 100

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class NotificationDetailView(DetailView):
    model = Notification


@login_required
def notifications(request):
    return JsonResponse({'message': 'test'})
