import base64

from django.contrib import messages
from django.http import (
    Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (
    require_GET, require_http_methods, require_POST,
)
from django.views.generic import View

from ratelimit.decorators import ratelimit

from colossus.apps.campaigns.models import Campaign, Email, Link
from colossus.apps.core.models import Token
from colossus.apps.lists.models import MailingList
from colossus.utils import get_client_ip, ip_address_key

from .constants import Status
from .forms import SubscribeForm, UnsubscribeForm
from .models import Subscriber


class IndexView(View):
    def get(self, request):
        return HttpResponse('Hi there! :)')


@csrf_exempt
@require_POST
def manage(request):
    for k, v in request.POST.items():
        print('%s ==> %s' % (k, v))

    subject = request.POST.get('subject', '')
    subject = subject.strip().lower()
    if subject == 'unsubscribe':
        return HttpResponse('unsub action')
    elif subject == 'subscribe':
        return HttpResponse('sub action')
    return HttpResponse('no action tiggered.')


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@ratelimit(key=ip_address_key, rate='10/5m', method='POST')
def subscribe(request, mailing_list_uuid):
    if 'application/json' in request.META.get('HTTP_ACCEPT'):
        pass
    else:
        pass

    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    is_limited = getattr(request, 'limited', False)

    if is_limited:
        messages.warning(request, _('Too many requests. Your IP address is blocked for 5 minutes.'))

    if request.method == 'POST' and not is_limited:
        form = SubscribeForm(mailing_list=mailing_list, data=request.POST)
        if form.is_valid():
            form.subscribe(request)
            return redirect('subscribers:confirm_subscription', mailing_list_uuid=mailing_list_uuid)
    else:
        form = SubscribeForm(mailing_list=mailing_list)
    return render(request, 'subscribers/subscribe_form.html', {
        'mailing_list': mailing_list,
        'form': form
    })


@require_GET
def confirm_subscription(request, mailing_list_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    return render(request, 'subscribers/subscribe_thank_you.html', {'mailing_list': mailing_list})


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

    return render(request, 'subscribers/confirm_thank_you.html', {'mailing_list': mailing_list})


@require_http_methods(['GET', 'POST'])
@ratelimit(key=ip_address_key, rate='5/5m', method='POST')
def unsubscribe_manual(request, mailing_list_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    is_limited = getattr(request, 'limited', False)

    if is_limited:
        messages.warning(request, _('Too many requests. Your IP address is blocked for 5 minutes.'))

    if request.method == 'POST' and not is_limited:
        form = UnsubscribeForm(mailing_list=mailing_list, data=request.POST)
        if form.is_valid():
            form.unsubscribe(request)
            return redirect('subscribers:goodbye', mailing_list_uuid=mailing_list_uuid)
    else:
        form = UnsubscribeForm(mailing_list=mailing_list)
    return render(request, 'subscribers/unsubscribe_form.html', {'form': form, 'mailing_list': mailing_list})


@require_GET
@ratelimit(key=ip_address_key, rate='5/5m', method='GET', block=True)
def unsubscribe(request, mailing_list_uuid, subscriber_uuid, campaign_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)

    try:
        subscriber = Subscriber.objects.get(uuid=subscriber_uuid, mailing_list=mailing_list)
    except Subscriber.DoesNotExist:
        return redirect('subscribers:unsubscribe_manual', mailing_list_uuid=mailing_list_uuid)

    try:
        campaign = Campaign.objects.get(uuid=campaign_uuid)
    except Campaign.DoesNotExist:
        campaign = None

    if subscriber.status == Status.SUBSCRIBED:
        subscriber.unsubscribe(request, campaign)
        return redirect('subscribers:goodbye', mailing_list_uuid=mailing_list_uuid)
    else:
        return HttpResponse('This email address was not found in our list.', content_type='text/plain')


@require_GET
def goodbye(request, mailing_list_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    return render(request, 'subscribers/unsubscribe_success.html', {'mailing_list': mailing_list})


@require_GET
@ratelimit(key=ip_address_key, rate='100/h', method='GET', block=True)
def track_open(request, email_uuid, subscriber_uuid):
    try:
        email = Email.objects.get(uuid=email_uuid)
        subscriber = Subscriber.objects.get(uuid=subscriber_uuid)
        ip_address = get_client_ip(request)
        subscriber.open(email, ip_address)
    except Exception:
        pass  # fail silently

    pixel = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')  # noqa
    return HttpResponse(pixel, content_type='image/png')


@require_GET
@ratelimit(key=ip_address_key, rate='100/h', method='GET', block=True)
def track_click(request, link_uuid, subscriber_uuid):
    link = None
    try:
        link = Link.objects.filter(uuid=link_uuid).select_related('email').get()
        subscriber = Subscriber.objects.get(uuid=subscriber_uuid)
        ip_address = get_client_ip(request)
        subscriber.click(link, ip_address)
    except Link.DoesNotExist:
        raise Http404
    except Subscriber.DoesNotExist:
        pass  # fail silently
    return HttpResponseRedirect(link.url)
