"""
Collection of Celery tasks for the lists app.
"""
import csv
import json
import logging
from typing import Dict, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from celery import shared_task

from colossus.apps.lists.constants import (
    ImportFields, ImportStatus, ImportStrategies,
)
from colossus.apps.notifications.constants import Actions
from colossus.apps.notifications.models import Notification
from colossus.apps.subscribers.constants import ActivityTypes, Status
from colossus.apps.subscribers.models import Domain, Subscriber

from .models import MailingList, SubscriberImport

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def clean_list_task(mailing_list_id):
    try:
        mailing_list = MailingList.objects.get(pk=mailing_list_id)
        data = {
            'mailing_list_id': mailing_list_id,
            'cleaned': 0
        }
        # TODO: Find a better way to determine what email backend is in use
        if settings.MAILGUN_API_KEY:
            from colossus.apps.core.mailgun import Mailgun
            client = Mailgun()
            # TODO: Handle pagination from Mailgun Bounces API
            bounces = client.bounces()
            if 'items' in bounces:
                for bounce in bounces['items']:
                    email_address = bounce['address']
                    if mailing_list.get_active_subscribers().filter(email=email_address).exists():
                        subscriber = mailing_list.subscribers.get(email=email_address)
                        subscriber.status = Status.CLEANED
                        subscriber.update_date = timezone.now()
                        with transaction.atomic():
                            subscriber.save(update_fields=['status', 'update_date'])
                            subscriber.create_activity(ActivityTypes.CLEANED)
                        data['cleaned'] += 1

        if data['cleaned'] > 0:
            text = json.dumps(data)
            # FIXME: Once there's a better user management associated to a given list, update the code below
            for user in User.objects.filter(is_superuser=True, is_active=True):
                Notification.objects.create(user=user, action=Actions.LIST_CLEANED, text=text)

        return 'Cleaned %(cleaned)s emails from mailing list %(mailing_list_id)s' % data

    except MailingList.DoesNotExist:
        return 'Mailing list with id "%s" does not exist.' % mailing_list_id


@shared_task
def clean_lists_hard_bounces_task():
    mailing_lists_ids = MailingList.objects.values_list('id', flat=True)
    for id in mailing_lists_ids:
        clean_list_task.delay(id)


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
            cached_domains: Dict[str, Domain] = dict()

            try:
                columns_mapping = subscriber_import.get_columns_mapping()
                subscriber_created = 0
                subscriber_updated = 0
                subscriber_skipped = 0

                with open(subscriber_import.file.path, 'r') as csvfile:
                    reader = csv.reader(csvfile)

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

                            email_name, domain_part = defaults['email'].rsplit('@', 1)
                            domain_name = '@' + domain_part

                            try:
                                email_domain = cached_domains[domain_name]
                            except KeyError:
                                email_domain, created = Domain.objects.get_or_create(name=domain_name)
                                cached_domains[domain_name] = email_domain

                            defaults['domain'] = email_domain

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
