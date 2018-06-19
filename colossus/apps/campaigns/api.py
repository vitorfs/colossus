from smtplib import SMTPException

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives, get_connection
from django.urls import reverse
from django.utils.translation import gettext as _

from colossus.apps.subscribers.constants import ActivityTypes


def get_test_email_context():
    context = {
        'uuid': '[SUBSCRIBER_UUID]',
        'name': '<< Test Name >>',
        'unsub': '#'
    }
    return context


def send_campaign_email(email, context, to, connection=None, is_test=False):
    if isinstance(to, str):
        to = [to, ]

    subject = email.subject
    if is_test:
        subject = '[%s] %s' % (_('Test'), subject)

    plain_text_message = email.render_text(context)
    rich_text_message = email.render_html(context)

    headers = {
        'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
        'List-Unsubscribe': '<%s>' % context['unsub']
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
    protocol = 'http'
    unsubscribe_absolute_url = '%s://%s%s' % (protocol, site.domain, path)
    context = {
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
    campaign.email.enable_tracking()
    with get_connection() as connection:
        for subscriber in campaign.mailing_list.get_active_subscribers():
            sent = send_campaign_email_subscriber(campaign.email, subscriber, site, connection)
            if sent:
                subscriber.create_activity(ActivityTypes.SENT, email=campaign.email)
