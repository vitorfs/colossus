from rest_framework.serializers import ModelSerializer

from colossus.apps.lists.models import MailingList


class MailingListSerializer(ModelSerializer):
    class Meta:
        model = MailingList
        fields = ('uuid', 'name', 'slug', 'subscribers_count', 'open_rate', 'click_rate', 'date_created',
                  'contact_email_address', 'website_url')
