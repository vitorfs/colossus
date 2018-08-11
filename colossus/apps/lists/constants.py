from django.utils.translation import gettext_lazy as _

from colossus.apps.lists.utils import (
    convert_date, normalize_email, normalize_text,
)


class ImportStatus:
    PENDING = 1
    QUEUED = 2
    IMPORTING = 3
    COMPLETED = 4
    ERRORED = 5
    CANCELED = 6

    LABELS = {
        PENDING: _('Pending'),
        QUEUED: _('Queued'),
        IMPORTING: _('Importing'),
        COMPLETED: _('Completed'),
        ERRORED: _('Errored'),
        CANCELED: _('Canceled'),
    }

    CHOICES = tuple(LABELS.items())


class ImportStrategies:
    CREATE = 1
    UPDATE = 2
    UPDATE_OR_CREATE = 3

    LABELS = {
        CREATE: _('Create new subscribers only'),
        UPDATE: _('Update existing subscribers only'),
        UPDATE_OR_CREATE: _('Update or create subscribers'),
    }

    CHOICES = tuple(LABELS.items())


class ImportFields:
    EMAIL = 'email'
    NAME = 'name'
    OPTIN_IP_ADDRESS = 'optin_ip_address'
    OPTIN_DATE = 'optin_date'
    CONFIRM_IP_ADDRESS = 'confirm_ip_address'
    CONFIRM_DATE = 'confirm_date'

    LABELS = {
        EMAIL: _('Email address'),
        NAME: _('Name'),
        OPTIN_IP_ADDRESS: _('Opt-in IP address'),
        OPTIN_DATE: _('Opt-in date'),
        CONFIRM_IP_ADDRESS: _('Confirm IP address'),
        CONFIRM_DATE: _('Confirm date'),
    }

    PARSERS = {
        EMAIL: normalize_email,
        NAME: normalize_text,
        OPTIN_IP_ADDRESS: normalize_text,
        OPTIN_DATE: convert_date,
        CONFIRM_IP_ADDRESS: normalize_text,
        CONFIRM_DATE: convert_date,
    }

    CHOICES = tuple(LABELS.items())
