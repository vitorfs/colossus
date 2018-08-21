import factory

from colossus.apps.notifications.constants import Actions
from colossus.apps.notifications.models import Notification
from colossus.test.factories import UserFactory


class NotificationFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    action = Actions.IMPORT_COMPLETED

    class Meta:
        model = Notification
