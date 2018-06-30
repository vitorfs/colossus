from smtplib import SMTPException

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives, get_connection
from django.urls import reverse
from django.utils.translation import gettext as _

import html2text

from colossus.apps.subscribers.constants import ActivityTypes


def get_test_email_context(**kwargs):
    if 'unsub' not in kwargs:
        kwargs['unsub'] = '#'
    if 'name' not in kwargs:
        kwargs['name'] = '<< Test Name >>'
    if 'uuid' not in kwargs:
        kwargs['uuid'] = '[SUBSCRIBER_UUID]'
    return kwargs


def send_campaign_email(email, context, to, connection=None, is_test=False):
    if isinstance(to, str):
        to = [to, ]

    subject = email.subject
    if is_test:
        subject = '[%s] %s' % (_('Test'), subject)

    rich_text_message = email.render(context)
    plain_text_message = html2text.html2text(rich_text_message)

    headers = {
        'List-ID': '%s <%s.list-id.%s>' % (
            email.campaign.mailing_list.name,
            email.campaign.mailing_list.uuid,
            context['domain']
        ),
        'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
        'List-Unsubscribe': '<mailto:%s>, <%s>' % ('unsubscribe@mg.simpleisbetterthancomplex.com', context['unsub'])
    }

    message = EmailMultiAlternatives(
        subject=subject,
        body=plain_text_message,
        from_email=email.get_from(),
        to=to,
        connection=connection,
        headers=headers
    )
    message.attach_alternative(rich_text_message, 'text/html')

    try:
        message.send(fail_silently=False)
        return True
    except SMTPException as err:
        # TODO: log error message
        return False


def send_campaign_email_subscriber(email, subscriber, site, connection=None):
    path = reverse('subscribers:unsubscribe', kwargs={
        'mailing_list_uuid': email.campaign.mailing_list.uuid,
        'subscriber_uuid': subscriber.uuid,
        'campaign_uuid': email.campaign.uuid
    })
    # TODO: remove hardcoded http
    protocol = 'http'
    unsubscribe_absolute_url = '%s://%s%s' % (protocol, site.domain, path)
    context = {
        'domain': site.domain,
        'uuid': subscriber.uuid,
        'name': subscriber.name,
        'unsub': unsubscribe_absolute_url
    }
    return send_campaign_email(email, context, subscriber.get_email(), connection)


def send_campaign_email_test(email, recipient_list):
    context = get_test_email_context()
    return send_campaign_email(email, context, recipient_list, is_test=True)


def send_campaign(campaign):
    site = get_current_site(request=None)  # get site based on SITE_ID
    campaign.email.enable_click_tracking()
    campaign.email.enable_open_tracking()
    with get_connection() as connection:
        for subscriber in campaign.mailing_list.get_active_subscribers():
            sent = send_campaign_email_subscriber(campaign.email, subscriber, site, connection)
            if sent:
                subscriber.create_activity(ActivityTypes.SENT, email=campaign.email)
