from django.utils.translation import gettext_lazy as _

'''
Subscriber Constants
'''

PENDING = 1
SUBSCRIBED = 2
UNSUBSCRIBED = 3
CLEANED = 4

STATUS_LABELS = {
    PENDING: _('Pending'),
    SUBSCRIBED: _('Subscribed'),
    UNSUBSCRIBED: _('Unsubscribed'),
    CLEANED: _('Cleaned'),
}

STATUS_CHOICES = tuple(STATUS_LABELS.items())


'''
Form Template Constants
'''

EMAIL = 1
PAGE = 2

TEMPLATE_TYPE_LABELS = {
    EMAIL: _('Email'),
    PAGE: _('Page'),
}

TEMPLATE_TYPE_CHOICES = tuple(TEMPLATE_TYPE_LABELS.items())


SUBSCRIPTION = 1
UNSUBSCRIPTION = 2

WORKFLOW_LABELS = {
    SUBSCRIPTION: _('Subscription'),
    UNSUBSCRIPTION: _('Unsubscription'),
}

WORKFLOW_CHOICES = tuple(WORKFLOW_LABELS.items())


SUBSCRIBE_PAGE = 1
SUBSCRIBE_THANK_YOU_PAGE = 2
CONFIRM_EMAIL = 3
CONFIRM_THANK_YOU_PAGE = 4
WELCOME_EMAIL = 5
UNSUBSCRIBE_PAGE = 6
UNSUBSCRIBE_SUCCESS_PAGE = 7
GOODBYE_EMAIL = 8

KEY_LABELS = {
    SUBSCRIBE_PAGE: _('Subscribe page'),
    SUBSCRIBE_THANK_YOU_PAGE: _('Subscribe thank you page'),
    CONFIRM_EMAIL: _('Opt-in confirm email'),
    CONFIRM_THANK_YOU_PAGE: _('Opt-in confirm thank you page'),
    WELCOME_EMAIL: _('Final welcome email'),
    UNSUBSCRIBE_PAGE: _('Unsubscribe page'),
    UNSUBSCRIBE_SUCCESS_PAGE: _('Unsubscribe success page'),
    GOODBYE_EMAIL: _('Goodbye email'),
}

KEY_CHOICES = tuple(KEY_LABELS.items())