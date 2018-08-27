import logging

from django.apps import apps
from django.db import transaction
from django.db.models import Q

from celery import shared_task

from colossus.apps.lists.models import MailingList
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.utils import get_location

logger = logging.getLogger(__name__)


@shared_task
def update_open_rate(subscriber_id, email_id):
    Subscriber = apps.get_model('subscribers', 'Subscriber')
    Email = apps.get_model('campaigns', 'Email')
    try:
        subscriber = Subscriber.objects.filter(pk=subscriber_id).select_related('mailing_list').get()
        email = Email.objects.filter(pk=email_id).select_related('campaign').get()
        with transaction.atomic():
            subscriber.update_open_rate()
            subscriber.mailing_list.update_open_rate()
            email.update_opens_count()
            email.campaign.update_opens_count_and_rate()
    except (Subscriber.DoesNotExist, Email.DoesNotExist):
        logger.exception('An error occurred while trying to update open rates with '
                         'subscriber_id = "%s" and email_id = "%s"' % (subscriber_id, email_id))


@shared_task
def update_click_rate(subscriber_id, link_id):
    Subscriber = apps.get_model('subscribers', 'Subscriber')
    Link = apps.get_model('campaigns', 'Link')
    try:
        subscriber = Subscriber.objects.filter(pk=subscriber_id).select_related('mailing_list').get()
        link = Link.objects.filter(pk=link_id).select_related('email__campaign').get()
        with transaction.atomic():
            if not subscriber.activities.filter(activity_type=ActivityTypes.OPENED, email=link.email).exists():
                # For the user to click on the email, he/she must have opened it. In some cases the open pixel won't
                # be triggered. So in those cases, force an open record
                activity = subscriber.activities.filter(activity_type=ActivityTypes.CLICKED, link=link).first()
                ip_address = activity.ip_address if activity is not None else None
                subscriber.open(link.email, ip_address)
            subscriber.update_click_rate()
            subscriber.mailing_list.update_click_rate()
            link.update_clicks_count()
            link.email.update_clicks_count()
            link.email.campaign.update_clicks_count_and_rate()
    except (Subscriber.DoesNotExist, Link.DoesNotExist):
        logger.exception('An error occurred while trying to update open rates with '
                         'subscriber_id = "%s" and link_id = "%s"' % (subscriber_id, link_id))


@shared_task
def update_rates_after_subscriber_deletion(mailing_list_id, email_ids, link_ids):
    mailing_list = MailingList.objects.only('pk').get(pk=mailing_list_id)
    mailing_list.update_open_and_click_rate()

    Email = apps.get_model('campaigns', 'Email')
    emails = Email.objects.filter(pk__in=email_ids).select_related('campaign').only('pk', 'campaign__id')
    for email in emails:
        email.update_clicks_count()
        email.update_opens_count()
        email.campaign.update_opens_count_and_rate()

    Link = apps.get_model('campaigns', 'Link')
    links = Link.objects.filter(pk__in=link_ids).only('pk')
    for link in links:
        link.update_clicks_count()


@shared_task
def update_subscriber_location(ip_address, subscriber_id):
    location = get_location(ip_address)
    if location is not None:
        Subscriber = apps.get_model('subscribers', 'Subscriber')

        subscriber = Subscriber.objects.get(pk=subscriber_id)

        if subscriber.last_seen_ip_address == ip_address and subscriber.location_id != location.pk:
            subscriber.location = location
            subscriber.save(update_fields=['location'])

        subscriber.activities \
            .filter(ip_address=ip_address) \
            .filter(Q(location=None) | Q(activity_type=ActivityTypes.OPENED)) \
            .update(location=location)
