from django.apps import apps
from django.core.mail import mail_managers

from celery import shared_task

from .api import send_campaign


@shared_task
def send_campaign_task(campaign_id):
    Campaign = apps.get_model('campaigns', 'Campaign')
    campaign = Campaign.objects.get(pk=campaign_id)
    send_campaign(campaign)
    mail_managers('Mailing campaign has been sent',
                  'Your campaign "%s" is on its way to your subscribers!' % campaign.email.subject)
