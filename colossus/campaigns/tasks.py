from celery import shared_task

from .models import Campaign


@shared_task
def send_campaign(campaign_id):
    pass
