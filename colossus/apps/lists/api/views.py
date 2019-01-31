from rest_framework.viewsets import ModelViewSet

from colossus.apps.lists.api.serializers import MailingListSerializer
from colossus.apps.lists.models import MailingList


class MailingListViewSet(ModelViewSet):
    queryset = MailingList.objects.all()
    serializer_class = MailingListSerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'
