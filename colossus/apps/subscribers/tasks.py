from celery import shared_task
from django.apps import apps

from colossus.apps.campaigns.models import Campaign
from colossus.apps.subscribers.constants import ActivityTypes


@shared_task
def update_open_rate(subscriber_id, email_id):
    pass
    # update_fields = {'total_opens_count': F('total_opens_count') + 1}
    # if not self.activities.filter(activity_type=ActivityTypes.OPENED, email=email).exists():
    #     # First time opening the email, count as unique open
    #     update_fields['unique_opens_count'] = F('unique_opens_count') + 1
    # Email.objects.filter(pk=email.pk).update(**update_fields)
    # Campaign.objects.filter(pk=email.campaign_id).update(**update_fields)
    # self.create_activity(ActivityTypes.OPENED, email=email, ip_address=get_client_ip(request))
    # self.update_open_rate()
    # self.mailing_list.update_open_rate()


@shared_task
def update_click_rate(subscriber_id, link_id):
    Subscriber = apps.get_model('subscribers', 'Subscriber')
    Link = apps.get_model('campaigns', 'Link')
    try:
        subscriber = Subscriber.objects.filter(pk=subscriber_id).select_related('mailing_list').get()
        link = Link.objects.filter(pk=link_id).select_related('email__campaign').get()
        if not subscriber.activities.filter(activity_type=ActivityTypes.OPENED, email=link.email).exists():
            # For the user to click on the email, he/she must have opened it. In some cases the open pixel won't
            # be triggered. So in those cases, force an open record
            subscriber.open(link.email)  # TODO: pass the same ip address as the click action
        subscriber.update_click_rate()
        subscriber.mailing_list.update_click_rate()
        link.update_clicks_count()
        link.email.update_clicks_count()
        link.email.campaign.update_clicks_count_and_rate()

    except (Subscriber.DoesNotExist, Link.DoesNotExist):
        pass

    # TODO: Work the click logic to do a proper counting of the email opens
    # update_fields = {'total_clicks_count': F('total_clicks_count') + 1}
    # if not self.activities.filter(activity_type=ActivityTypes.CLICKED, link=link).exists():
    #     # First time clicking on a link, count as unique click
    #     update_fields['unique_clicks_count'] = F('unique_clicks_count') + 1
    #     if not self.activities.filter(activity_type=ActivityTypes.OPENED, email=link.email).exists():
    #         # For the user to click on the email, he/she must have opened it. In some cases the open pixel won't
    #         # be triggered. So in those cases, force an open record
    #         self.open(request, link.email)
    # Link.objects.filter(pk=link.pk).update(**update_fields)
    # Campaign.objects.filter(pk=link.email.campaign_id).update(**update_fields)
    # self.create_activity(ActivityTypes.CLICKED, link=link, email=link.email, ip_address=get_client_ip(request))
    # self.update_click_rate()
    # self.mailing_list.update_click_rate()
