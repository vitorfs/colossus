"""
Collection of Celery tasks for the lists app.
"""
import csv
import logging
from typing import Union

from django.db import transaction
from django.utils import timezone

from celery import shared_task

from colossus.apps.lists.constants import (
    ImportFields, ImportStatus, ImportStrategies,
)
from colossus.apps.notifications.constants import Actions
from colossus.apps.notifications.models import Notification
from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Subscriber

from .models import SubscriberImport

logger = logging.getLogger(__name__)


@shared_task
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
            notification_action: int
            output_message = ''

            try:
                columns_mapping = subscriber_import.get_columns_mapping()
                subscriber_created = 0
                subscriber_updated = 0
                subscriber_skipped = 0

                with open(subscriber_import.file.path, 'r') as csvfile:
                    dialect = csv.Sniffer().sniff(csvfile.read(1024))
                    csvfile.seek(0)
                    reader = csv.reader(csvfile, dialect)

                    # FIXME: determine if needs to skip the first line or not
                    if True:
                        next(reader)

                    with transaction.atomic():
                        for row in reader:
                            subscriber = None

                            defaults = {'status': subscriber_import.subscriber_status}
                            for column_index, subscriber_field_name in columns_mapping.items():
                                field_parser = ImportFields.PARSERS[subscriber_field_name]
                                cleaned_field_data = field_parser(row[column_index])
                                defaults[subscriber_field_name] = cleaned_field_data

                            subscriber_queryset = Subscriber.objects.filter(
                                email__iexact=defaults['email'],
                                mailing_list_id=subscriber_import.mailing_list_id,
                            )
                            subscriber_exists = subscriber_queryset.exists()

                            if subscriber_import.strategy == ImportStrategies.CREATE:
                                if not subscriber_exists:
                                    subscriber = Subscriber.objects.create(
                                        mailing_list_id=subscriber_import.mailing_list_id,
                                        **defaults
                                    )
                                    subscriber_created += 1
                                else:
                                    subscriber_skipped += 1

                            elif subscriber_import.strategy == ImportStrategies.UPDATE:
                                if subscriber_exists:
                                    subscriber_queryset.update(update_date=timezone.now(), **defaults)
                                    subscriber = subscriber_queryset.get()
                                else:
                                    subscriber_skipped += 1

                            elif subscriber_import.strategy == ImportStrategies.UPDATE_OR_CREATE:
                                subscriber, created = Subscriber.objects.update_or_create(
                                    email__iexact=defaults['email'],
                                    mailing_list_id=subscriber_import.mailing_list_id,
                                    defaults=defaults
                                )
                                if created:
                                    subscriber_created += 1
                                else:
                                    subscriber.update_date = timezone.now()
                                    subscriber.save(update_fields=['update_date'])
                                    subscriber_updated += 1

                            if subscriber is not None:
                                subscriber.create_activity(ActivityTypes.IMPORTED)

                subscriber_import.mailing_list.update_subscribers_count()
                import_status = ImportStatus.COMPLETED
                notification_action = Actions.IMPORT_COMPLETED
                output_message = 'The subscriber import "%s" completed with success. %s created, %s updated, ' \
                                 '%s skipped.' % (subscriber_import_id, subscriber_created, subscriber_updated,
                                                  subscriber_skipped)
            except Exception:
                import_status = ImportStatus.ERRORED
                notification_action = Actions.IMPORT_ERRORED
                output_message = 'An error occurred while importing the file "%s".' % subscriber_import_id
                logger.exception(output_message)
            finally:
                subscriber_import.status = import_status
                subscriber_import.save(update_fields=['status'])
                Notification.objects.create(user=subscriber_import.user, action=notification_action,
                                            text=output_message)
                return output_message
        else:
            return 'The subscriber import file "%s" was not queued to be imported.' % subscriber_import_id
    except SubscriberImport.DoesNotExist:
        return 'Subscriber import file "%s" does not exist.' % subscriber_import_id
