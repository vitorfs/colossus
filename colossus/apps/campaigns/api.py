import logging
import re
from smtplib import SMTPException

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone
from django.utils.translation import gettext as _

import html2text

from colossus.apps.campaigns.constants import CampaignStatus
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.utils import get_absolute_url

logger = logging.getLogger(__name__)


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
    plain_text_message = html2text.html2text(rich_text_message, bodywidth=2000)

    # Remove track open from plain text version
    plain_text_message = re.sub(r'(!\[\]\(https?://.*/track/open/.*/\)\n\n)', '', plain_text_message, 1)

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
    except SMTPException:
        logger.exception('Could not send email "%s" due to SMTP error.' % email.uuid)
        return False


def send_campaign_email_subscriber(email, subscriber, site, connection=None):
    unsubscribe_absolute_url = get_absolute_url('subscribers:unsubscribe', kwargs={
        'mailing_list_uuid': email.campaign.mailing_list.uuid,
        'subscriber_uuid': subscriber.uuid,
        'campaign_uuid': email.campaign.uuid
    })
    subscribe_absolute_url = get_absolute_url('subscribers:subscribe', kwargs={
        'mailing_list_uuid': email.campaign.mailing_list.uuid
    })
    context = {
        'domain': site.domain,
        'uuid': subscriber.uuid,
        'name': subscriber.name,
        'sub': subscribe_absolute_url,
        'unsub': unsubscribe_absolute_url
    }
    return send_campaign_email(email, context, subscriber.get_email(), connection)


def send_campaign_email_test(email, recipient_list):
    if email.campaign.mailing_list is not None:
        unsubscribe_absolute_url = get_absolute_url('subscribers:unsubscribe_manual', kwargs={
            'mailing_list_uuid': email.campaign.mailing_list.uuid
        })
    else:
        unsubscribe_absolute_url = '#'
    context = get_test_email_context(unsub=unsubscribe_absolute_url)
    return send_campaign_email(email, context, recipient_list, is_test=True)


def send_campaign(campaign):
    campaign.status = CampaignStatus.DELIVERING
    campaign.save(update_fields=['status'])
    site = get_current_site(request=None)  # get site based on SITE_ID

    if campaign.track_clicks:
        campaign.email.enable_click_tracking()

    if campaign.track_opens:
        campaign.email.enable_open_tracking()

    with get_connection() as connection:
        for subscriber in campaign.get_recipients():
            if not subscriber.activities.filter(activity_type=ActivityTypes.SENT, email=campaign.email).exists():
                sent = send_campaign_email_subscriber(campaign.email, subscriber, site, connection)
                if sent:
                    subscriber.create_activity(ActivityTypes.SENT, email=campaign.email)
                    subscriber.update_open_and_click_rate()
                    subscriber.last_sent = timezone.now()
                    subscriber.save(update_fields=['last_sent'])

    campaign.mailing_list.update_open_and_click_rate()
    campaign.status = CampaignStatus.SENT
    campaign.save(update_fields=['status'])
