import base64
import logging
from uuid import UUID

from django.contrib import messages
from django.http import (
    Http404, HttpRequest, HttpResponse, HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (
    require_GET, require_http_methods, require_POST,
)

import requests
from ratelimit.decorators import ratelimit

from colossus.apps.campaigns.models import Campaign, Email, Link
from colossus.apps.core.models import Token
from colossus.apps.lists.models import MailingList
from colossus.utils import get_client_ip, ip_address_key

from .constants import Status
from .forms import SubscribeForm, UnsubscribeForm
from .models import Subscriber

logger = logging.getLogger(__name__)


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
@require_http_methods(['GET', 'HEAD', 'POST'])
@ratelimit(key=ip_address_key, rate='10/5m', method='POST')
def subscribe(request, mailing_list_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    is_limited = getattr(request, 'limited', False)

    if is_limited:
        logger.warning('IP address "%s" exceeded rate limit 10/5m for subscribe view.' % get_client_ip(request))
        messages.warning(request, _('Too many requests. Your IP address is blocked for 5 minutes.'))

    if request.method == 'POST' and not is_limited:
        valid_recaptcha_or_skip_recaptcha_validation = True
        if mailing_list.enable_recaptcha:
            # reCAPTCHA validation
            recaptcha_response = request.POST.get('g-recaptcha-response')
            data = {
                'secret': mailing_list.recaptcha_secret_key,
                'response': recaptcha_response
            }
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            recaptcha_result = r.json()
            valid_recaptcha_or_skip_recaptcha_validation = recaptcha_result['success']

        form = SubscribeForm(mailing_list=mailing_list, data=request.POST)

        if valid_recaptcha_or_skip_recaptcha_validation:
            if form.is_valid():
                form.subscribe(request)
                return redirect('subscribers:confirm_subscription', mailing_list_uuid=mailing_list_uuid)
        else:
            messages.info(request, _('Please check the reCAPTCHA and submit the form again.'))
    else:
        form = SubscribeForm(mailing_list=mailing_list)

    content = mailing_list.get_subscribe_form_template().content_html

    return render(request, 'subscribers/subscribe_form.html', {
        'mailing_list': mailing_list,
        'form': form,
        'content': content
    })


@require_GET
def confirm_subscription(request, mailing_list_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    form_template = mailing_list.get_subscribe_thank_you_page_template()

    if form_template.redirect_url:
        return redirect(form_template.redirect_url)

    return render(request, 'subscribers/subscribe_thank_you.html', {
        'mailing_list': mailing_list,
        'content': form_template.content_html
    })


@require_GET
def confirm_double_optin_token(request, mailing_list_uuid, token):
    try:
        mailing_list = MailingList.objects.get(uuid=mailing_list_uuid)
    except MailingList.DoesNotExist:
        return HttpResponseBadRequest('The requested list does not exist.', content_type='text/plain')

    try:
        confirm_token = Token.objects.get(text=token, description='confirm_subscription')
    except Token.DoesNotExist:
        return HttpResponseBadRequest('Invalid token.', content_type='text/plain')

    subscriber = confirm_token.content_object
    subscriber.confirm_subscription(request)

    form_template = mailing_list.get_confirm_thank_you_page_template()

    if form_template.redirect_url:
        return redirect(form_template.redirect_url)

    return render(request, 'subscribers/confirm_thank_you.html', {
        'mailing_list': mailing_list,
        'content': form_template.content_html
    })


@require_http_methods(['GET', 'POST'])
@ratelimit(key=ip_address_key, rate='5/5m', method='POST')
def unsubscribe_manual(request, mailing_list_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    is_limited = getattr(request, 'limited', False)

    if is_limited:
        messages.warning(request, _('Too many requests. Your IP address is blocked for 5 minutes.'))
        logger.warning('IP address "%s" exceeded rate limit 5/5m for unsubscribe view.' % get_client_ip(request))

    if request.method == 'POST' and not is_limited:
        form = UnsubscribeForm(mailing_list=mailing_list, data=request.POST)
        if form.is_valid():
            form.unsubscribe(request)
            # If the unsubscribe was done manually, force send good bye email
            goodbye_email = mailing_list.get_goodbye_email_template()
            goodbye_email.send(form.cleaned_data.get('email'))
            return redirect('subscribers:goodbye', mailing_list_uuid=mailing_list_uuid)
    else:
        form = UnsubscribeForm(mailing_list=mailing_list)

    content = mailing_list.get_unsubscribe_form_template().content_html

    return render(request, 'subscribers/unsubscribe_form.html', {
        'form': form,
        'mailing_list': mailing_list,
        'content': content
    })


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

    if subscriber.status != Status.SUBSCRIBED:
        return HttpResponse('This email address was not found in our list.', content_type='text/plain')

    subscriber.unsubscribe(request, campaign)
    return redirect('subscribers:goodbye', mailing_list_uuid=mailing_list_uuid)


def goodbye(request, mailing_list_uuid):
    mailing_list = get_object_or_404(MailingList, uuid=mailing_list_uuid)
    form_template = mailing_list.get_unsubscribe_success_page_template()

    if form_template.redirect_url:
        return redirect(form_template.redirect_url)

    content = form_template.content_html
    return render(request, 'subscribers/unsubscribe_success.html', {
        'mailing_list': mailing_list,
        'content': content
    })


@require_GET
@ratelimit(key=ip_address_key, rate='100/h', method='GET', block=True)
def track_open(request, email_uuid, subscriber_uuid):
    try:
        email = Email.objects.get(uuid=email_uuid)
        subscriber = Subscriber.objects.get(uuid=subscriber_uuid)
        subscriber.open(email)
    except Exception:
        logger.exception('An error occurred while subscriber "%s" was trying to '
                         'open the email "%s".' % (subscriber_uuid, email_uuid))

    pixel = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')  # noqa
    return HttpResponse(pixel, content_type='image/png')


@require_GET
@ratelimit(key=ip_address_key, rate='100/h', method='GET', block=True)
def track_click(request: HttpRequest,
                link_uuid: UUID,
                subscriber_uuid: UUID) -> HttpResponseRedirect:
    """
    Track subscriber's click on links on email from campaigns.
    Triggers celery tasks to update total and unique click count.
    Affects subscriber click rate, mailing list click rate and campaign click
    rate.

    This view can only be accessed via GET request and has a limit of 100
    requests per hour per IP address.

    :param request: A Django HTTP Request object
    :param link_uuid: A Link instance uuid field
    :param subscriber_uuid: A Subscriber instance uuid field
    :return: Redirection to the link's target URL
    """
    link: Link
    try:
        link = Link.objects.filter(uuid=link_uuid).select_related('email').get()
        subscriber = Subscriber.objects.get(uuid=subscriber_uuid)
        ip_address = get_client_ip(request)
        subscriber.click(link, ip_address)
    except Link.DoesNotExist:
        raise Http404
    except Subscriber.DoesNotExist:
        # fail silently
        logger.info('track_click call to non-existing Subscriber instance'
                    'uuid = "%s"' % str(subscriber_uuid))
    except Exception:
        logger.exception('Failed to track click on link "%s" from subscriber '
                         '"%s"' % (str(link_uuid), str(subscriber_uuid)))
    return HttpResponseRedirect(link.url)
