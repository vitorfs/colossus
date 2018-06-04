from django.views.generic import View, FormView
from django.http import HttpResponse, JsonResponse

from colossus.mailing.models import MailingList

from .forms import SubscriptionForm


class IndexView(View):
    def get(self, request):
        return HttpResponse('Hi there! :)')


class SubscribeView(View):
    def get(self, request):
        mailing_list_uuid = request.GET.get('l')
        mailing_list = MailingList.objects.get(uuid=mailing_list_uuid)
        form = SubscriptionForm()
        return JsonResponse({'form': form.as_p(), 'mailing_list': mailing_list.pk})
