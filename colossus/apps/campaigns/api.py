from smtplib import SMTPException

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives, get_connection
from django.urls import reverse
from django.utils.translation import gettext as _

import html2text

from colossus.apps.subscribers.constants import ActivityTypes


def get_test_email_context(**kwargs):
    if 'sub' not in kwargs:
        kwargs['sub'] = '#'
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

    headers = dict()
    if not is_test:
        headers['List-ID'] = '%s <%s.list-id.%s>' % (
            email.campaign.mailing_list.name,
            email.campaign.mailing_list.uuid,
            context['domain']
        ),
        headers['List-Post'] = 'NO',
        headers['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

        list_subscribe_header = ['<%s>' % context['sub']]
        list_unsubscribe_header = ['<%s>' % context['unsub']]
        if email.campaign.mailing_list.list_manager:
            list_subscribe_header.append('<mailto:%s?subject=subscribe>' % email.campaign.mailing_list.list_manager)
            list_unsubscribe_header.append(
                '<mailto:%s?subject=unsubscribe>' % email.campaign.mailing_list.list_manager
            )

        headers['List-Subscribe'] = ', '.join(list_subscribe_header)
        headers['List-Unsubscribe'] = ', '.join(list_unsubscribe_header)

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
    # TODO: remove hardcoded http
    protocol = 'http'

    unsub_path = reverse('subscribers:unsubscribe', kwargs={
        'mailing_list_uuid': email.campaign.mailing_list.uuid,
        'subscriber_uuid': subscriber.uuid,
        'campaign_uuid': email.campaign.uuid
    })
    unsubscribe_absolute_url = '%s://%s%s' % (protocol, site.domain, unsub_path)

    sub_path = reverse('subscribers:subscribe', kwargs={
        'mailing_list_uuid': email.campaign.mailing_list.uuid
    })
    subscribe_absolute_url = '%s://%s%s' % (protocol, site.domain, sub_path)

    context = {
        'domain': site.domain,
        'uuid': subscriber.uuid,
        'name': subscriber.name,
        'sub': subscribe_absolute_url,
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
                subscriber.update_open_and_click_rate()
        campaign.mailing_list.update_open_and_click_rate()
