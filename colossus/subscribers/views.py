import base64

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.generic import View
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404

from colossus.campaigns.models import Campaign, Email, Link
from colossus.core.models import Token
from colossus.lists.models import MailingList
from colossus.utils import get_client_ip

from .forms import SubscribeForm, UnsubscribeForm
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
        MailingList.objects.get(uuid=mailing_list_uuid)
    except MailingList.DoesNotExist:
        return HttpResponseBadRequest('The requested list does not exist.')

    try:
        confirm_token = Token.objects.get(text=token, description='confirm_subscription')
    except Token.DoesNotExist:
        return HttpResponseBadRequest('Invalid token.')

    subscriber = confirm_token.content_object
    subscriber.confirm_subscription(request)

    return HttpResponse('Thank you!')


def unsubscribe_manual(request, mailing_list_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    if request.method == 'POST':
        form = UnsubscribeForm(mailing_list=mailing_list, data=request.POST)
        if form.is_valid():
            form.unsubscribe(request)
            return redirect('subscribers:goodbye')
    else:
        form = UnsubscribeForm(mailing_list=mailing_list)
    return render(request, 'subscribers/unsubscribe_form.html', {'form': form})


def unsubscribe(request, mailing_list_uuid, subscriber_uuid, campaign_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)

    try:
        sub = Subscriber.objects.get(uuid=subscriber_uuid, mailing_list=mailing_list)
    except Subscriber.DoesNotExist:
        return redirect('subscribers:unsubscribe_manual', mailing_list_uuid=mailing_list_uuid)

    try:
        campaign = Campaign.objects.get(uuid=campaign_uuid)
    except Campaign.DoesNotExist:
        campaign = None

    sub.unsubscribe(request, campaign)

    return redirect('subscribers:goodbye')


def goodbye(request):
    return HttpResponse('Sorry to see you go! Goodbye!', content_type='text/plain')


@require_GET
def track_open(request, email_uuid, subscriber_uuid):
    try:
        email = Email.objects.get(uuid=email_uuid)
        # TODO: increase open count
        sub = Subscriber.objects.get(uuid=subscriber_uuid)
        sub.create_activity('opened', email=email, ip_address=get_client_ip(request))
    except Exception as e:
        pass  # fail silently

    pixel = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')  # noqa
    return HttpResponse(pixel, content_type='image/png')


@require_GET
def track_click(request, link_uuid, subscriber_uuid):
    link = get_object_or_404(Link, uuid=link_uuid)
    # TODO: increase click count

    try:
        sub = Subscriber.objects.get(uuid=subscriber_uuid)
        sub.create_activity('clicked', link=link, ip_address=get_client_ip(request))
    except Subscriber.DoesNotExist:
        pass  # fail silently

    return HttpResponseRedirect(link.url)
