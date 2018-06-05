from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import View, FormView
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.utils import timezone

from colossus.core.models import Token
from colossus.lists.models import MailingList

from .forms import SubscribeForm
from .models import Subscriber


class IndexView(View):
    def get(self, request):
        return HttpResponse('Hi there! :)')


class SubscribeView(View):
    def get(self, request):
        mailing_list_uuid = request.GET.get('l')
        mailing_list = MailingList.objects.get(uuid=mailing_list_uuid)
        form = SubscribeForm()
        return JsonResponse({'form': form.as_p(), 'mailing_list': mailing_list.pk})


@csrf_exempt
def subscribe(request, mailing_list_uuid):
    if 'application/json' in request.META.get('HTTP_ACCEPT'):
        pass
    else:
        pass

    mailing_list = MailingList.objects.get(uuid=mailing_list_uuid)
    if request.method == 'POST':
        form = SubscribeForm(mailing_list=mailing_list, data=request.POST)
        if form.is_valid():
            form.subscribe(request)
            return redirect('subscribers:confirm_subscription', mailing_list_uuid=mailing_list_uuid)
    else:
        form = SubscribeForm(mailing_list=mailing_list)
    return render(request, 'subscribers/subscription_form.html', {
        'mailing_list': mailing_list,
        'form': form
    })


@require_GET
def confirm_subscription(request, mailing_list_uuid):
    mailing_list = MailingList.objects.get(uuid=mailing_list_uuid)
    return render(request, 'subscribers/confirm_subscription.html', {'mailing_list': mailing_list})


@require_GET
def confirm_double_optin_token(request, mailing_list_uuid, token):
    try:
        mailing_list = MailingList.objects.get(uuid=mailing_list_uuid)
    except MailingList.DoesNotExist:
        return HttpResponseBadRequest('The requested list does not exist.')

    try:
        confirm_token = Token.objects.get(text=token, description='confirm_subscription')
    except Token.DoesNotExist:
        return HttpResponseBadRequest('Invalid token.')

    subscriber = confirm_token.content_object
    subscriber.confirm_subscription(request)

    return HttpResponse('Thank you!')
