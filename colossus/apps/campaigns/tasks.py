import logging

from django.apps import apps
from django.core.mail import mail_managers
from django.utils import timezone

from celery import shared_task

from .api import send_campaign
from .constants import CampaignStatus

logger = logging.getLogger(__name__)


@shared_task
def send_campaign_task(campaign_id):
    Campaign = apps.get_model('campaigns', 'Campaign')
    try:
        campaign = Campaign.objects.get(pk=campaign_id)
        if campaign.status == CampaignStatus.QUEUED:
            send_campaign(campaign)
            mail_managers('Mailing campaign has been sent',
                          'Your campaign "%s" is on its way to your subscribers!' % campaign.email.subject)
        else:
            logger.warning('Campaign "%s" was placed in a queue with status "%s".' % (campaign_id,
                                                                                      campaign.get_status_display()))
    except Campaign.DoesNotExist:
        logger.exception('Campaign "%s" was placed in a queue but it does not exist.' % campaign_id)


@shared_task
def send_scheduled_campaigns_task():
    Campaign = apps.get_model('campaigns', 'Campaign')
    campaigns = Campaign.objects.filter(status=CampaignStatus.SCHEDULED, send_date__gte=timezone.now())
    if campaigns.exists():
        for campaign in campaigns:
            campaign.send()


@shared_task
def update_rates_after_campaign_deletion(mailing_list_id):
    MailingList = apps.get_model('lists', 'MailingList')
    mailing_list = MailingList.objects.only('pk').get(pk=mailing_list_id)
    for subscriber in mailing_list.subscribers.only('pk'):
        subscriber.update_open_and_click_rate()
    mailing_list.update_open_and_click_rate()
