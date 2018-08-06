import csv
from typing import Union

from django.db import transaction
from django.utils import timezone

import pytz
from celery import shared_task

from colossus.apps.lists.constants import ImportStatus
from colossus.apps.notifications.models import Notification
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Subscriber

from .models import SubscriberImport


def convert_date(text):
    date = timezone.datetime.strptime(text.strip(), '%Y-%m-%d %H:%M:%S')
    return pytz.utc.localize(date)


IMPORT_PARSERS = (
    lambda text: ('email', Subscriber.objects.normalize_email(text)),  # 0
    lambda text: ('name', text.strip()),  # 1
    lambda text: ('optin_ip_address', text.strip()),  # 2
    lambda text: ('optin_date', convert_date(text)),  # 3
    lambda text: ('confirm_ip_address', text.strip()),  # 4
    lambda text: ('confirm_date', convert_date(text)),  # 5
)


@shared_task
@transaction.atomic
def import_subscribers(subscriber_import_id: Union[str, int]) -> str:
    """
    Parse the data from a SubscriberImport CSV file and import to the database.

    :param subscriber_import_id: SubscriberImport instance ID
    :return: Message with the status of the import process
    """
    try:
        subscriber_import = SubscriberImport.objects.get(pk=subscriber_import_id)
        if subscriber_import.status == ImportStatus.QUEUED:

            # Start import process
            subscriber_import.status = ImportStatus.IMPORTING
            subscriber_import.save(update_fields=['status'])

            import_status: int
            output_message = ''

            try:
                max_size = len(IMPORT_PARSERS)
                imported = 0
                updated = 0
                with open(subscriber_import.file.path, 'r') as csvfile:
                    dialect = csv.Sniffer().sniff(csvfile.read(1024))
                    csvfile.seek(0)
                    reader = csv.reader(csvfile, dialect)
                    for row in reader:
                        defaults = {'status': subscriber_import.status}
                        for index, column in enumerate(row):
                            if index < max_size:
                                parser = IMPORT_PARSERS[index]
                                field, data = parser(column)
                                defaults[field] = data
                            else:
                                # Exit the for loop to avoid tuple index out of range
                                break
                        subscriber, created = Subscriber.objects.update_or_create(
                            email__iexact=defaults['email'],
                            mailing_list_id=subscriber_import.mailing_list_id,
                            defaults=defaults
                        )
                        if created:
                            subscriber.create_activity(ActivityTypes.IMPORTED)
                            imported += 1
                        else:
                            subscriber.update_date = timezone.now()
                            subscriber.save(update_fields=['update_date'])
                            updated += 1
                subscriber_import.mailing_list.update_subscribers_count()
                import_status = ImportStatus.COMPLETED
                output_message = 'The subscriber import "%s" completed with success.' % subscriber_import_id
            except Exception as e:
                import_status = ImportStatus.ERRORED
                output_message = 'An error occurred while importing the file "%s". ' \
                                 'Error message: "%s"' % (subscriber_import_id, str(e))
            finally:
                subscriber_import.status = import_status
                subscriber_import.save(update_fields=['status'])
                Notification.objects.create(user=subscriber_import.user, text=output_message)
                return output_message
        else:
            return 'The subscriber import file "%s" was not queued to be imported.' % subscriber_import_id
    except SubscriberImport.DoesNotExist:
        return 'Subscriber import file "%s" does not exist.' % subscriber_import_id
